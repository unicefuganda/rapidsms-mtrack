import datetime
from django.conf import settings
from mtrack.models import AnonymousReport, AnonymousReportBatch
from rapidsms.models import Connection
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.models import Message

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            d = datetime.datetime.now() - datetime.timedelta(0,3600)
            anonymous_report = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            anonymous_report.save()

            # if anonymous report gets in and its time stamp is within the limit of 1hr
            # add this report to an existing AnonymousReportBatch object
            if AnonymousReportBatch.objects.filter(date__gte=d, connection__in=Connection.objects.filter(id=message.connection.id)).exists():
                # if batch exists and is  not older than 1 hour.
                try:
                    anonymous_report_batch = AnonymousReportBatch.objects.filter(date__gte=d, connection__in=Connection.objects.filter(id=message.connection.id))[0] # a little paranoid
                    anonymous_report_batch.anonymous_reports.add(anonymous_report)
                    anonymous_report_batch.save()
                    Message.objects.create(direction="O",
                        text = "Thank you for your consistent feedback about this health facility.",
                        status='Q',
                        connection=message.connection,
                        in_response_to=anonymous_report.message)

                except IndexError:
                    print "anonymous report batch doesn't exist."
                    pass
            else:
                arb = AnonymousReportBatch.objects.create(connection=message.connection)
                arb.anonymous_reports.add(anonymous_report)
                arb.save()
                Message.objects.create(direction="O",
                    text = "Thank you for your report, this report will be sent to relevant authorities. If this is an emergency, contact your nearest facility",
                    status='Q',
                    connection=message.connection,
                    in_response_to=anonymous_report.message)

        return True
