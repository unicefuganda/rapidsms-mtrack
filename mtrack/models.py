from mtrack import signals
from rapidsms_xforms.models import XFormField, XForm, XFormSubmission, dl_distance, xform_received
import re
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
    message = models.ForeignKey(Message)
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility)

    def __unicode__(self):
        return self.messages


def parse_facility_value(value):
    #TODO full refactor to uganda_commons
    #TODO thought: should health facility be a free-form name or is it strictly code-based
    #TODO use dl to get the right "name" of the health facility just in case it is left out.
    # get the levenstein distance in the spellings for the name
    try:
        #when the Health Facility name has been provided in text message
        name_of_health_facility = value.capitalize()
        for health_facility_name in [health_facility.name for health_facility in HealthFacility.objects.all()]:
            if dl_distance(name_of_health_facility,health_facility_name) <= 1:
                return health_facility_name
    except:
        raise ValidationError("We do not recognize this value: %s" % value)

def parse_facility(command,value):
    return parse_facility_value(value)

def parse_district(command,value):
    cap_value = value.strip().capitalize()
    # cost of this operation is nasty!
    for district_name in [district.name for district in Location.objects.all()]:
        if dl_distance(cap_value, district_name) <= 1:
            return district_name
    else:
        #TODO provide better Luganda translations
        raise ValidationError("Did not understand your location: %s. Tetutegedde ekiffyo kkyo: %s"%(value,value))
    

XFormField.register_field_type('district', 'District', parse_district, db_type=XFormField.TYPE_TEXT, xforms_type='string')

#TODO --> facility codes?
XFormField.register_field_type('facility', 'Health Facility', parse_facility, db_type=XFormField.TYPE_TEXT, xforms_type='string')


def xform_received_handler(sender, **kwargs):
    xform = kwargs['xform']
    submission = kwargs['submission']

    if submission.has_errors:
        return

    # TODO: check validity
    kwargs.setdefault('message', None)
    message = kwargs['message']
    try:
        message = message.db_message
        if not message:
            return
    except AttributeError:
        return
"""
    if xform.keyword == "anonymousreport" and submission.connection.contact:
        anonymous_report = AnonymousReport(connection=submission.connection,
            messages
        )
"""
    

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
    annonymous_report = AnonymousReport.objects.create(
        connection=connection,
        messages="hello+anonymous", #TODO "extract message from incoming texts"
        district=district,
        health_facility=healthfacility
    )
    annonymous_report.save()

script_progress_was_completed.connect(anonymous_autoreg, weak=False)