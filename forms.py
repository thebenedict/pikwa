#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import forms
from django.contrib.admin import widgets
from rapidsms.models import *
from retail.models import Sale, Stock, Product


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ("connections", "organization", "language", "cached_revenue")

class SaleForm(forms.ModelForm):
    def clean_serial(self):
        cleaned_data = self.cleaned_data
        serial = cleaned_data.get("serial")
        code = serial[0:2]
        print("Code from serial is %s" % code)
        try:
            prod = Product.objects.get(code=code)
        except:
            raise forms.ValidationError("Product code %s not found" % code)
        #exists = Sale.objects.filter(serial=serial)
        #if exists:
            raise forms.ValidationError("Serial %s already registered" % serial) 
        return cleaned_data["serial"]

    '''verify that seller has the item to be sold in stock'''
    def clean_seller(self):
        cleaned_data = self.cleaned_data
        
        code = cleaned_data.get("serial")[0:2]
        current_stock = Stock.get_existing(cleaned_data.get("seller").alias, code)
        prod = Product.objects.get(code=code)
        if current_stock is None or current_stock.stock_amount <= 0:
            raise forms.ValidationError("%s has no %s in stock" % (cleaned_data.get("seller").alias, prod.display_name))
        return cleaned_data["seller"]

    class Meta:
        model = Sale
        widgets = {
            'purchase_date': widgets.AdminSplitDateTime()
        }
        exclude = ("product")

