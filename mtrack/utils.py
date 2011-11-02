import datetime
from django.contrib.auth.models import Group
from django.db.models import Count, Max, Min
from healthmodels.models import HealthFacility, HealthProvider
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XFormSubmission
from uganda_common.utils import get_location_for_user

def last_reporting_period():
    """
    Find a date range that spans from the most recent Wednesday (exactly a week ago if
    today is Wednesday) to the beginning of Thursday, one week prior
    """
    d = datetime.datetime.now()
    d = datetime.datetime(d.year, d.month, d.day)
    # find the past day with weekday() of 2, or if we're on a wednesday, go
    # to the last one.
    last_wednesday = d - datetime.timedelta((((5 + d.weekday()) % 7) or 7))
    return (last_wednesday - datetime.timedelta(7), d,)

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
    location = Location.tree.root_nodes()[0]
    if request.user:
        location = get_location_for_user(request.user) or location
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

def get_last_reporting_date(facility):
    facilities = HealthFacility.objects.filter(pk=facility.pk)
    staff = get_staff_for_facility(facilities)
    try:
        return XFormSubmission.objects.filter(message__connection__contact__in=staff)\
            .latest('created').created
    except XFormSubmission.DoesNotExist:
        return None

def get_facility_reports(facility):
    facilities = HealthFacility.objects.filter(pk=facility.pk)
    staff = get_staff_for_facility(facilities)
    return XFormSubmission.objects.filter(message__connection__contact__in=staff)\
        .filter(has_errors=False)\
        .count()

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

def non_reporting_facilities(location):
    return total_facilities(location) - reporting_facilities(location, date_range=last_reporting_period())

def non_reporting_vhts(location):
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


