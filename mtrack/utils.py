import datetime
import xlwt
from alerts.models import Notification
from django.contrib.auth.models import Group
from django.db.models import Count, Max, Min
from healthmodels.models import HealthFacility, HealthProvider
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XFormSubmission
from uganda_common.utils import get_location_for_user
from django.db import connection
from ussd.models import Session
from mtrack.models import AnonymousReport, Facilities, ApproveSummary, XFormSubmissionExtras
from django.conf import settings
XFORMS = [
    'anonymous'  # anonymous report collecting
]

def last_reporting_period(period=1, weekday=getattr(settings, 'FIRSTDAY_OF_REPORTING_WEEK', 3), todate=False):
    """
    Find a date range that spans from the most recent Wednesday (exactly a week ago if
    today is Wednesday) to the beginning of Thursday, one week prior
    
    if period is specified, this wednesday can be exactly <period> weeks prior
    """
    d = datetime.datetime.now()
    d = datetime.datetime(d.year, d.month, d.day)
    # find the past day with weekday() of 3
    last_thursday = d - datetime.timedelta((((7 - weekday) + d.weekday()) % 7)) - datetime.timedelta((period - 1) * 7)
    return last_thursday - datetime.timedelta(7), datetime.datetime.now() if todate else last_thursday,

def last_reporting_period_number():
    first_monday = last_reporting_period(weekday=getattr(settings, 'FIRSTDAY_OF_REPORTING_WEEK', 3), period=1)[0]
    start_of_year = datetime.datetime(first_monday.year, 1, 1, 0, 0, 0)
    td = first_monday - start_of_year
    toret = int(td.days / 7)
    if start_of_year.weekday() != 0:
        toret += 1
    return toret
def current_reporting_week_number():
    # if Monday is first day of Week
    # return int(time.strftime('%W'))
    return last_reporting_period_number() + 1

def current_week_reporting_range():
    return last_reporting_period(period=0)

def total_facilities(location, count=True):
    """
    Find all health facilities whose catchment areas are somewhere inside
    the passed in location.
    
    Return their count if count is True, otherwise return the queryset
    """
    if not location:
        location = Location.tree.root_nodes()[0]
    locations = location.get_descendants(include_self=True).all()
    # facilities = HealthFacility.objects.filter(catchment_areas__in=locations).select_related().distinct()
    facilities = Facilities.objects.filter(id__in=HealthFacility.\
                                           objects.filter(catchment_areas__in=locations).\
                                           values_list('id', flat=True))
    if count:
        return facilities.count()

    return facilities

def get_facilites_for_view(request=None):
    location = get_location_for_user(getattr(request, 'user', None))
    return total_facilities(location, count=False)

def total_vhts(location, count=True):
    """
    Find all vhts whose reporting_location's are somewhere inside
    the passed in location.
    
    Return their count if count is True, otherwise return the queryset
    """
    locations = location.get_descendants(include_self=True).all()
    roles = Group.objects.filter(name__in=['VHT', 'PVHT'])
    vhts = HealthProvider.objects.filter(\
            reporting_location__in=locations, \
            active=True, \
            groups__in=roles).distinct()
    if count:
        return vhts.count()

    return vhts

def get_staff_for_facility(facilities):
    hc_role = Group.objects.get(name='HC')
    return HealthProvider.objects.filter(groups=hc_role, facility__in=facilities)

def get_latest_report(facility, keyword=None):
    facilities = HealthFacility.objects.filter(pk=facility.pk)
    staff = get_staff_for_facility(facilities)
    try:
        if keyword:
            return XFormSubmission.objects.filter(xform__keyword=keyword, message__connection__contact__in=staff)\
                .latest('created')
        else:
            return XFormSubmission.objects.filter(message__connection__contact__in=staff)\
                .latest('created')
    except XFormSubmission.DoesNotExist:
        return None

