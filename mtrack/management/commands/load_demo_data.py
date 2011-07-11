from django.core.management.base import BaseCommand
from dimagi.utils.couch.database import get_db
from django.conf import settings
import sys

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        load_products()

def load_products():
    from logistics.models import Product, ProductType
    malaria, created = ProductType.objects.get_or_create(code='m', name="Malaria")
    yellow, created = Product.objects.get_or_create(sms_code='yellow', name='Yellow ACT',
                                                    type=malaria, units='box')
    
    
