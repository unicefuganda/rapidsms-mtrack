from .forms import ReplyTextForm, MassTextForm, AskAQuestionForm
from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from generic.sorters import SimpleSorter
from generic.views import generic, generic_row
from mtrack.models import AnonymousReport
from mtrack.reports import ManagementReport
from mtrack.utils import get_dashboard_messages, get_facility_reports_for_view, \
    get_all_facility_reports_for_view
from mtrack.views.anonymous_reports import edit_report, delete_report
from mtrack.views.dashboard import admin, approve
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission

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

    #FIXTHIS anonymous messages
    # login required added
    url(r'^anonymousreports/$', login_required(generic), {
        'model':AnonymousReport,  
        'queryset': AnonymousReport.objects.all().order_by('-date','action'), #action --> analogous to status of report      
        'objects_per_page':25,
        'base_template':'mtrack/mtrack_generic_base.html',
        'partial_row':'mtrack/partials/anon_row.html',
        'selectable':True,
        'results_title' : 'Anonymous Reports',
        'action_forms':[ReplyTextForm, AskAQuestionForm],
        'columns':[('Facility', True, 'health_facility', SimpleSorter(),),
            ('District', True, 'district', SimpleSorter(),),
            ('Date', True, 'date', SimpleSorter(),),
            ('Reports', True, 'messages', None,),
            ('Status', True, 'actions', SimpleSorter(),),
            ('Comments', True, 'comments', SimpleSorter(),),
            ('Responses', True, 'responses', None,),
            ('', False, '', None,)], \
        'results_title':'Anonymous reports',
    }, name='dashboard-anonymous-messagelog'),

    url(r'^anonymousreports/(\d+)/edit/', edit_report, name='edit-report'),
    url(r'^anonymousreports/(\d+)/delete/', delete_report, name='delete-report'),
    url(r'^anonymousreports/(?P<pk>\d+)/show', generic_row, {'model':AnonymousReport, 'partial_row':'mtrack/partials/anon_row.html'}),

    # FIXME: add anonymous repots to dashboard
    url(r'^dashboard/ars/$', direct_to_template, {'template':'mtrack/partials/demo_areports.html'}, name="dashboard-anonymous"),
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
        'sort_column':'message__connection__contact__healthproviderbase__healthprovider__facility__name', \
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
                   ('', False, '', None,)], \
        'sort_column':'message__connection__contact__healthproviderbase__healthprovider__facility__name', \
    }, name='facility-reports'),


    (r'^mtrack/mgt/stats/', include(ManagementReport().as_urlpatterns(name='mtrack-mgt-stats'))),
)
