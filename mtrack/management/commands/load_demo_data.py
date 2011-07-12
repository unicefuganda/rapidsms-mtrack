from django.core.management.base import BaseCommand
from dimagi.utils.couch.database import get_db
from django.conf import settings
import sys

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        load_products()
        generate_codes_for_locations()

def load_products():
    from logistics.models import Product, ProductType
    product_types = {'m':'Malaria'
                     }
    products = [('yellow','Yellow ACT','m','box'), 
                ('blue','Blue ACT','m','box'), 
                ('brown','Brown ACT','m','box'), 
                ('green','Green ACT','m','box'), 
                ('other','Other ACT','m','box'), ]
    for key in product_types.keys():
        t, created = ProductType.objects.get_or_create(code=key, name=product_types[key])
    for prod in products:
        p, created = Product.objects.get_or_create(sms_code=prod[0], name=prod[1], 
                                                   type=ProductType.objects.get(code=prod[2]), 
                                                   units=prod[3])
        if created:
            print "Created product %(prod)s" % {'prod':p}

def generate_codes_for_locations():
    from rapidsms.contrib.locations.models import Location
    locs = Location.objects.all().order_by('name')
    for loc in locs:
        if loc.code is None or len(loc.code) == 0:
            loc.code = _generate_location_code(loc.name)
            loc.save()
            print "  %(name)s's code is %(code)s" % {'name':loc.name,
                                                     'code':loc.code}

def _generate_location_code(name):
    from rapidsms.contrib.locations.models import Location
    code = name.lower().replace(' ','_')
    code = code.replace('().&,','')
    postfix = ''
    existing = Location.objects.filter(code=code)
    if existing:
        count = 1
        postfix = str(count)
        try:
            while True:
                Location.objects.get(code=(code + postfix))
                count = count + 1
                postfix = str(count)
        except Location.DoesNotExist:
            pass
    return code + postfix

    
