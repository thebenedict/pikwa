#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from rapidsms.contrib.handlers.handlers.pattern import PatternHandler
from retail.models import Stock, StockTransaction

class AcceptHandler(PatternHandler):

    """
    Accept an incoming transfer of stock. This corresponds to a physical
    transfer of product from one person to another.

    """

    pattern = r'(?i)yes|y'

    def handle(self):
        target = self.msg.connection.contact
        trans = list(StockTransaction.objects.filter(recipient=target, status=2))
        if trans is None:
            self.respond("There were no transactions pending." % recip)
            return True
       
        for t in trans:
            stk_list = t.to_transfer.all()
            for stk in stk_list:
                existing = Stock.get_existing(target.alias, stk.product.code)
                if existing:
                    existing.stock_amount += stk.stock_amount
                    existing.save()
                    stk.delete()
                else:
                    stk.seller = target
                    stk.save()

            t.status = 1
            t.date_resolved = datetime.now()
            t.save()

            self.respond("Transfer from %s done, current stock %s." % (t.initiator.alias, self.get_current_stock(target)))

            #now confirm with sender
            t.initiator.message("Transfer confirmed by %s. Current stock %s." % (target.alias, self.get_current_stock(t.initiator)))

    def get_current_stock(self, usr):
        cur_stock = Stock.objects.filter(seller=usr)
        response = ""
        if cur_stock is not None:
            for s in list(cur_stock):
                response += "%s %s, " % (s.stock_amount, s.product.display_name)
            return response.rstrip()[:-1]
        else:
            return "not found."
