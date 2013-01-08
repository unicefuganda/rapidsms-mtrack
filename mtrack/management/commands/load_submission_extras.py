from django.core.management.base import BaseCommand
from rapidsms_xforms.models import XFormSubmission
from mtrack.models import XFormSubmissionExtras

class Command(BaseCommand):
    help = """Used to populate the XFormSubmissionsExtras model with values
    (facility and reporter) when running the 0009_auto__add_field_xformsubmissionextras_facility.py migration
    """

    def handle(self, *args, **options):
        submissions = XFormSubmission.objects.all()
        for sub in submissions:
            if sub.connection:
                if sub.connection.contact:
                    hp = sub.connection.contact.healthproviderbase
                    facility = sub.connection.contact.healthproviderbase.facility
                    sdate = sub.created
                    extras = XFormSubmissionExtras.objects.filter(submission=sub.id)
                    if not extras:
                        s = XFormSubmissionExtras.objects.create(submission_id=sub.id, facility=facility,reporter=hp)
                        print "submission=>",sub.id,"  facility=>",facility, "  reporter=>", hp
                        s.cdate=sdate
                        s.save()
