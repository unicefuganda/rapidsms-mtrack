import datetime
from django.conf import settings
from mtrack.models import AnonymousReport
from rapidsms.models import Connection
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.models import Message

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            #anonymous_report = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            #anonymous_report.save()
            # if anonymous report gets in and its time stamp is within the limit of 1hr
            # add this report to an existing AnonymousReportBatch object
            end_epoch = datetime.datetime.now()
            epoch = end_epoch - datetime.timedelta(seconds=3600)
            if AnonymousReport.objects.filter(date__gte=epoch, connection__in=Connection.objects.filter(id=message.connection.id)).exists():
                try:
                    anonymous_report = AnonymousReport.objects.filter(date__gte=epoch, connection__in=Connection.objects.filter(id=message.connection.id))[0]
                    anonymous_report.messages.add(message.db_message)
                    anonymous_report.save()
                    Message.objects.create(direction="O",
                        text="Thank you for your consistent feedback about this health facility.",
                        status='Q',
                        connection=message.connection,
                        in_response_to=message.db_message)
                    return True
                except IndexError:
                    pass
            else:
                if message.connection.identity in getattr(settings, 'MODEM_NUMBERS', ['256777773260', '256752145316', '256711957281', '256790403038', '256701205129']):
                    Message.objects.create(direction="O", text=message.db_message,
                                           status='Q', connection=message.connection,
                                           in_response_to=message.db_message)
                    return True
                anonymous_report = AnonymousReport.objects.create(connection=message.connection)
                anonymous_report.messages.add(message.db_message)
                anonymous_report.save()
                Message.objects.create(direction="O",
                    text="Thank you for your report, this report will be sent to relevant authorities. If this is an emergency, contact your nearest facility",
                    status='Q',
                    connection=message.connection,
                    in_response_to=message.db_message)
                return True
