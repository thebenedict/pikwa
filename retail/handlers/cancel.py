#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from datetime import datetime
from decimal import *
from retail.models import Product, Stock, Sale

class CancelHandler(KeywordHandler):
    """
    Logic for cancelling a sale.

    """

    keyword = "cancel"

    def help(self):
        self.respond("To cancel a sale use cancel serial#")

    def handle(self, sn):
        serial = sn.upper()
        to_cancel = Sale.by_serial(serial)
        if to_cancel is None:
            self.respond("ERROR: No sale record found for %s" % serial)
            return True
        #verify that the person requesting the cancellation is the seller
        if to_cancel.seller != self.msg.connection.contact:
            self.respond("ERROR: You are not allowed to cancel this sale")
            return True
        #save values for later, then delete
        seller = to_cancel.seller
        owner_name = "%s %s" % (to_cancel.fname, to_cancel.lname)
        purchase_price = to_cancel.purchase_price
        to_cancel.delete()
        
        #now increase the seller's stock by one to reflect the canceled sale
        #this assumes the stock exists, and the seller only has one stock for a given product type
        stk = Stock.objects.filter(seller=seller, product__code=serial[0:2])[0]
        stk.stock_amount += 1
        stk.save()
        seller.cached_revenue -= (purchase_price * 1000)
        seller.save()

        #confirm the cancellation
        response = self.get_current_stock(seller)
        self.respond("Sale %s to %s canceled. Stock for %s: %s" % (serial, owner_name, seller.alias, response))

    def get_current_stock(self, usr):
        cur_stock = Stock.objects.filter(seller=usr)
        response = ""
        if cur_stock is not None:
            for s in list(cur_stock):
                response += "%s %s, " % (s.stock_amount, s.product.display_name)
            return response.rstrip()[:-1]
        else:
            return "not found."
                       
