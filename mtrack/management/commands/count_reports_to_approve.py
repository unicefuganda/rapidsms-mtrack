from django.core.management.base import BaseCommand
from rapidsms_xforms.models import XFormSubmissionValue
from mtrack.utils import last_reporting_period, total_facilities
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthProvider import HealthProvider
from django.db import connections, transaction
from django.conf import settings

class Command(BaseCommand):
    help = """Loads stock data into BasicClasssLayer for geoserver"""
    def handle(self, *args, **opts):
        self.conn = connections['default']
        self.cursor = self.conn.cursor()
        locs = Location.objects.filter(type='district')
        print "Start populating........"
        for l in locs:
            self.get_facility_reports(l)
        loc = Location.tree.root_nodes()[0]
        self.get_facility_reports(loc, root=True)
        print "Done populating........"

    @transaction.commit_manually
    def get_facility_reports(self, location, root=False):
        """ This functions populates the approve_summaries table (ApproveSummary model)
        given a location say Masaka, it computes the reports waiting for approval form
        all facilities in Masaka.
        computes reports waiting approval in the following:
        a) current reporting week (reports_crp)
        b) last reporting period to date (reports_lrp_uptodate)
        
        The whole idea is to speed loading of landing page "Approve HMIS Reports"
        """
        cur = self.cursor
        facilities = total_facilities(location, count=False)
        staff = list(HealthProvider.objects.filter(groups__name='HC', facility__in=facilities).values_list('id'))

        lrp = last_reporting_period(period=0)
        lrp_todate = last_reporting_period(todate=True)

        if root:
            extra_where_clause = " AND TRUE "
        else:
            extra_where_clause = " AND reporter_id IN (%s)" % ','.join(['%s' % i for i in staff] or ['0'])

        sql_1 = ("SELECT count(distinct report_id) FROM xform_submissions_view3 "
               " WHERE has_errors = %s AND approved = %s AND date >= '%s' AND date <= '%s' %s")
        sql_1 = sql_1 % (False, False, lrp[0], lrp[1], extra_where_clause)
        cur.execute(sql_1)
        x = cur.fetchone()
        x = x[0] if x else 0

        sql_2 = ("SELECT count(distinct report_id) FROM xform_submissions_view3 "
               " WHERE has_errors = %s AND approved = %s AND date >= '%s' AND date <= '%s' %s")
        sql_2 = sql_2 % (False, False, lrp_todate[0], lrp_todate[1], extra_where_clause)
        cur.execute(sql_2)
        y = cur.fetchone()
        y = y[0] if y else 0

        sql = ("SELECT id FROM approve_summaries WHERE start_of_crp = '%s' AND end_of_crp = '%s'"
               " AND location = %s ")
        cur.execute(sql % (lrp[0], lrp[1], location.id))
        r = cur.fetchall()
        if r:
            sql = ("UPDATE approve_summaries SET reports_crp = %s, reports_lrp_uptodate = %s"
                   " WHERE location = %s AND start_of_crp = '%s' AND  end_of_crp = '%s'")

            cur.execute(sql % (x, y, location.id, lrp[0], lrp[1]))
            self.conn.commit()
        else:
            sql = ("INSERT INTO approve_summaries(location, reports_crp, "
                        "reports_lrp_uptodate, start_of_crp, end_of_crp) "
                        "VALUES(%s, %s, %s, '%s','%s')")
            cur.execute(sql % (location.id, x, y, lrp[0], lrp[1]))
            self.conn.commit()
