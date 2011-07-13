from django.core.management.base import BaseCommand
from logistics import loader as logi_loader
from mtrack import loader as mtrack_loader
#rom mtrack import utils as mtrack_utils

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        logi_loader.load_products()
        logi_loader.generate_codes_for_locations()
        logi_loader.init_reports(True)
        logi_loader.init_roles(True)
        logi_loader.init_test_location_and_supplypoints()
        logi_loader.init_test_product_and_stock()
        mtrack_loader.init_test_facilities(True)
        mtrack_loader.load_cvs_xforms()  
        # act xform initiailization is already handled in cvs
        # mtrack_loader.init_xforms()  
        mtrack_loader.add_supply_points_to_facilities()
