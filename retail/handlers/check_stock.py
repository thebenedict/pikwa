#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from retail.models import Stock

class CheckStockHandler(KeywordHandler):
    """
    Allow remote users to find out their, or another user's, current stock.
    """

    keyword = "stock|stk|st|"

    # Using the help function to return a users' own stock.
    # It's a hack, but it's a simple way to do it since no arguments are needed 	
    def help(self):
        user = self.msg.connection.contact
        response = self.get_current_stock(user)
        self.respond("Stock for %s: %s" % (user.alias, response))

    def handle(self, seller_alias):
        try:
            seller = Contact.by_alias(seller_alias)
        except:
            self.respond("Sorry, user %s was not found. Please check your spelling and try again" % seller_alias)
        else:
            response = self.get_current_stock(seller)
            self.respond("Stock for %s: %s" % (seller.alias, response))

    def get_current_stock(self, usr):
        cur_stock = Stock.objects.filter(seller=usr)
        response = ""
        if cur_stock is not None:
            for s in list(cur_stock):
                response += "%s %s, " % (s.stock_amount, s.product.display_name)
            return response.rstrip()[:-1]
        else:
            return "not found."
