from contact.models import Flag, MessageFlag
from django.conf import settings
from mtrack.models import AnonymousReport
from poll.models import Poll
from rapidsms.apps.base import AppBase
from rapidsms.models import Contact
from rapidsms_httprouter.models import Message
from script.models import Script, ScriptProgress
import rapidsms
import datetime
#sending messages??? outbound!

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            ar = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            ar.save()                    
            Message.objects.create(direction="O",
                                   text="Thank you for your report! Webaale kututegeezako!",
                                   status='Q',
                                   connection=message.connection,
                                   in_response_to=ar.message)            
            return True