def get_last_reporting_date(facility):
    report = get_latest_report(facility)
    if report:
        return report.created

    return None

# def get_facility_reports(location, count=False, date_range=last_reporting_period(period=1, todate=True), approved=None):
#    facilities = total_facilities(location, count=False)
#    # print date_range
#    staff = get_staff_for_facility(facilities)
#    toret = XFormSubmission.objects.filter(\
#        connection__contact__in=staff, \
#        has_errors=False).order_by('-created')
#    if date_range:
#        toret = toret.filter(created__range=date_range)
#    if approved is not None:
#        toret = toret.filter(approved=approved)
#
#    if count:
#        # print toret.values('created', 'id')
#        return toret.count()
#    return toret

def get_facility_reports(location, count=False, date_range=last_reporting_period(period=1, todate=True), approved=None):
    facilities = total_facilities(location, count=False)
    toret = XFormSubmission.objects.filter(pk__in=XFormSubmissionExtras.objects.filter(\
            facility__in=facilities, reporter__groups__name='HC').\
            values_list('submission', flat=True), has_errors=False).order_by('-created')

    if date_range:
        toret = toret.filter(created__range=date_range)
    if approved is not None:
        toret = toret.filter(approved=approved)

    if count:
        # print toret.values('created', 'id')
        return toret.count()
    return toret

def get_facility_reports2(location, date_range=last_reporting_period(period=0), todate=False):
    toret = 0
    result = ApproveSummary.objects.filter(location=location.id,
                                  start_of_crp=date_range[0], end_of_crp=date_range[1])
    if result:
        return result[0].reports_lrp_uptodate if todate else result[0].reports_crp
    return toret

def get_ussd_facility_reports(location, count=False, date_range=last_reporting_period(todate=True), approved=None):
    toret = XFormSubmission.objects.exclude(connection__contact=None)\
        .exclude(connection__contact__healthproviderbase__healthprovider__facility=None)\
        .filter(\
        # connection__contact__in=staff, \
        pk__in=Session.objects.exclude(submissions=None).values_list('submissions', flat=True), \
        has_errors=False).order_by('-created')
    if date_range:
        toret = toret.filter(created__range=date_range)
    if approved is not None:
        toret = toret.filter(approved=approved)
    d = []
    for x in toret:
        if x.connection.contact.healthproviderbase.healthprovider.facility <> None:
            d.append(x.pk)
    toret = XFormSubmission.objects.filter(pk__in=d)
    if count:
        return toret.count()
    return toret

def get_all_facility_reports_for_view(request=None):
    location = get_location_for_user(request.user)
    return get_facility_reports(location, count=False, date_range=None)

def get_all_ussd_facility_reports_for_view(request=None):
    location = get_location_for_user(request.user)
    return get_ussd_facility_reports(location, count=False, date_range=None)

def get_facility_reports_for_view(request=None):
    location = get_location_for_user(request.user)
    # print location
    return get_facility_reports(location, count=False, approved=False)

def get_district_for_facility(hc):
    bounds = hc.catchment_areas.aggregate(Min('lft'), Max('rght'))
    l = Location.objects.filter(lft__lte=bounds['lft__min'], rght__gte=bounds['rght__max'], type__name='district')
    if l:
        return l[0]
    return None


def reporting_facilities(location, facilities=None, count=True, date_range=None):
    facilities = facilities or total_facilities(location, count=False)
    staff = get_staff_for_facility(facilities)
    reporting = XFormSubmission.objects.filter(connection__contact__in=staff)
    if date_range:
        reporting = reporting.filter(created__range=date_range)

    reporting = reporting\
            .filter(has_errors=False)\
            .values('message__connection__contact__healthproviderbase__facility')\
            .annotate(Count('pk'))\
            .values('message__connection__contact__healthproviderbase__facility', \
                    'pk__count')

    if count:
        return reporting.count()

    return reporting

