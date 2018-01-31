import datetime
import re
from django.conf import settings
from mtrack.models import AnonymousReport
from rapidsms.models import Connection
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.models import Message
from uganda_common.utils import handle_dongle_sms
from urllib import urlopen
import requests


class App(AppBase):
    def handle(self, message):
        if handle_dongle_sms(message):
                    return True
        DHIS2_MESSAGE_PREFIXES = getattr(settings, 'DHIS2_MESSAGE_PREFIXES', ['mcd', 'pmtct'])
        if filter(message.text.strip().lower().startswith, DHIS2_MESSAGE_PREFIXES + [''])[0]:
            keyword = re.split('\W+', message.text.strip().lower())[0]
            keywordServerMappings = getattr(settings, 'KEYWORD_SERVER_MAPPINGS', {})

            if getattr(settings, 'USE_DISPATCHER', False):
                if keyword in getattr(settings, 'DISPATCHER_KEYWORDS', []):
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

            # XXX please note that source and destination must be configured in dispatcher2
            destinationSever = keywordServerMappings.get(keyword, '')
            if destinationSever:
                # this time we're to queue requests in dispatcher2 with a POST request like so;
                # http://localhost:9191/queue?source=mtrack&destination=y&raw_msg=msg&is_qparam=t&
                msg_date = message.date.date()
                year, week = self.get_reporting_week(msg_date)
                queueEndpoint = getattr(
                    settings, 'DISPATCHER2_QUEUE_ENDPOINT', 'http://localhost:9191/queue?')
                payload = 'message=%s&originator=%s' % (message.text, message.connection.identity)
                params = {
                    'source': 'mtrack', 'destination': destinationSever,
                    'raw_msg': message.text, 'msisdn': message.connection.identity,
                    'ctype': 'text', 'is_qparams': 't',
                    'year': year, 'week': week,
                    'username': getattr(settings, 'DISPATCHER2_USERNAME', ''),
                    'password': getattr(settings, 'DISPATCHER2_PASSWORD', '')}
                try:
                    requests.post(
                        queueEndpoint, data=payload, params=params, headers={
                            'Content-type': 'text/plain'})
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

    def get_reporting_week(self, date):
        """Given date, return the reporting week in the format 2016W01
        reports coming in this week are for previous one.
        """
        offset_from_last_sunday = date.weekday() + 1
        last_sunday = date - datetime.timedelta(days=offset_from_last_sunday)
        year, weeknum, _ = last_sunday.isocalendar()
        return (year, weeknum)
