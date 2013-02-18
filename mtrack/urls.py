from .forms import ReplyTextForm, ApproveForm, RejectForm
from django.conf.urls.defaults import patterns, url, include
from mtrack.decorators import login_required
from django.views.generic.simple import direct_to_template
from generic.sorters import SimpleSorter
from generic.views import generic, generic_row
from mtrack.models import AnonymousReport, Schedules
from mtrack.reports import ManagementReport
from mtrack.utils import get_dashboard_messages, get_facility_reports_for_view, \
    get_all_facility_reports_for_view, get_all_ussd_facility_reports_for_view, get_anonymous_reports
from mtrack.views.anonymous_reports import edit_anonymous_report, detail_anonymous_report, delete_report, create_excel
from mtrack.views.dashboard import admin, approve
from mtrack.views.reports import edit_report
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission
from mtrack.views.visuals import stock_level_viz, stock_level_piechart
from mtrack.views.dataentry import data_entry, ajax_portal
from mtrack.views.facility_locations import facility_cas, ajax_portal2
from mtrack.views.schedules import broadcasts

urlpatterns = patterns('',
                       #    url(r'^facility/(?P<code>\w+)/config/?$',
                       #       'mtrack.views.facility_detail',
                       #       name='facility_detail'),
                       url(r'^dashboard/messagelog/$', generic, {
                           'model': Message,
                           'queryset': get_dashboard_messages,
                           'objects_per_page': 5,
                           'base_template': 'mtrack/partials/dashboard.html',
                           'partial_base': 'mtrack/partials/messages_base.html',
                           'partial_header': 'mtrack/partials/messages_header.html',
                           'selectable': False,
                           'results_title': '',
                       }, name='dashboard-messagelog'),

                       #FIXTHIS anonymous messages
                       # login required added
                       url(r'^anonymousreports/excelreport/$', create_excel),
                       url(r'^anonymousreports/$', login_required(generic), {
                           'model': AnonymousReport,
                           # primitive filtering by actions
                           #TODO subclass SimpleSorter to sort actions
                           'queryset': get_anonymous_reports, #action --> analogous to status of report
                           'objects_per_page': 25,
                           'base_template': 'mtrack/partials/anonymous_base.html',
                           'partial_row': 'mtrack/partials/anon_row.html',
                           'partial_header': 'mtrack/partials/partial_header.html',
                           'selectable': True,
                           'results_title': 'Anonymous Reports',
                           #'filter_forms':[StatusFilterForm],
                           'action_forms': [ReplyTextForm], #, AskAQuestionForm],
                           'columns': [('Facility', True, 'health_facility', SimpleSorter(),),
                                       ('District', True, 'district', SimpleSorter(),),
                                       ('Date', True, 'date', SimpleSorter(),),
                                       ('Reports', True, 'messages', None,),
                                       ('Topic', True, 'topic', SimpleSorter(),),
                                       ('Status', True, 'action', SimpleSorter(),),
                                       ('A Center', True, 'action_center', SimpleSorter(),),
                                       ('A Taken', True, 'action_taken', SimpleSorter(),),
                                       ('Comments', True, 'comments', None,),
                                       ('', False, '', None,)],
                           #'sort_column':'date',
                       }, name='dashboard-anonymous-messagelog'),

                       url(r'^anonymousreports/(\d+)/edit/', edit_anonymous_report, name='edit-report'),
                       url(r'^anonymousreports/(\d+)/detail/', detail_anonymous_report, name='detail-report'),
                       url(r'^anonymousreports/(\d+)/delete/', delete_report, name='delete-report'),
                       url(r'^anonymousreports/(?P<pk>\d+)/show', generic_row,
                           {'model': AnonymousReport, 'partial_row': 'mtrack/partials/anon_row.html'}),
                       url(r'^stocklevelviz/$', stock_level_viz, name='stock-viz'),
                       url(r'^stocklevelpie/$', stock_level_piechart, name='stock-pie'),


                       # FIXME: add anonymous repots to dashboard
                       url(r'^dashboard/ars/$', direct_to_template, {'template': 'mtrack/partials/demo_areports.html'},
                           name="dashboard-anonymous"),
                       # FIXME: dashboard admin summary
                       url(r'^dashboard/admin/$', admin, name='dashboard-admin'),

                       # FIXME: dashboard alerts list
                       url(r'^dashboard/alerts/$', direct_to_template, {'template': 'mtrack/partials/demo_alerts.html'},
                           name='dashboard-alerts'),

                       url(r'^dashboard/approve/$', approve, name='dashboard-approve'),
                       # FIXME: dashboard contacts
                       url(r'^dashboard/contacts/$', direct_to_template,
                           {'template': 'mtrack/partials/demo_contacts.html'}, name='dashboard-contacts'),
                       # FIXME: dashboard stock map
                       url(r'^dashboard/stockmap/$', direct_to_template,
                           {'template': 'mtrack/partials/demo_map_stock.html'}, name='dashboard-stock-map'),
                       # FIXME: dashboard disease map
                       url(r'^dashboard/epimap/$', direct_to_template,
                           {'template': 'mtrack/partials/demo_map_epi.html'}, name='dashboard-epi-map'),

                       (r'^alerts/', include('alerts.urls')),

                       url(r'^approve/$', login_required(generic), { \
                           'model': XFormSubmission, \
                           'queryset': get_facility_reports_for_view, \
                           'objects_per_page': 25, \
                           'base_template': 'mtrack/approve_base.html', \
                           'partial_row': 'mtrack/partials/report_row.html', \
                           'results_title': 'Last Reporting Period Results', \
                           'action_forms': [ApproveForm, RejectForm], \
                           'columns': [('Facility', True,
                                        'connection__contact__healthproviderbase__healthprovider__facility__name',
                                        SimpleSorter()), \
                                       ('Reporter', True, 'connection__contact__name', SimpleSorter(),), \
                                       ('Report', True, 'raw', SimpleSorter(),), \
                                       ('Week#', False, '', None,),
                                       ('Date', True, 'created', SimpleSorter(),), \
                                       ('Approved', True, 'approved', SimpleSorter(),), \
                                       ('', False, '', None,)], \
                           'sort_column': 'connection__contact__healthproviderbase__healthprovider__facility__name', \
                           }, name='approve'),

                       url(r'^hc/reports/$', login_required(generic), { \
                           'model': XFormSubmission, \
                           'queryset': get_all_facility_reports_for_view, \
                           'objects_per_page': 25, \
                           'base_template': 'mtrack/mtrack_generic_base.html', \
                           'partial_row': 'mtrack/partials/report_row.html', \
                           'results_title': 'Reports', \
                           'action_forms': [ApproveForm, RejectForm], \
                           'columns': [('Facility', True,
                                        'message__connection__contact__healthproviderbase__healthprovider__facility__name',
                                        SimpleSorter()),
                                       ('Reporter', True, 'message__connection__contact__name', SimpleSorter(),),
                                       ('Report', True, 'raw', SimpleSorter(),),
                                       ('Week #', False, '', None,),
                                       ('Date', True, 'created', SimpleSorter(),), \
                                       ('Approved', True, 'approved', SimpleSorter(),), \
                                       ('', False, '', None,)], \
                           'sort_column': 'connection__contact__healthproviderbase__healthprovider__facility__name', \
                           }, name='facility-reports'),
                       url(r'^ussd/reports/$', generic, { \
                           'model': XFormSubmission, \
                           'queryset': get_all_ussd_facility_reports_for_view, \
                           'objects_per_page': 25, \
                           'base_template': 'mtrack/mtrack_generic_base.html', \
                           'partial_row': 'mtrack/partials/report_ussd_row.html', \
                           'results_title': 'Reports', \
                           'columns': [('Facility', True,
                                        'connection__contact__healthproviderbase__healthprovider__facility__name',
                                        SimpleSorter()),
                                       ('Reporter', True, 'connection__contact__name', SimpleSorter(),),
                                       ('Report', False, '', None,), \
                                       ('Week #', False, '', None,), \
                                       ('Date', True, 'created', SimpleSorter(),), \
                                       ('Approved', False, '', None,), \
                                       ('', False, '', None,)], \
                           'sort_column': 'connection__contact__healthproviderbase__healthprovider__facility__name'
                       }, name='ussd-facility-reports'),
                       url(r"^xforms/submissions/(\d+)/edit/$", login_required(edit_report)),
                       url(r"^dataentry/$", login_required(data_entry), name='dataentry'),
                       url(r"^facility_cas/$", login_required(facility_cas)),
                       url(r"^ajax_portal/$", ajax_portal),
                       url(r"^ajax_portal2/$", ajax_portal2),
                       url(r"^schedules/$", login_required(broadcasts), name='schedule_creator'),

                       (r'^mtrack/mgt/stats/', include(ManagementReport().as_urlpatterns(name='mtrack-mgt-stats'))),
                       url(r'^mtrack/logistics/?$',
                           'logistics.views.aggregate',
                           {'location_code': 'western'},
                           name="mtrack-logistics"),

                       url(r'^mtrack/schedule-list/$', login_required(generic), {
                           'model': Schedules,
                           'queryset': Schedules.objects.all(),
                           'objects_per_page': 25,
                           'partial_row': 'mtrack/schedule/schedule_row.html',
                           'base_template': 'mtrack/schedule/schedule_base.html',
                           'results_title': 'Reminder Schedules',
                           'sort_column': 'start_date',
                           'sort_ascending': False,
                           'columns': [('Message', True, 'message', SimpleSorter()),
                                       ('Start Date', True, 'start_date', SimpleSorter(),),
                                       ('End Date', True, 'end_date', SimpleSorter(),),
                                       ('Start Time', True, 'start_time', SimpleSorter(),),
                                       ('Enabled', False, '', None,),
                                       ('Recipient Locations', True, 'recipient_location', SimpleSorter(),),
                                       ('Group References', True, 'group_ref', SimpleSorter(),),
                                       ('Delete', False, 'action', None,),
                           ],
                       }, name="reminder-schedules"),
                       url(r'^mtrack/schedule/delete/(\d+)/$', 'mtrack.views.schedules.delete_schedule',
                           name='delete_schedule'),
                       url(r'^mtrack/schedule/edit/(\d+)/$', 'mtrack.views.schedules.edit_schedule',
                           name='edit_schedule'),
                       url(r'^mtrack/massmessages_excel/$', 'mtrack.views.massmessage_excel', name='massmessage_excel')
)
