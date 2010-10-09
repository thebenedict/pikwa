#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from retail.models import Product, Stock, StockTransaction
from datetime import datetime

class RestockHandler(KeywordHandler):
    """
    Allow remote users to transfer stock to another user.
    Transfers are from one user (the 'stocker') to another (the 'target').
    The transfer must be confirmed by the target before it is processed.

    """

    keyword = "restock|rs"

    def help(self):
        self.respond("Usage: restock (recipient) (code)(amount)\nExample: restock dnombo 5ew")

    def handle(self, text):
        args = text.partition(' ')
        target_alias = args[0].lower()
        restock_list = self.parse_restock_string(args[2].lower())
        if not restock_list:
            self.help()
            return True

        # confirm that alias exists
        try:
            target = Contact.objects.get(alias=target_alias)
        except:
            self.respond("Sorry, user %s was not found. Please check your spelling and try again" % target_alias)
            return True
        
        stocker = self.msg.connection.contact

        errors = []
        stockouts = []
        pending = []
        response = ""
        notification = ""
        #admin must create this user, for holding pending stock transactions
        nobody = Contact.by_alias("nobody")

        for code, amount in restock_list:
            if amount == 0:
                errors.append(code)
            if amount == -1 or code == '':
                self.respond("Missing product code or amount. Restock messages cannot contain spaces.\nExample: restock dnombo 5ew")
                return True
            else:
                current_stock = Stock.get_existing(stocker.alias, code)
                #make sure the initiator of the transaction has enough stock
                if current_stock is None or current_stock.stock_amount < amount:
                    stockouts.append(code)
                else:
                    target_product = Product.by_code(code)
                    s = Stock(seller = nobody, product=target_product, stock_amount=amount)
                    s.save()
                    pending.append(s)
                    current_stock.stock_amount -= amount
                    current_stock.save()

        if pending:
            #create the transaction object and add stock to be moved
            trans = StockTransaction(initiator = stocker, recipient = target, status = 2, date_initiated = datetime.now())
            trans.save() #need to generate a primary key before adding products
            for p in pending:
                trans.to_transfer.add(p)
                response += "%s %s " % (p.stock_amount, p.product.display_name)
                notification += "%s %s " % (p.stock_amount, p.product.display_name)

            trans.save()
            response += "sent to %s. " % target.alias

        if stockouts:
            for out in stockouts:
                response += "%s " % out
            response += "out of stock. "

        if errors:
            for err in errors:
                response += "%s " % err
            response += "not recognized."

        self.respond(response)

        if notification:
            notification += "being sent by %s. Reply 'yes' to accept, 'no' to reject." % stocker.alias
            target.message(notification)


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


