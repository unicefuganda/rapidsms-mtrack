import datetime
from alerts.models import Notification
from django.contrib.auth.models import Group
from django.db.models import Count, Max, Min
from healthmodels.models import HealthFacility, HealthProvider
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XFormSubmission
from uganda_common.utils import get_location_for_user



XFORMS = [
    'anonymous' #anonymous report collecting
]

def last_reporting_period(period=1):
    """
    Find a date range that spans from the most recent Wednesday (exactly a week ago if
    today is Wednesday) to the beginning of Thursday, one week prior
    
    if period is specified, this wednesday can be exactly <period> weeks prior
    """
    d = datetime.datetime.now()
    d = datetime.datetime(d.year, d.month, d.day)
    # find the past day with weekday() of 3
    last_thursday = d - datetime.timedelta(((4 + d.weekday()) % 7)) - datetime.timedelta((period - 1) * 7)
    return (last_thursday - datetime.timedelta(7), last_thursday,)

def total_facilities(location, count=True):
    """
    Find all health facilities whose catchment areas are somewhere inside
    the passed in location.
    
    Return their count if count is True, otherwise return the queryset
    """
    if not location:
        location = Location.tree.root_nodes()[0]
    locations = location.get_descendants(include_self=True).all()
    facilities = HealthFacility.objects.filter(catchment_areas__in=locations).distinct()
    if count:
        return facilities.count()

    return facilities

def get_facilites_for_view(request=None):
    location = get_location_for_user(request.user)
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

def get_facility_reports(location, count=False, date_range=last_reporting_period()):
    facilities = total_facilities(location, count=False)
    staff = get_staff_for_facility(facilities)
    date_range = last_reporting_period()
    toret = XFormSubmission.objects.filter(\
        message__connection__contact__in=staff, \
        has_errors=False)
    if date_range:
        toret = toret.filter(created__range=date_range)

    if count:
        return toret.count()

    return toret

def get_all_facility_reports_for_view(request=None):
    location = get_location_for_user(request.user)
    return get_facility_reports(location, count=False, date_range=None)

def get_facility_reports_for_view(request=None):
    location = get_location_for_user(request.user)
    return get_facility_reports(location, count=False)

def reporting_facilities(location, facilities=None, count=True, date_range=None):
    facilities = facilities or total_facilities(location, count=False)
    staff = get_staff_for_facility(facilities)
    reporting = XFormSubmission.objects.filter(message__connection__contact__in=staff)
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
        .filter(created__range=last_reporting_period())\
        .filter(has_errors=False)\
        .values('message__connection__contact')\
        .count()

def get_district_for_facility(hc):
    bounds = hc.catchment_areas.aggregate(Min('lft'), Max('rght'))
    l = Location.objects.filter(lft__lte=bounds['lft__min'], rght__gte=bounds['rght__max'], type__name='district')
    if l.count():
        return l[0]

    return None

def get_dashboard_messages(request=None):
    from cvs.utils import get_unsolicited_messages
    toret = get_unsolicited_messages(request=request)
    # dashboard messages don't have columns, so can't 
    # be sorted the regular way in generic
    return toret.order_by('-date')



def get_anonymous_reports(request=None):
    toret = AnoymousReport.objects.filter(date_gte=datetime.now() - datetime.timedelta(hours=1))
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

