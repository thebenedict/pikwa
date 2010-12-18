#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.core.urlresolvers import reverse
from django.db.models import Sum
from djtables import Table, Column
from retail.models import Sale

def _sale_date(cell):
    return cell.object.purchase_date.date()

def _customer_name(cell):
    return cell.object.fname + " " + cell.object.lname

def _region(cell):
    return cell.object.get_region_display()

def _price(cell):
    return cell.object.purchase_price

def _phone(cell):
    return cell.object.pri_phone

def _seller_alias(cell):
    return cell.object.seller.alias

class SaleTable(Table):
    serial         = Column()
    purchase_date  = Column(name="Sale Date", value=_sale_date, sortable=False)
    seller         = Column(value=_seller_alias)
    customer_name  = Column(name="Customer", value=_customer_name, sortable=False)
    pri_phone      = Column(name="Phone", value=_phone, sortable=False)
    purchase_price = Column(name="Price", value=_price, sortable=False)
    region         = Column(value=_region)
    description    = Column()

    class Meta:
        order_by = '-purchase_date'

def _revenue(cell):
    sales = Sale.objects.filter(seller=cell.object)
    if sales:
        sale_total = sales.aggregate(Sum('purchase_price'))
        return int(sale_total['purchase_price__sum'] * 1000)
    else:
        return 0

def _sale_count(cell):
    return Sale.objects.filter(seller=cell.object).count()

def _phone(cell):
    try:
        return cell.object.default_connection.identity
    except:
        return ""

def _last_sale(cell):
    return Sale.objects.latest('purchase_date').purchase_date

class PerformanceTable(Table):
    alias          = Column()
    name           = Column()
    revenue        = Column(name="Revenue (Tsh)", value=_revenue, sortable=False)
    sale_count     = Column(name="Sales", value=_sale_count, sortable=False)
    phone          = Column(name="Phone", value=_phone, sortable=False)
    last_sale      = Column(name="Last Sale", value=_last_sale, sortable=False)

    #This doesn't work, need a new way to sort
    #class Meta:
        #order_by = "revenue"
