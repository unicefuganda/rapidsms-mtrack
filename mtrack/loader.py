"""
Load utils: good for setting up a demo environment, 
first setup of production environment, and automated testing
"""

import os
import sys
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from logistics.const import Reports
from logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.util import config

def mtrack_init():
    from logistics import loader as logi_loader
    from cvs.utils import init_xforms as cvs_init_xforms
    logi_loader.load_products()
    logi_loader.init_reports(True)
    logi_loader.init_roles_and_responsibilities(True)
    logi_loader.init_supply_point_types()
    logi_loader.generate_codes_for_locations()
    init_admin()
    cvs_init_xforms()  
    # act xform initiailization is already handled in cvs
    # mtrack_loader.init_xforms()  
    add_supply_points_to_facilities()

def mtrack_init_demo():
    from logistics import loader as logi_loader
    mtrack_init()
    logi_loader.init_test_location_and_supplypoints()
    logi_loader.init_test_product_and_stock()
    init_test_facilities(True)
    logi_loader.load_products_into_facilities(demo=True)

def init_admin():
    from django.contrib.auth.models import User
    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        admin = User.objects.create_user(username='admin', 
                                 email='test@doesntmatter.com', 
                                 password='password')
        admin.is_staff=True
        admin.is_superuser=True
        admin.save()

def  _init_facility_types():
    from healthmodels.models import HealthFacilityType
    from logistics.util import config
    for code, name in config.SupplyPointCodes.ALL.items():
        type_ = HealthFacilityType.objects.get_or_create(slug=code)[0]
        if type_.name != name:
            type_.name = name
            type_.save()

def init_test_facilities(log_to_console=False):
    # this assumes all supply point codes will be the same as facility codes
    # and that all supply points are clinics
    from healthmodels.models import HealthFacility, HealthFacilityType
    from logistics.models import SupplyPoint, SupplyPointType
    _init_facility_types()
    loc = Location.objects.all()[0]
    sp_type = SupplyPointType.objects.get(code=config.SupplyPointCodes.CLINIC)
    try:
        sp = SupplyPoint.objects.get(code='tf')
    except SupplyPoint.DoesNotExist:
        sp, created = SupplyPoint.objects.get_or_create(code='tf', type=sp_type, 
                                                        location=loc)
    sp.name = 'test supply point'
    sp.active = True
    sp.save()
    try:
        hf = HealthFacility.objects.get(code='tf')
    except HealthFacility.DoesNotExist:
        hf_type = HealthFacilityType.objects.all()[0]
        hf = HealthFacility.objects.create(name='test facility', 
                                           code='tf', 
                                           type=hf_type,   
                                           supply_point=sp)
        if log_to_console:
            print "  Supply point %s created" % hf.name

def add_supply_points_to_facilities(log_to_console=False):
    from healthmodels.models import HealthFacility, HealthFacilityType
    from logistics.models import SupplyPoint, SupplyPointType
    from rapidsms.contrib.locations.models import Location
    facilities = HealthFacility.objects.all().order_by('name')
    for f in facilities:
        if f.supply_point is None:
            sp = SupplyPoint(code=f.code, 
                             name=f.name, 
                             type=SupplyPointType.objects.get(code=f.type.slug), 
                             active=True)
            if f.location is None:
                l = Location(name=f.name)
                l.save()
                sp.location = l 
                f.location = l
            else:
                sp.location = f.location
            sp.save()
            f.supply_point = sp
            f.save()
            if log_to_console:
                print "  %s supply point created" % f.name

def init_xforms():
    from cvs.utils import init_xforms_from_tuples
    XFORMS = (
        ('', 'act', ' ', 'ACT stock report','Report levels of ACT stocks',),
    )

    XFORM_FIELDS = {
        'act':[
             ('yellow', 'int', 'Yellow ACT', True),
             ('blue', 'int', 'Blue ACT', True),
             ('brown', 'int', 'Brown ACT', True),
             ('green', 'int', 'Green ACT', True),
             ('other', 'int', 'Other ACT', True),
         ],
    }
    
    init_xforms_from_tuples(XFORMS, XFORM_FIELDS)
