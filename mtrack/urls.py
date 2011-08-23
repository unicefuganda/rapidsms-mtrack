from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import *
from generic.views import generic
from django.views.generic.simple import direct_to_template
from rapidsms_httprouter.models import Message
from .utils import get_dashboard_messages

urlpatterns = patterns('',
    url(r'^facility/(?P<code>\w+)/config/?$',
       'mtrack.views.facility_detail',
       name='facility_detail'),
    url(r'^dashboard/messagelog/$', generic, {
        'model':Message,
        'queryset':get_dashboard_messages,
        'objects_per_page':5,
        'base_template':'mtrack/partials/dashboard.html',
        'selectable':False,
        'results_title':'',
    }, name='dashboard-messagelog'),
    # FIXME: dashboard admin summary
    url(r'^dashboard/admin/$', direct_to_template, {'template':'mtrack/partials/demo_admin.html'}, name='dashboard-admin'),
    # FIXME: dashboard alerts list
    url(r'^dashboard/alerts/$', direct_to_template, {'template':'mtrack/partials/demo_alerts.html'}, name='dashboard-alerts'),
    # FIXME: dashboard approve module
    url(r'^dashboard/approve/$', direct_to_template, {'template':'mtrack/partials/demo_approve.html'}, name='dashboard-approve'),
    # FIXME: dashboard contacts
    url(r'^dashboard/contacts/$', direct_to_template, {'template':'mtrack/partials/demo_contacts.html'}, name='dashboard-contacts'),
    # FIXME: dashboard stock map
    url(r'^dashboard/stockmap/$', direct_to_template, {'template':'mtrack/partials/demo_map_stock.html'}, name='dashboard-stock-map'),
    # FIXME: dashboard disease map
    url(r'^dashboard/epimap/$', direct_to_template, {'template':'mtrack/partials/demo_map_epi.html'}, name='dashboard-epi-map'),
)
