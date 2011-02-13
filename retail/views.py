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

from retail.models import Sale, Stock, Product, Organization

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
    sales = Sale.objects.all()
    if org != "ALL":
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
@user_passes_test((lambda u: u.get_profile().organization is not None) or (lambda u: u.is_staff))
def dashboard(request, org_id=None, template_name="retail/dashboard.html"):
    context = {}
    if org_id is None and request.user.is_staff:
        return admin_dashboard(request)
    elif request.user.is_staff:
        try:
            org = Organization.objects.get(id=org_id)
        except:
            return HttpResponse(status=404)
    elif request.user.get_profile().organization is not None:
        org = request.user.get_profile().organization
    else:
        return HttpResponse(status=550)
    
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
    #TODO make top_sellers include only a fixed number of sellers, or paginate
    top_sellers = Contact.objects.filter(organization=org)
    context['performance_table'] = PerformanceTable(top_sellers, request)
    context['sale_bars'] = get_sale_bars(org)

    return  render_to_response(template_name, {},
 context_instance=RequestContext(request, context))

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request, template_name="retail/admin_dashboard.html"):
    context = {}
    
    organization_count = Organization.objects.count()
    total_staff_count = Contact.objects.count()
    total_sale_count = Sale.objects.count()
    total_revenue = Sale.objects.aggregate(Sum('purchase_price'))

    #generate data for heat map
    map_data=[]
    for n in range(1,27):
        #get the capital letter region code per Sale.REGION_CHOICES
        p = chr(n+64)
        sls = Sale.objects.filter(region=p)
        n_padded = '%02d' % n
        percent_sales = int(round(float(sls.count()) / total_sale_count * 100,0))
        if percent_sales > 0:
            percent_sales += 10 #offset for visibility
        region_data = {'number': n_padded, 'sale_percent': percent_sales}
        map_data.append(region_data)

    #per organization stats table
    org_table=[]
    for o in Organization.objects.all():
        sales = Sale.objects.filter(seller__organization=o)
        sale_count = sales.count()
        if sale_count > 0:
            sellers = Contact.objects.filter(organization=o)
            staff_count = sellers.count()
            revenue = sellers.aggregate(Sum('cached_revenue'))['cached_revenue__sum']
            org_data = {'name': o.display_name, 'id': o.id, 'sale_count': sale_count, 'staff_count': staff_count, 'revenue': revenue}
            org_table.append(org_data)

    context['total_staff_count'] = total_staff_count
    context['total_sale_count'] = total_sale_count
    try:
        context['total_revenue'] = int(total_revenue['purchase_price__sum']*1000)
    except:
        context['total_revenue'] = 0
    context['map_data'] = map_data
    context['org_table'] = org_table

    return  render_to_response(template_name, {},
 context_instance=RequestContext(request, context))


@login_required
@user_passes_test(lambda u: u.get_profile().organization is not None)
def sales(request, template_name="retail/sales.html"):
    org = request.user.get_profile().organization
    sale = None
    sale_form = SaleForm(instance=sale, initial={'purchase_date': datetime.now()})
    sale_form.fields['seller'].queryset=Contact.objects.filter(organization=org)
    sale_form.fields['purchase_date']

    if request.method == "POST":
        sale_form = SaleForm(data=request.POST)
        if sale_form.is_valid():
            #since sale.product is excluded from the form, get it from the
            #first two characters of the serial no. The form validation
            #checks that the product exists, and is in stock for the seller
            #so this is probably a safe way to do it
            sale = sale_form.save(commit=False)
            sale.product = Product.by_code(sale.serial[0:2].upper())
            sale.save() 
            return HttpResponseRedirect(reverse(sales))
   
    return render_to_response(
        "retail/sales.html", {
            "organization": org,
            "sale_table": SaleTable(Sale.objects.filter(seller__organization=request.user.get_profile().organization), request),
            "sale_form": sale_form,
        }, context_instance=RequestContext(request)
    )

@login_required
def csv_export(request, org_id=None):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=sales_export.csv'
    try:
        org = Organization.objects.get(id=org_id)
    except:
        org = None
    if org is None and request.user.is_staff:
        sale_list = Sale.objects.all().order_by('purchase_date')
    elif org == request.user.get_profile().organization or request.user.is_staff:
        sale_list = Sale.objects.filter(seller__organization = org).order_by('purchase_date')
    else:
        return HttpResponse(status=550)

    writer = csv.writer(response)
    writer.writerow(['Sale date', 'Retailer', 'Serial #', 'Last name', 'First name', 'Primary phone', 'Secondary phone', 'Region', 'Location notes'])
    for s in sale_list:
        writer.writerow([s.purchase_date.date().strftime("%Y-%m-%d"), s.seller, s.serial, s.lname.capitalize(), s.fname.capitalize(), s.pri_phone, s.sec_phone,  s.get_region_display(), s.description])
    return response

@login_required
@user_passes_test(lambda u: u.get_profile().organization is not None)
def advanced(request):
    return render_to_response("retail/advanced.html", {}, context_instance=RequestContext(request))


