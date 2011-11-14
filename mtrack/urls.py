from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import patterns, url, include
from generic.views import generic
from generic.sorters import SimpleSorter
from django.views.generic.simple import direct_to_template
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission
from mtrack.utils import get_dashboard_messages
from mtrack.views.dashboard import admin, approve
from mtrack.utils import get_facility_reports_for_view, get_all_facility_reports_for_view
from mtrack.reports import ManagementReport

urlpatterns = patterns('',
#    url(r'^facility/(?P<code>\w+)/config/?$',
#       'mtrack.views.facility_detail',
#       name='facility_detail'),
    url(r'^dashboard/messagelog/$', generic, {
        'model':Message,
        'queryset':get_dashboard_messages,
        'objects_per_page':5,
        'base_template':'mtrack/partials/dashboard.html',
        'partial_base':'mtrack/partials/messages_base.html',
        'partial_header':'mtrack/partials/messages_header.html',
        'selectable':False,
        'results_title':'',
    }, name='dashboard-messagelog'),

    #annonymous messages
    url(r'^dashboard/annonymous/$', generic, {
        'model':Message,
        'queryset':get_dashboard_messages,
        'objects_per_page':5,
        'base_template':'mtrack/partials/dashboard.html',
        'partial_base':'mtrack/partials/messages_base.html',
        'partial_header':'mtrack/partials/messages_header.html',
        'selectable':False,
        'results_title':'',
    }, name='dashboard-annonymous-messagelog'),

    # FIXME: dashboard admin summary
    url(r'^dashboard/admin/$', admin, name='dashboard-admin'),

    # FIXME: dashboard alerts list
    url(r'^dashboard/alerts/$', direct_to_template, {'template':'mtrack/partials/demo_alerts.html'}, name='dashboard-alerts'),

    url(r'^dashboard/approve/$', approve, name='dashboard-approve'),
    # FIXME: dashboard contacts
    url(r'^dashboard/contacts/$', direct_to_template, {'template':'mtrack/partials/demo_contacts.html'}, name='dashboard-contacts'),
    # FIXME: dashboard stock map
    url(r'^dashboard/stockmap/$', direct_to_template, {'template':'mtrack/partials/demo_map_stock.html'}, name='dashboard-stock-map'),
    # FIXME: dashboard disease map
    url(r'^dashboard/epimap/$', direct_to_template, {'template':'mtrack/partials/demo_map_epi.html'}, name='dashboard-epi-map'),

    (r'^alerts/', include('alerts.urls')),

    url(r'^approve/$', generic, { \
        'model':XFormSubmission, \
        'queryset':get_facility_reports_for_view, \
        'objects_per_page':25, \
        'base_template':'mtrack/mtrack_generic_base.html', \
        'partial_base':'mtrack/partials/reports_base.html', \
        'partial_row':'mtrack/partials/report_row.html', \
        'results_title':'Last Reporting Period Results', \
        'columns':[('Facility', True, 'message__connection__contact__healthproviderbase__healthprovider__facility__name', SimpleSorter()), \
                   ('Reporter', True, 'message__connection__contact__name', SimpleSorter(),), \
                   ('Report', True, 'raw', SimpleSorter(),), \
                   ('Date', True, 'created', SimpleSorter(),), \
                   ('', False, '', None,)], \
    }, name='approve'),

    url(r'^hc/reports/$', generic, { \
        'model':XFormSubmission, \
        'queryset':get_all_facility_reports_for_view, \
        'objects_per_page':25, \
        'base_template':'mtrack/mtrack_generic_base.html', \
        'partial_row':'mtrack/partials/report_row.html', \
        'results_title':'Reports', \
        'columns':[('Facility', True, 'message__connection__contact__healthproviderbase__healthprovider__facility__name', SimpleSorter()),
                   ('Reporter', True, 'message__connection__contact__name', SimpleSorter(),),
                   ('Report', True, 'raw', SimpleSorter(),),
                   ('Date', True, 'created', SimpleSorter(),), \
                   ('', False, '', None,)],
    }, name='facility-reports'),


    (r'^mtrack/mgt/stats/', include(ManagementReport().as_urlpatterns(name='mtrack-mgt-stats'))),
)
