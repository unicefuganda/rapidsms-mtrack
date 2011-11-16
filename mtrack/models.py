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

class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    message = models.ManyToManyField(Message) #TODO; implications of not using FK here, view will just pick all anonymous reports
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility)

    def __unicode__(self):
        return self.connection

def parse_facility(value):
    find_closest_match(value, HealthFacility, match_exact=True)

def parse_district(value):
    find_closest_match(value,Location,match_exact=True) #be a little strict


Poll.register_poll_type('facility', 'Health Facility', parse_facility, db_type=Attribute.TYPE_OBJECT,
                        view_template='mtrack/partials/response_facility_view.html',
                        edit_template='mtrack/partials/response_facility_edit.html',
                        report_columns=(('Original Text', 'text'), ('Health Facility', 'custom',),),
                        edit_form='mtrack.forms.FacilityResponseForm')

Poll.register_poll_type('district', 'District', parse_district, db_type=Attribute.TYPE_OBJECT,
                        view_template='mtrack/partials/response_district_view.html',
                        edit_template='mtrack/partials/response_district_edit.html',
                        report_columns=(('Original Text', 'text'), ('District', 'custom',),),
                        edit_form='mtrack.forms.FacilityResponseForm')


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

    #TODO how do we represent that first message that gets sent to the helpline
    #report = script.steps.get(poll__name="anonymous_report").poll
    districtpoll = script.steps.get(poll__name='district_name_anonymous').poll
    healthfacilitypoll = script.steps.get(poll__name='health_facility_anonymous').poll

    district = find_best_response(session, districtpoll)
    healthfacility = find_best_response(session, healthfacilitypoll)
        
    contact = connection.contact
    connection.save() #save instance

    if district:
        contact.reporting_location = district
    else:
        #contact probably arleady in the system (usually we won't have to hit this point)
        contact.reporting_location = Location.tree.root_notes()[0]
    if healthfacility:
        facility = find_closest_match(healthfacility,HealthFacility.objects) #redundant
        if facility:
            contact.facility = facility
    contact.save()
    connection.save() # save it again; creepy stuff could happen
#
#       This has to go and preferably be part of a signal
#    annonymous_report = AnonymousReport.objects.create(
#        connection=connection,
#        messages="hello+anonymous", #TODO "extract message from incoming texts"
#        district=district,
#        health_facility=healthfacility
#    )
#    annonymous_report.save()

script_progress_was_completed.connect(anonymous_autoreg, weak=False)