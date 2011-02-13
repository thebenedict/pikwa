#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
#from pikwa.retail import views
from . import views

urlpatterns = patterns('',
    url(r'^admin_dashboard/$', views.admin_dashboard, name='admin-dashboard'),
    url(r'^advanced/$', 'retail.views.advanced', name='advanced'),
    url(r'^sales/$', 'retail.views.sales', name='sales'),
    url(r'^sales/export/$', views.csv_export,
        name='export'),
    url(r'^sales/export/(?P<org_id>\d+)/$', views.csv_export,
        name='export'),
#(r'^retail_media/(?P<path>.*)$', 'django.views.static.serve',
#        {'document_root': '/retail/static'}),
)


'''scrap
urlpatterns = patterns('',

    url(r'^$',
        'registration.views.registration',
        name="registration"),

    url(r'^registration/(?P<pk>\d+)/edit/$',
        'registration.views.registration',
        name="registration_edit")
)'''

    
