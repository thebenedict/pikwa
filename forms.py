#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import forms
from django.contrib.admin import widgets
from rapidsms.models import *
from retail.models import Sale, Stock, Product


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ("connections", "organization", "language")

class SaleForm(forms.ModelForm):
    def clean_serial(self):
        cleaned_data = self.cleaned_data
        print("Cleaned data is %s" % self.cleaned_data)
        code = cleaned_data.get("serial")[0:2]
        print("Code from serial is %s" % code)
        try:
            prod = Product.objects.get(code=code)
        except:
            raise forms.ValidationError("Product code %s not found" % code)
        #TODO this doesn't work, need to find a way to set product from 
        #a code extracted from a SN
        #cleaned_data["product"] = prod
        return cleaned_data["serial"]

    def clean_seller(self):
        cleaned_data = self.cleaned_data
        print("Cleaned data from clean_seller is %s" % self.cleaned_data)
        #verify that seller has the item to be sold in stock
        current_stock = Stock.get_existing(cleaned_data.get("seller").alias, cleaned_data.get("product").code)
        if current_stock is None or current_stock.stock_amount <= 0:
            raise forms.ValidationError("%s has no %s in stock" % (cleaned_data.get("seller").alias, cleaned_data.get("product").display_name))
        current_stock.stock_amount -= 1
        current_stock.save()
        #return cleaned_data.get("seller")
        return cleaned_data["seller"]

    class Meta:
        model = Sale
        widgets = {
            'purchase_date': widgets.AdminSplitDateTime()
        }
        #exclude = ("product")

