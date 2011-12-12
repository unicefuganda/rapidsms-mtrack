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
            Message.objects.create(direction="O",
                                   text=u"Thank you for your report! Webaale kututegeezako!",
                                   status='Q',
                                   connection=message.connection,
                                   in_response_to=ar.message)
            ar.save()
            return True