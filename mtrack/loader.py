import os
import sys
from django.conf import settings
from rapidsms.contrib.locations.models import LocationType, Location, Point
from dimagi.utils.couch.database import get_db
from logistics.const import Reports
from logistics.models import SupplyPoint, SupplyPointType,\
    ProductReportType, ContactRole, Product, ProductType
from logistics.util import config

def load_cvs_xforms():
    from cvs.utils import init_xforms
    init_xforms()
    
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
                                           location=loc,  
                                           supply_point=sp)
        if log_to_console:
            print "  Supply point %s created" % hf.name
