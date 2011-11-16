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

def parse_facility(command,value):
    find_closest_match(value, HealthFacility, match_exact=True)

def parse_district(command,value):
    find_closest_match(value,Location,match_exact=True) #be a little strict


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
