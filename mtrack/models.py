from mtrack import signals
from rapidsms_xforms.models import XFormField, XForm, XFormSubmission, dl_distance, xform_received
import datetime
from healthmodels.models import *
from healthmodels.models.HealthProvider import HealthProviderBase
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from poll.models import Poll
from eav.models import Attribute
from mtrack.utils import XFORMS
from script.signals import *
from script.models import *
from uganda_common.utils import parse_district_value
from script.utils.handling import find_closest_match, find_best_response
import itertools

from django.db import models
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from mtrack import signals


ACTIONS = (
    ('Op', 'Open'),
    ('Ig', 'Ignore'),
    ('Na', 'No Action needed'),
    ('S', 'Stock out'),
    ('Ot', 'Other critical')
)
class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    messages = models.ManyToManyField(Message)
    date = models.DateTimeField(auto_now_add=True, null=True)
    district = models.ForeignKey(Location, null=True)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility, null=True)
    action = models.CharField(max_length=2, choices=ACTIONS, default='Op') #is this the right way??
    def __unicode__(self):
        return self.connection.identity

def parse_facility(value):
    find_closest_match(value, HealthFacility, match_exact=False) #a little lenient

def parse_district(value):
    find_closest_match(value, Location, match_exact=True) #be a little strict


Poll.register_poll_type('facility', 'Health Facility', parse_facility, db_type=Attribute.TYPE_OBJECT,
                        view_template='mtrack/partials/response_facility_view.html',
                        edit_template='mtrack/partials/response_facility_edit.html',
                        report_columns=(('Original Text', 'text'), ('Health Facility', 'custom',),),
                        edit_form='mtrack.forms.FacilityResponseForm')

#Poll.register_poll_type('district', 'District', parse_district, db_type=Attribute.TYPE_OBJECT,
#                        view_template='mtrack/partials/response_district_view.html',
#                        edit_template='mtrack/partials/response_district_edit.html',
#                        report_columns=(('Original Text', 'text'), ('District', 'custom',),),
#                        edit_form='mtrack.forms.DistrictResponseForm')


def anonymous_autoreg(**kwargs):
    '''
    Anonymous autoreg script
    This method responds to a signal sent by the Script module on completion of the anonymous_autoreg script
    '''
    connection = kwargs['connection']
    progress = kwargs['sender']
    if not progress.script.slug == 'anonymous_autoreg':
        return
    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script

    district_poll = script.steps.get(poll__name='district_name_anonymous').poll
    health_facility_poll = script.steps.get(poll__name='health_facility_anonymous').poll

    # narrow down the health facility in catchment areas; reporter will now be able to report multiple times and in any location
    health_facility = find_best_response(session, health_facility_poll)
    district = find_best_response(session, district_poll)

    if district:
        district = find_closest_match(district, Location.objects.filter(type__name='district'))
        if district:
            all_sub_locations = district.get_descendants(include_self=True)
        else:
            all_sub_locations = Location.objects.all()
    else:
        all_sub_locations = Location.objects.all() # in case district is "failed"

    health_facility = find_closest_match(health_facility, HealthFacility.objects.filter(catchment_areas__in=all_sub_locations))
#TODO get district just in case a good district not found
#    if not district and health_facility:
#        district = health_facility.district

    anonymous_report = AnonymousReport.objects.filter(connection=connection).latest('date')
    anonymous_report.health_facility = health_facility
    anonymous_report.district = district
    anonymous_report.save()

script_progress_was_completed.connect(anonymous_autoreg, weak=False)
