from django.core.management.base import BaseCommand
from mtrack import loader as mtrack_loader

class Command(BaseCommand):
    help = "Verify that facilities are linked to supply points, and all xform submissions have been processed for logistics."

    def handle(self, *args, **options):
        mtrack_loader.add_supply_points_to_facilities()
        mtrack_loader.process_xforms()
        mtrack_loader.remove_whitespace_from_codes()
