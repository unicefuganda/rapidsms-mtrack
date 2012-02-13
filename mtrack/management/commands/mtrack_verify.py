from django.core.management.base import BaseCommand
from logistics import loader as logi_loader
from mtrack import loader as mtrack_loader

class Command(BaseCommand):
    help = """1. Verify that facilities are linked to supply points
              2. all xform submissions have been processed for logistics.
              3. remove whitespace from location and facility codes
           """

    def handle(self, *args, **options):
        mtrack_loader.verify_supplypoint_type_names()
        logi_loader.generate_codes_for_locations()
        mtrack_loader.fix_codes_to_be_well_formed()
        mtrack_loader.add_supply_points_to_facilities()
        logi_loader.load_products_into_facilities()
        mtrack_loader.process_xforms()
