#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import csv

from django.template import RequestContext
from django.core.urlresolvers import reverse#
from django.http import HttpResponseRedirect#
from django.http import HttpResponse
from django.shortcuts import render_to_response

from django.db.models import Sum

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.models import User

from rapidsms.models import Contact

from pikwa.forms import SaleForm
from pikwa.tables import SaleTable, PerformanceTable

from retail.models import Sale, Stock, Product

from datetime import datetime, timedelta, time

def get_inventory_list(org):
    inventory_list = []
    for p in Product.objects.all():
        sale_count = Sale.objects.filter(seller__organization=org, product=p).count()
        stocks = Stock.objects.filter(seller__organization=org, product=p)
        if stocks:
            stock_count = stocks.aggregate(Sum('stock_amount'))
            inventory_list.append({'product': p, 'sale_count': sale_count, 'stock_count': stock_count['stock_amount__sum']})
    return inventory_list

def get_sale_bars(org):
    sale_bars = []
    sales = Sale.objects.filter(seller__organization=org)
    for i in range(0,30):
        d = datetime.now().date() - timedelta(days=i)
        day_start = datetime.combine(d, time.min)
        day_end = datetime.combine(d, time.max)
        sale_count = sales.filter(purchase_date__range=(day_start, day_end)).count()
        if i % 3 == 0:
            label = d.strftime("%d-%b")
        else:
            label = ""
        sale_bars.insert(0,{'date': d, 'sale_count': sale_count, 'label': label})
    return sale_bars

@login_required
#TODO take the user somewhere informative if they don't pass the test
@user_passes_test(lambda u: u.get_profile().organization is not None)
def dashboard(request, template_name="retail/dashboard.html"):
    context = {}
    org = request.user.get_profile().organization
    
    staff_count = Contact.objects.filter(organization=org).count()
    all_sales = Sale.objects.filter(seller__organization=org)
    sale_count = all_sales.count()
    total_revenue = all_sales.aggregate(Sum('purchase_price'))
    inventory_list = get_inventory_list(org)

    context['organization'] = org
    context['staff_count'] = staff_count
    context['sale_count'] = sale_count
    try:
        context['total_revenue'] = int(total_revenue['purchase_price__sum']*1000)
    except:
        context['total_revenue'] = 0
    context['inventory_list'] = inventory_list
    context['performance_table'] = PerformanceTable(Contact.objects.filter(organization = org), request)
    context['sale_bars'] = get_sale_bars(org)

    return  render_to_response(template_name, {}, context_instance=RequestContext(request, context))

@login_required
@user_passes_test(lambda u: u.get_profile().organization is not None)
def sales(request, template_name="retail/sales.html"):
    org = request.user.get_profile().organization
    sale = None
    sale_form = SaleForm(instance=sale, initial={'purchase_date': datetime.now()})
    sale_form.fields['seller'].queryset=Contact.objects.filter(organization=org)
    sale_form.fields['purchase_date']

    if request.method == "POST":
        print sale_form.errors.values()
        sale_form = SaleForm(data=request.POST)
        if sale_form.is_valid():
            sale = sale_form.save()
            return HttpResponseRedirect(reverse(sales))
   
    return render_to_response(
        "retail/sales.html", {
            "organization": org,
            "sale_table": SaleTable(Sale.objects.filter(seller__organization=request.user.get_profile().organization), request),
            "sale_form": sale_form,
        }, context_instance=RequestContext(request)
    )

@login_required
@user_passes_test(lambda u: u.get_profile().organization is not None)
def csv_export(request):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=sales_export.csv'

    writer = csv.writer(response)
    sale_list = Sale.objects.all().order_by('purchase_date')
    writer.writerow(['Sale date', 'Retailer', 'Serial #', 'Last name', 'First name', 'Primary phone', 'Secondary phone', 'Region', 'Location notes'])
    for s in sale_list:
        writer.writerow([s.purchase_date.date().strftime("%Y-%m-%d"), s.seller, s.serial, s.lname.capitalize(), s.fname.capitalize(), s.pri_phone, s.sec_phone,  s.get_region_display(), s.description])
    return response

@login_required
@user_passes_test(lambda u: u.get_profile().organization is not None)
def advanced(request):
    return render_to_response("retail/advanced.html", {}, context_instance=RequestContext(request))


