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
            ar = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            ar.save()
            return True
        
#            if AnonymousReport.objects.filter(date__gte=d, connection=message.connection).exists() and not ScriptProgress.objects.filter(connection=message.connection).exists():
#                #get anonymous report objects that already passed the first script progress
#                ar = AnonymousReport.objects.filter(connection=message.connection).order_by('-date')[0] #get last report by user
#                ar.messages.add(message.db_message)
#                return True
#            else:
#                # just create a new anonymous report object for first time user
##                ar = AnonymousReport.objects.create(connection=message.connection)
#                # add message to it!!!
##                ar.messages.add(message.db_message)
##                return True
#            # send a thank you message via backend
#            #FIXTHIS is is this a okay?
##            message.connection.message(u"This report will be sent to your District. If this is an emergency, contact your nearest facility")
##            return True
#                if not AnonymousReport.objects.filter(date__gte=d, connection=message.connection).exists():
#
#                    ar = AnonymousReport.objects.create(connection=message.connection)
#                elif ScriptProgress.objects.filter(script__slug="anonymous_autoreg", connection=message.connection).exists():
#                    return False
#                else:
#                    ar = AnonymousReport.objects.filter(connection=message.connection).latest('date')
#                ar.messages.add(message.db_message)
#                return True