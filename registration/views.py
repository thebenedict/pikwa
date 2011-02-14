#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import csv

from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from pikwa.forms import ContactForm
from rapidsms.models import Contact
from rapidsms.models import Connection
from rapidsms.models import Backend
from pikwa.retail.models import Sale, Stock
from .tables import ContactTable
from .forms import BulkRegistrationForm

@transaction.commit_on_success
@login_required
def registration(req, pk=None):
    contact = None
    sellerSummary = None

    if pk is not None:
        contact = get_object_or_404(
            Contact, pk=pk)

    if req.method == "POST":
        if req.POST["submit"] == "Delete Contact":
            contact.delete()
            return HttpResponseRedirect(
                reverse(registration))

        elif "bulk" in req.FILES:
            # TODO use csv module
            #reader = csv.reader(open(req.FILES["bulk"].read(), "rb"))
            #for row in reader:
            for line in req.FILES["bulk"]:
                line_list = line.split(',')
                name = line_list[0].strip()
                backend_name = line_list[1].strip()
                identity = line_list[2].strip()

                contact = Contact(name=name)
                contact.save()
                # TODO deal with errors!
                backend = Backend.objects.get(name=backend_name)

                connection = Connection(backend=backend, identity=identity,\
                    contact=contact)
                connection.save()

            return HttpResponseRedirect(
                reverse(registration))
        else:
            contact_form = ContactForm(
                instance=contact,
                data=req.POST)

            if contact_form.is_valid():
                contact = contact_form.save()
                return HttpResponseRedirect(
                    reverse(registration))

    else:
        contact_form = ContactForm(
            instance=contact)
            #Not allowing user to add contacts through the UI for now
            #If we eventually do, the line below sets the new contacts'
            #organization to that of the logged in user
            #################
            #instance=Contact(organization=req.user.get_profile().organization))
        seller_summary = getSellerSummary(contact)
        bulk_form = BulkRegistrationForm()

    if req.user.is_staff:
        ctable = ContactTable(Contact.objects.exclude(alias='nobody'), request=req)
        org = None
    else:
        ctable = ContactTable(Contact.objects.filter(organization=req.user.get_profile().organization), request=req)
        org = req.user.get_profile().organization

    return render_to_response(
        "registration/dashboard.html", {
            "organization": org,
            "contacts_table": ctable,
            "contact_form": contact_form,
            "bulk_form": bulk_form,
            "contact": contact,
            "seller_summary": seller_summary
        }, context_instance=RequestContext(req)
    )

def getSellerSummary(seller):
    if seller:
        sale_count = Sale.objects.filter(seller=seller).count()
        try:
            last_sale_date = Sale.objects.filter(seller=seller).latest('purchase_date').purchase_date.date()
        except:
            last_sale_date = "Never"
        stock_summary = []
        stocks = Stock.objects.filter(seller=seller)
        for s in stocks:
            stock_summary.append({"product_name": s.product.full_name, "stock_amount": s.stock_amount})

        seller_summary = {
            "sale_count": sale_count,
            "revenue": "%s Tsh" % seller.cached_revenue,
            "last_sale_date": last_sale_date,
            "stock_summary": stock_summary,
        }
        return seller_summary
