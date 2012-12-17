from django.db import models
from healthmodels.models.HealthFacility import HealthFacility
from healthmodels.models.HealthProvider import HealthProvider
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission
from datetime import datetime

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
          ('Absenteeism', 'Absenteeism'),
          ('Drug Theft', 'Drug Theft'),
          ('Extortion', 'Extortion'),
          ('Fraud', 'Fraud'),
          ('General Complaint', 'General Complaint'),
          ('General Inquiry', 'General Inquiry'),
          ('Good Service', 'Good Service'),
          ('Ignore/Delete', 'Ignore/Delete'),
          ('Illegal schools', 'Illegal Schools'),
          ('Impersonation', 'Impersonation'),
          ('Malpractice', 'Malpractice'),
          ('Negligence', 'Negligence'),
          ('Other Critical', 'Other Critical'),
          ('Stock Out', 'Stock Out'),
          ('Unknown', 'Unknown'),
          ('Working hours of HCs', 'Working hours of HCs'),
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
    action_taken = models.TextField(null=True)
    def __unicode__(self):
        return self.connection.identity

    class Meta:
        ordering = ['-date', 'action', 'topic']

#class AnonymousReportBatch(models.Model):
#    connection = models.ForeignKey(Connection)
#    anonymous_reports = models.ManyToManyField(AnonymousReport, null=True, default=None)
#    date = models.DateTimeField(auto_now_add=True)

#Use this model to store extra info on submission esp those created from dashboard
class XFormSubmissionExtras(models.Model):
    submission = models.ForeignKey(XFormSubmission)
    is_late_report = models.BooleanField(default=False)
    submitted_by = models.TextField(null=True)
    cdate = models.DateTimeField(auto_now_add=True) #since we fake submission.created

    class Meta:
        db_table = 'rapidsms_xforms_xformsubmissionextras'

class Schedules(models.Model):
    created_by = models.TextField(default='')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    message_type = models.TextField()
    message = models.TextField()
    recur_frequency = models.IntegerField(default=0)
    recur_interval = models.TextField(default='none')
    recur_day = models.TextField(default='')
    recur_weeknumber = models.IntegerField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    class Meta:
        db_table = u'schedules'
    @property
    def extras(self):
        return self.scheduleextras

    def __unicode__(self):
        return self.message

class ScheduleExtras(models.Model):
    schedule = models.OneToOneField(Schedules)
    recipient_location_type = models.TextField(blank=True, null=True)
    recipient_location = models.TextField(blank=True, null=True)
    allowed_recipients = models.TextField(default='all')
    recipient_group_type = models.TextField(blank=True, null=True)
    group_ref = models.TextField(blank=True, null=True)
    missing_reports = models.TextField(default='')
    expected_reporter = models.TextField(default='HC')
    is_message_temp = models.BooleanField(default=False)
    message_args = models.TextField(default='')
    return_code = models.TextField(default='')
    cdate = models.DateTimeField(default=datetime.now())
    class Meta:
        db_table = u'schedule_extras'

    def __unicode__(self):
        return self.schedule.message

class HealthFacilityExtras(models.Model):
    health_facility = models.ForeignKey(HealthFacility, unique=True)
    total_reports = models.IntegerField(default=0)
    total_reporters = models.IntegerField(default=0)
    catchment_areas_list = models.TextField(default='')
    class Meta:
        db_table = 'healthmodels_healthfacilityextras'

#The Health Facilities view used to speed up the facility page
class Facilities(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    district = models.TextField()
    owner = models.TextField()
    authority = models.TextField()
    last_reporting_date = models.DateField(null=True)
    total_reports = models.IntegerField()
    total_reporters = models.IntegerField()
    catchment_areas = models.TextField()
    class Meta:
        managed = False
        db_table = 'facilities'

class HealthProviderExtras(models.Model):
    health_provider = models.ForeignKey(HealthProvider, unique=True)
    total_reports = models.IntegerField(default=0)
    district = models.TextField()
    class Meta:
        db_table = 'healthmodels_healthproviderextras'

#HealthProviders view that helps to load user's page faster
class Reporters(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    village_name = models.CharField(max_length=100)
    reporting_location = models.IntegerField(default=0)
    default_connection = models.TextField(default='')
    connections = models.TextField(default='')
    groups = models.TextField(default='')
    district = models.TextField(default='')
    total_reports = models.IntegerField(default=0)
    facility_id = models.IntegerField(null=True)
    facility = models.TextField(default='')
    last_reporting_date = models.DateField(null=True)
    loc_name = models.CharField(max_length=100, default='') # reporting_location name
    class Meta:
        managed = False
        db_table = 'reporters'

    def __unicode__(self):
        return self.name

class ApproveSummary(models.Model):
    location = models.IntegerField(null=True)
    reports_crp = models.IntegerField(default=0)
    reports_lrp_uptodate = models.IntegerField(default=0)
    start_of_crp = models.DateField(null=True)
    end_of_crp = models.DateField(null=True)
    class Meta:
        db_table = 'approve_summaries'

