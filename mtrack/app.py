import rapidsms, datetime, re
from rapidsms.apps.base import AppBase
from contact.models import Flag, MessageFlag
from poll.models import Poll
from script.models import Script, ScriptProgress
from rapidsms.models import Contact

class App(AppBase):
    def handle(self, message):
        if not message.connection.contact and not ScriptProgress.objects.filter(script__slug="mtrac_anonymous_autoreg",connection=message.connection).exists():
            ScriptProgress.objects.create(script=Script.objects.get(slug="mtrac_anonymous_autoreg"),connection=message.connection)
            return True
        flags = Flag.objects.values_list('name',flat=True).distinct()
        one_template = r"(.*\b(%s)\b.*)"
        w_regex = []
        for word in flags:
            w_regex.append(one_template % str(word).strip())
        reg = re.compile(r"|".join(w_regex))
        match = reg.search(message.text)
        print match # test what's been matched
        if match:
            if hasattr(message,"db_message"):
                db_message = message.db_message
                try:
                    flag = Flag.objects.get(name=[d for d in list(match.groups()) if d][1])
                except (Flag.DoesNotExist,IndexError):
                    flag = None
                MessageFlag.objects.create(message=db_message,flag=flag)
        return False