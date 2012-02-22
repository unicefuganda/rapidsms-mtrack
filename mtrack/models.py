from django.db import models
from healthmodels.models.HealthFacility import HealthFacility
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message

ACTIONS = (
    ('Op', 'Open'),
    ('C', 'Claim'),
    ('Es', 'Escalate'),
    ('Cl', 'Close'),
    ('Ig', 'Ignore'),
    #('Na', 'No Action needed'),
    #('S', 'Stock out'),
    #('Ot', 'Other critical')
)
TOPICS = (
          ('Drug Theft', 'Drug Theft'),
          ('General Complaint', 'General Complaint'),
          ('General Inquiry', 'General Inquiry'),
          ('Good Service', 'Good Service'),
          ('Impersonation', 'Impersonation'),
          ('Other Critical', 'Other Critical'),
          ('Stock Out', 'Stock Out'),
          ('Unknown', 'Unknown'),
        )
ACTION_CENTERS = (
                  ('MOH', 'MOH'),
                  ('MU', 'MU'),
                  ('NMS', 'NMS'),
                  )
class AnonymousReport(models.Model):
    connection = models.ForeignKey(Connection)
    messages = models.ManyToManyField(Message, null=True, default=None)
    date = models.DateTimeField(auto_now_add=True)
    district = models.ForeignKey(Location, null=True)
    comments = models.TextField(null=True)
    health_facility = models.ForeignKey(HealthFacility, null=True)
    action = models.CharField(max_length=2, choices=ACTIONS, default='Op') #is this the right way??
    topic = models.CharField(max_length=32, default='Unknown', choices=TOPICS, null=True)
    action_center = models.CharField(max_length=32, default='', choices=ACTION_CENTERS, null=True)
    def __unicode__(self):
        return self.connection.identity

    class Meta:
        ordering = ['-date', 'action', 'topic']

#class AnonymousReportBatch(models.Model):
#    connection = models.ForeignKey(Connection)
#    anonymous_reports = models.ManyToManyField(AnonymousReport, null=True, default=None)
#    date = models.DateTimeField(auto_now_add=True)

import signals
