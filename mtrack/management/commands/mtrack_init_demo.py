from django.core.management.base import BaseCommand
from logistics import loader as logi_loader
from mtrack import loader as mtrack_loader
#rom mtrack import utils as mtrack_utils

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        mtrack_loader.mtrack_init_demo()
