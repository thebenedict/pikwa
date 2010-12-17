#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from datetime import datetime
from decimal import *
from retail.models import Product, Stock, Sale

class SaleHandler(KeywordHandler):
    """
    Logic for recording a sale.

    """

    keyword = "sale|s"

    def help(self):
        self.respond("Sale format: sale serial# firstname lastname mobile# price regioncode village")

    def handle(self, sale_string):
        seller = self.msg.connection.contact
        sale_result = self.verify_sale(sale_string, seller)
        if sale_result[0] == 0: #sale failed
            self.respond("ERROR: " + ', '.join(sale_result[1]) + ". Sale format: sale serial# firstname lastname mobile# price regioncode description" )
        else:
            sale_data = sale_result[1]
            product_code = sale_result[2]
        
        #verify that seller has the item to be sold in stock
        current_stock = Stock.get_existing(sale_data['seller'].alias, product_code)
        if current_stock is None or current_stock.stock_amount <= 0:
            self.respond("ERROR: No %s in stock." % product_code)
            return True
        
        #verify that the serial # is not a duplicate
        exists = Sale.by_serial(sale_data['serial'])
        if exists:
            self.respond("ERROR: %s is already registered." % sale_data['serial'])
            return True
          
        #now create and save the new sale record
        s = Sale(**sale_data)
        s.save()
        
        #subtract the sale from the retailer's stock
        current_stock.stock_amount -= 1
        current_stock.save()
        
        payment_response = "Cash sale."
        self.respond("%s registered to %s %s by %s." % (s.serial, s.fname, s.lname, s.seller.alias, ) + " " + payment_response)        


    def verify_sale(self, input, rep):
        """
        parsing and error checking for sales
        """

        #assume a valid sale, change status to 0 if we encounter an error
        status = 1
        errors = []
        
        data_list = input.split()
        if len(data_list) < 7:
            status = 0
            errors.append("Sale missing information. Please check the format and try again")
            return ([status, errors])            
        
        #check serial number
        sn = data_list[0].upper()
        if len(sn) is not 7:
            errors.append("SN must be 7 characters")
        if sn[0:2].isdigit():
            errors.append("SN must start with a product code")
        
        #get product code
        #this assumes product codes are all letters, and they're the only letters in a serial number
        product_code = (''.join([l for l in sn if l.isalpha()])).upper()
        prod = Product.by_code(product_code)
        if not prod:
            errors.append("product %s not found" % product_code)
            
        #check product owner's name
        if not ((data_list[1] + data_list[2]).isalpha()):
            errors.append("cust name not understood")
        if (len(data_list[1]) < 2 or len(data_list[2]) < 2):
            errors.append("cust name too short")
        else:
            first = data_list[1].title()
            last = data_list[2].title()
        
        #check phone
        if not (data_list[3].isdigit()):
            errors.append("phone # can only be digits")
        if len(data_list[3]) < 10:
            errors.append("phone # is mising digits")
        
        #check price
        price = Decimal(data_list[4])
        if price > 50:
            errors.append("price is too high")
        if price < 4:
            errors.append("price is too low")        
        
        #check region
        #this is a placeholder for now
        region =  data_list[5].upper()
                
        #take anything left as free text description
        des = ' '.join(d.capitalize() for d in data_list[6:])   
        
        if errors:
            #something went wrong, return error messages
            status = 0
            return ([status, errors])
        else: 
            #nothing went wrong, return sale data
            sale_dict = dict ({'seller': rep,
                               'serial': sn,
                               'product': prod,
                               'fname': data_list[1].capitalize(),
                               'lname': data_list[2].capitalize(),
                               'pri_phone': data_list[3],
                               'purchase_price': price,
                               'purchase_date': datetime.now(),
                               'region': region,
                               'description': des})
            return ([status, sale_dict, product_code])            
