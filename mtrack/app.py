import rapidsms, datetime
from django.conf import settings
from rapidsms.apps.base import AppBase
from contact.models import Flag, MessageFlag
from poll.models import Poll
from script.models import Script, ScriptProgress
from rapidsms.models import Contact
from mtrack.models import AnonymousReport
#sending messages??? outbound!
from rapidsms_httprouter.models import Message

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            d = datetime.datetime.now() - datetime.timedelta(hours=1)
            #snatch and compare every immediate SMS connections & timestamps to existing Anonymous Reports messages

            #skip the script
            #TODO compute better time intervals subject to environment variables like Yo!, MTN, Warid and others
            #>>> time_diff = datetime.datetime.now() - message.date
            # or
            #>>> msg_date = AnonymousReport.objects.all().order_by('-date')[0].messages.values()[0]['date']
            #>>> time_diff = datetime.datetime.now() - msg_date <-- using that filters for message times that are more recent
            # typically, a data reporter will have about 10 to 30 minutes moving from place to place at a hospital
            # another common use cases are immediate reports or rapid reporting which can be accurately predicted.

            # look for reports that have come in within the hour from the same person and that aren't in any script progress

            import pdb; pdb.set_trace()
            if AnonymousReport.objects.filter(date__gte=d, connection=message.connection).exists() and not ScriptProgress.objects.filter(connection=message.connection).exists():
                #get anonymous report objects that already passed the first script progress
                ar = AnonymousReport.objects.filter(connection=message.connection).order_by('-date')[0] #get last report by user
                ar.messages.add(message.db_message)
                return True
            else:
                # just create a new anonymous report object for first time user
                ar = AnonymousReport.objects.create(connection=message.connection)
                # add message to it!!!
                ar.messages.add(message.db_message)
                return True
            # send a thank you message via backend
            message.connection.message(u"This report will be sent to your District. If this is an emergency, contact your nearest facility")
            return True
#                if not AnonymousReport.objects.filter(date__gte=d, connection=message.connection).exists():
#
#                    ar = AnonymousReport.objects.create(connection=message.connection)
#                elif ScriptProgress.objects.filter(script__slug="anonymous_autoreg", connection=message.connection).exists():
#                    return False
#                else:
#                    ar = AnonymousReport.objects.filter(connection=message.connection).latest('date')
#                ar.messages.add(message.db_message)
#                return True