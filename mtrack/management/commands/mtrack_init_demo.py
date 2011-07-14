from django.core.management.base import BaseCommand
from logistics import loader as logi_loader
from mtrack import loader as mtrack_loader
#rom mtrack import utils as mtrack_utils

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        mtrack_loader.mtrack_init()
        logi_loader.init_test_location_and_supplypoints()
        logi_loader.init_test_product_and_stock()
        mtrack_loader.init_test_facilities(True)
        logi_loader.load_products_into_facilities(demo=True)
