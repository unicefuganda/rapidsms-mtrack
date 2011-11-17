import rapidsms, datetime
from rapidsms.apps.base import AppBase
from contact.models import Flag, MessageFlag
from poll.models import Poll
from script.models import Script, ScriptProgress
from rapidsms.models import Contact
from mtrack.models import AnonymousReport

class App(AppBase):
    def handle(self, message):
        if message.connection.backend.name == 'yo8200':
            d = datetime.datetime.now() - datetime.timedelta(hours=1)
            if not AnonymousReport.objects.filter(date__gte=d, connection=message.connection).exists():
                ScriptProgress.objects.create(script=Script.objects.get(slug="mtrack_anonymous_autoreg"), connection=message.connection)
                ar = AnonymousReport.objects.create(connection=message.connection)
            elif ScriptProgress.objects.filter(script__slug="mtrac_anonymous_autoreg", connection=message.connection).exists():
                return False
            else:
                ar = AnonymousReport.objects.filter(connection=message.connection).latest('date')
            ar.messages.add(message.db_message)
            return True
