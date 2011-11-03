from generic.reporting.views import ReportView
from generic.reporting.reports import Column
from uganda_common.reports import XFormAttributeColumn, XFormSubmissionColumn, QuotientColumn
from uganda_common.views import XFormReport
from cvs.utils import active_reporters, registered_reporters
from cvs.reports import ActiveReportersColumn, RegisteredReportersColumn
from uganda_common.utils import reorganize_location
from uganda_common.reports import QuotientColumn, DifferenceColumn
from mtrack.utils import ALERTS_ACTIONED, ALERTS_CREATED, ALERTS_TOTAL, alerts_report, last_reporting_period

class AlertReportsColumn(Column):
    def __init__(self, type=ALERTS_TOTAL, period=1, **kwargs):
        Column.__init__(self, **kwargs)
        self.type = type
        self.date_range = last_reporting_period(period=period)

    def add_to_report(self, report, key, dictionary):
        val = alerts_report(report.location, date_range=self.date_range, type=self.type)
        reorganize_location(key, val, dictionary)


class ManagementReport(XFormReport):
    def get_top_columns(self):
        return [
            ('Alerts', '#', 4),
            ('VHTs', '#', 3),
            ('Health Centers', '#', 3),
        ]

    has_chart = False

    new_alerts = AlertReportsColumn(type=ALERTS_CREATED, period=1, title='Alerts this week', order=0)
    alerts_actioned = AlertReportsColumn(type=ALERTS_ACTIONED, period=1, title='Alerts actioned this week', order=1)
    percentage_change = DifferenceColumn(\
        QuotientColumn(\
            AlertReportsColumn(type=ALERTS_ACTIONED, period=1), \
            AlertReportsColumn(type=ALERTS_CREATED, period=1) \
        ), \
        QuotientColumn(\
            AlertReportsColumn(type=ALERTS_ACTIONED, period=2), \
            AlertReportsColumn(type=ALERTS_CREATED, period=2) \
        ), \
    order=2, title='% Change (prev week)')
    total_outstanding = AlertReportsColumn(type=ALERTS_TOTAL, period=1, title='Total Outstanding', order=3)

    registered_vhts = RegisteredReportersColumn(order=4, title="Active", chart_title='Active VHTs')
    active_vhts = ActiveReportersColumn(order=5, title="Active", chart_title='Active VHTs')
    percent_change_vhts = DifferenceColumn(\
        QuotientColumn(\
            ActiveReportersColumn(), \
            RegisteredReportersColumn() \
        ), \
        QuotientColumn(\
            ActiveReportersColumn(period=2), \
            RegisteredReportersColumn() \
        ), \
    order=6, title='% Change (prev week)')

    registered_hcs = RegisteredReportersColumn(order=7, title="Active", roles=['HC'], chart_title='Active HCs')
    active_hcs = ActiveReportersColumn(order=8, title="Active", roles=['HC'], chart_title='Active HCs')
    percent_change_hcs = DifferenceColumn(\
        QuotientColumn(\
            ActiveReportersColumn(roles=['HC']), \
            RegisteredReportersColumn() \
        ), \
        QuotientColumn(\
            ActiveReportersColumn(roles=['HC'], period=2), \
            RegisteredReportersColumn() \
        ), \
    order=9, title='% Change (prev week)')
