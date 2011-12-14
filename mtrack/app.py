from django.conf import settings
from mtrack.models import AnonymousReport
from rapidsms.apps.base import AppBase
from rapidsms_httprouter.models import Message

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == getattr(settings, 'HOTLINE_BACKEND', 'console'):
            ar = AnonymousReport.objects.create(connection=message.connection, message=message.db_message)
            ar.save()                    
            Message.objects.create(direction="O",
                                   text = "Thank you for your report, this report will be sent to relevant authorities. If this is an emergency, contact your nearest facility",
                                   status='Q',
                                   connection=message.connection,
                                   in_response_to=ar.message)            
        return True  