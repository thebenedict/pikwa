#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from retail.models import Product, Stock

class NewProductHandler(KeywordHandler):
    """
    Used by administrators to add newly recieved product into the system.

    """

    keyword = "n|new|add"

    def help(self):
        user = self.msg.connection.contact
        if not user.role:
            self.respond("You do not have permission to add new product.")
        else:
            self.respond("Usage: new (code)(amount)\nExample: new 100ew")

    def handle(self, restock_string):
        user = self.msg.connection.contact
        #Check permissions. Unregistered users will receive an unhelpful error message.
        if not user.role:
            self.respond("You do not have permission to use this command.")
            return True
    
        restock_list = self.parse_restock_string(restock_string)
        errors = []
        response = ""
        for code, amount in restock_list:
            #ignore incorrect codes
            if amount <= 0: #no matching product code
                errors.append(code)
            else:
                target_product = Product.by_code(code)
                current_stock = Stock.get_existing(user.alias, code)
                if current_stock is None:
                    s = Stock(seller=user, product=target_product, stock_amount=amount)
                    s.save()
                    response += "%s %s, " % (amount, target_product.display_name)
                else:
                    current_stock.stock_amount += amount
                    current_stock.save()
                    response += "%s %s, " % (amount, target_product.display_name)
        
        if response:
            response = response[:-2] + " added. "
       
        if errors:
            for err in errors:
                response += "%s " % err
            response += "not recognized. "
        
        self.respond("%sCurrent stock: %s" % (response, self.get_current_stock(user)))

    def parse_restock_string(self, rstring):
        if rstring == '':
            return False
        restock_list = []
        restock_split = rstring.split(" ")
        for s in restock_split:
            code = (''.join([l for l in s if l.isalpha()])).upper()
            exists = Product.objects.filter(code = code)
            if exists:
                amount_str = ''.join([d for d in s if d.isdigit()])
                if amount_str.isdigit():
                    amount = int(amount_str)
                else:
                    amount = -1 #no code found
            else:
                amount = 0 #code not found
            restock_list.append([code,amount])
        return restock_list

    def get_current_stock(self, usr):
        cur_stock = Stock.objects.filter(seller=usr)
        response = ""
        if cur_stock is not None:
            for s in list(cur_stock):
                response += "%s %s, " % (s.stock_amount, s.product.display_name)
            return response.rstrip()[:-1]
        else:
            return "not found."