def total_registered_facilities(location):
    all_facilities = total_facilities(location, count=False)
    all_staff = get_staff_for_facility(all_facilities)
    return len(all_staff.values_list('facility', flat=True).distinct())

def reporting_vhts(location):
    vhts = total_vhts(location, count=False)
    return XFormSubmission.objects.filter(message__connection__contact__in=vhts)\
        .filter(created__range=last_reporting_period(period=0))\
        .filter(has_errors=False)\
        .values('message__connection__contact')\
        .count()


def get_dashboard_messages(request=None):
    from cvs.utils import get_unsolicited_messages
    toret = get_unsolicited_messages(request=request)
    # dashboard messages don't have columns, so can't
    # be sorted the regular way in generic
    return toret.order_by('-date')


ALERTS_TOTAL = 0
ALERTS_ACTIONED = 1
ALERTS_CREATED = 2

def alerts_report(location, date_range, type=ALERTS_TOTAL):
    tnum = 3
    count_val = 'id'

    select = {
        'location_name':'T%d.name' % tnum,
        'location_id':'T%d.id' % tnum,
        'rght':'T%d.rght' % tnum,
        'lft':'T%d.lft' % tnum,
    }

    if type == ALERTS_ACTIONED:
        notifications = Notification.objects.filter(modified_on__range=date_range, escalated_on=None)
    elif type == ALERTS_CREATED:
        notifications = Notification.objects.filter(created_on__range=date_range, escalated_on=None)
    else:
        notifications = Notification.objects.filter(is_open=True, escalated_on=None)

    values = ['location_name', 'location_id', 'rght', 'lft']
    if location.get_children().count() > 1:
        location_children_where = 'T%d.id in %s' % (tnum, (str(tuple(location.get_children().values_list(\
                       'pk', flat=True)))))
    else:
        location_children_where = 'T%d.id = %d' % (tnum, location.get_children()[0].pk)
    return  notifications.values('originating_location__name').extra(
            tables=['locations_location'], where=[\
                   'T%d.lft <= locations_location.lft' % tnum, \
                   'T%d.rght >= locations_location.rght' % tnum, \
                   location_children_where]).extra(select=select).values(*values).annotate(value=Count(count_val))


def write_data_values_to_excel(data, rowx, sheet,cell_red_if_value):
    mark_cell_as_red_style = xlwt.easyxf("pattern: fore_colour red, pattern solid;")
    for row in data:
        rowx += 1
        for colx, value in enumerate(row):
            style = xlwt.easyxf()
            try:
                value = value.strftime("%d/%m/%Y")
            except:
                pass
            if value == cell_red_if_value:
                style = mark_cell_as_red_style
            sheet.write(rowx, colx, value, style)


def write_xls(sheet_name=None, headings=None, data=None, book=None,cell_red_if_value=None):
    sheet = book.add_sheet(sheet_name)
    rowx = 0
    if not headings:
        pass
    else:
        for colx, value in enumerate(headings):
            sheet.write(rowx, colx, value)
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(rowx + 1)
        sheet.set_remove_splits(True)

    write_data_values_to_excel(data, rowx, sheet,cell_red_if_value)

def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(zip(col_names, row))
        yield row_dict
    return

def get_facilities():
    return query_to_dicts("SELECT a.id, a.name||' '|| b.name  as name FROM"
                   " healthmodels_healthfacilitybase a, healthmodels_healthfacilitytypebase b "
                   " WHERE a.type_id = b.id ORDER BY a.name;")
def get_anonymous_reports(request=None):
    location = get_location_for_user(getattr(request, 'user', None))
    districts = Location.objects.filter(type__name='district').values_list('name', flat=True)
    if location.name in districts:
        return AnonymousReport.objects.filter(district=location).select_related('health_facility__type', 'district__name').order_by('-date')
    else:
        return AnonymousReport.objects.all().select_related('health_facility__type', 'district__name').order_by('-date')

