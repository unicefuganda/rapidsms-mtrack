from django.db import models
from healthmodels.models.HealthFacility import HealthFacility
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message

ACTIONS = (
    ('Op', 'Open'),
    ('Ig', 'Ignore'),
    ('Na', 'No Action needed'),
    ('S', 'Stock out'),
    ('Ot', 'Other critical')
)
class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    message = models.ForeignKey(Message)
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location, null=True)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility, null=True)
    action = models.CharField(max_length=2, choices=ACTIONS, default='Op') #is this the right way??
    def __unicode__(self):
        return self.connection.identity

    class Meta:
        ordering = ['-date', 'action']

class AnonymousReportBatch(models.Model):
    connection = models.ForeignKey(Connection)
    anonymous_reports = models.ManyToManyField(AnonymousReport, null=True, default=None)
    date = models.DateTimeField(auto_now_add=True)
