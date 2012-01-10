from django.core.management.base import BaseCommand
from mtrack import loader as mtrack_loader

class Command(BaseCommand):
    help = """1. Verify that facilities are linked to supply points
              2. all xform submissions have been processed for logistics.
              3. remove whitespace from location and facility codes
           """

    def handle(self, *args, **options):
        mtrack_loader.add_supply_points_to_facilities()
        mtrack_loader.process_xforms()
        mtrack_loader.remove_whitespace_from_codes()
