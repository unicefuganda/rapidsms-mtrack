import datetime
from django.conf import settings
from mtrack.models import AnonymousReport
from rapidsms.models import Connection
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.models import Message
from uganda_common.utils import handle_dongle_sms
from urllib import urlopen


class App(AppBase):
    def handle(self, message):
        if handle_dongle_sms(message):
                    return True
        DHIS2_MESSAGE_PREFIXES = getattr(settings, 'DHIS2_MESSAGE_PREFIXES', ['mcd', 'pmtct'])
        if filter(message.text.strip().lower().startswith, DHIS2_MESSAGE_PREFIXES + [''])[0]:
            url = getattr(settings, 'DHIS2_SMSINPUT_URL', 'http://localhost:9090/dhis2_smsinput?')
            if url.find('?') < 0:
                c = '?'
            else:
                c = ''
            url = url + c + 'message=%s&originator=%s' % (message.text, message.connection.identity)
            try:
                urlopen(url)
            except:
                pass
            return True
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            # anonymous_report = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            # anonymous_report.save()
            # if anonymous report gets in and its time stamp is within the limit of 1hr
            # add this report to an existing AnonymousReportBatch object
            end_epoch = datetime.datetime.now()
            epoch = end_epoch - datetime.timedelta(seconds=3600 * 24 * 3)
            if AnonymousReport.objects.filter(date__gte=epoch, connection__in=Connection.objects.filter(id=message.connection.id)).exists():
                try:
                    anonymous_report = AnonymousReport.objects.filter(date__gte=epoch, connection__in=Connection.objects.filter(id=message.connection.id))[0]
                    anonymous_report.messages.add(message.db_message)
                    anonymous_report.save()
                    Message.objects.create(
                        direction="O",
                        text="Thank you for your consistent feedback about this health facility.",
                        status='Q',
                        connection=message.connection,
                        in_response_to=message.db_message)
                    return True
                except IndexError:
                    pass
            else:
                anonymous_report = AnonymousReport.objects.create(connection=message.connection)
                anonymous_report.messages.add(message.db_message)
                anonymous_report.save()
                Message.objects.create(
                    direction="O",
                    text=getattr(
                        settings, 'HOTLINE_DEFAULT_RESPONSE',
                        ("Your report has been sent to relevant authorities. You can also call Ministry "
                            "of Health on 0800100066 (toll free) for further help and inquires. "
                            "If this is an emergency contact your nearest facility")),
                    status='Q',
                    connection=message.connection,
                    in_response_to=message.db_message)
                return True
