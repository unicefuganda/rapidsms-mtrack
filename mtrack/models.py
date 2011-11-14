from django.db import models
from mtrack import signals

# Create your models here.
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from script.signals import script_progress_was_completed

class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    messages = models.ManyToManyField(Message)
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility)

    def __unicode__(self):
        return self.messages

def create_anonymous_report():
    pass

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
    districtpoll = script.steps.get(poll__name='anonymous_district').poll
    healthfacilitypoll = script.steps.get(poll__name='anonymous_healthfacility').poll


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
