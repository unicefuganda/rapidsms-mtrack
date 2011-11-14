from django.core.management.base import BaseCommand
from script.models import *
from poll.models import *

class Command(BaseCommand):
    def handle(self,**options):
        script = Script.objects.create(
            slug="mtrack_anonymous_autoreg",
            name="mtrack autoreg script"
        )
        user = User.objects.get(username="admin")
        script.sites.add(Site.objects.get_current())
        poll = Poll.create_location_based("contactdistrict","Thanks for reporting. What is the name of your District and Health Center? Webaale kututegeezako, tusaaba kumanya Linya lya District gyolimu ne linya lya health center yo","",[],user)
        script.steps.add(
            Script.objects.create(
                script=script,
                poll=poll,
                order=1,
                rule=ScriptStep.STRICT_MOVEON,
                start_offset=0,
                retry_offset=36000,
                numtries=1,
                giveup_offset=36000
            )
        )
        script.steps.add(ScriptStep.objects.create(
            script = script,
            message = "Thanks for filing your report. We will forward it to the District Health Team. If this is an emergency, you need to contact your nearest Health Facility directly.",
            order=2,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0
        ))