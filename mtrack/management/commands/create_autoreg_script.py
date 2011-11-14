from django.core.management.base import BaseCommand
from script.models import *

class Command(BaseCommand):
    def handle(self,**options):
        script = Script.objects.create(
                                       slug="mtrack_autoreg",
                                       name="mtrack autoregistration script")
        pass