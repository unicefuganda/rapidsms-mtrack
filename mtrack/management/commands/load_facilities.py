import sys
import xlrd
from django.core.management.base import BaseCommand
from rapidsms.contrib.locations.models import Location, LocationType, Point
from healthmodels.models.HealthFacility import HealthFacility, HealthFacilityBase, HealthFacilityType
from logistics.models import SupplyPoint
from script.utils.handling import find_closest_match
from random import choice

class Command(BaseCommand):
    """Loads Health Facilities from file"""
    def handle(self, *args, **options):
        if (len(args) < 1):
            print "Please specify file with facilities"
            return
        self.order = {
                 'district': 0,
                 'county': 1,
                 'sub_county': 2,
                 'parish': 3,
                 'facility': 4,
                 'facility_type': 5,
                 'owner': 6,
                 'authority': 7,
                 'point': 8,
                 }
        l = self.read_all_facilities(args[0])

        print l[:3]
        self.load_facilities(l[1:])
    def read_all_facilities(self, filename):
        wb = xlrd.open_workbook(filename)
        l = []
        #lets stick to sheet one only
        #num_of_sheets = wb.nsheets
        num_of_sheets = 1
        for i in xrange(num_of_sheets):
            sh = wb.sheet_by_index(i)
            for rownum in range(sh.nrows):
                vals = sh.row_values(rownum)
                l.append(vals)
        return l

    def gen_code(self):
        chars = '1234567890_QWERTYUOPASDFGHJKLZXCVBNM'
        code = u"gen" + u"".join([choice(chars) \
                                  for i in range(10)]).lower()
        return code
    def flatten(self, mylist):
        return [item for sublist in mylist for item in sublist]
    def does_facility_exist(self, facility_data):
        district = Location.objects.filter(name=facility_data['district'], type='district')
        if district:
            district = district[0]
        else:
            return False,None
        county = district.get_descendants().filter(name__icontains=facility_data['county'], type='county').values_list('id', flat=True)
        sub_county = district.get_descendants().filter(name__icontains=facility_data['sub_county'], type='sub_county').values_list('id', flat=True)
        parish = district.get_descendants().filter(name__icontains=facility_data['parish'], type='parish').values_list('id', flat=True)
        f = HealthFacility.objects.filter(name__icontains=facility_data['facility'], type__name=facility_data['facility_type']).\
            filter(catchment_areas__in=list(district.get_descendants(include_self=True).values_list('id', flat=True)))
        if f:
            return True, f[0]
        return False, None



    def create_new_facility(self, facility_data):
        print "Creating new facility %(facility)s %(facility_type)s in %(district)s"%facility_data
        district = Location.objects.filter(name=facility_data['district'], type='district')
        if district:
            district = district[0]
        else:
            return False
        county = district.get_descendants().filter(name__icontains=facility_data['county'], type='county')
        sub_county = district.get_descendants().filter(name__icontains=facility_data['sub_county'], type='sub_county')
        parish = district.get_descendants().filter(name__icontains=facility_data['parish'], type='parish')
        if parish.count() > 0:
            c_as = parish[0]
        elif sub_county.count() > 0:
            c_as = sub_county[0]
        elif county.count() > 0:
            c_as = county[0]
        else:
            c_as = district
        # create facility
        _point = facility_data['point'].strip().split(',')
        facility_point = None
        if len(_point) > 1:
            try:
                latitude = float(_point[0])
                longitude = float(_point[1])
                facility_point, _ = Point.objects.get_or_create(latitude=latitude, longitude=longitude)
            except:
                pass

        ftype = HealthFacilityType.objects.get(name=facility_data['facility_type'])
        facility_code = self.gen_code()
        if facility_point:
            f = HealthFacility.objects.create(name=facility_data['facility'], type=ftype,
                    location=facility_point, code=facility_code)
        else:
            f = HealthFacility.objects.get(name=facility_data['facility'], type=ftype, code=facility_code)


        f.district = district.name
        f.owner = facility_data['owner']
        f.authority = facility_data['authority']
        f.catchment_areas.clear()
        f.catchment_areas.add(c_as)
        #clean up
#        sup_point = SupplyPoint.objects.filter(code=facility_code, type=ftype.name)
#        if (len(sup_point) > 0):
#            print "We have a supply point"
#            sup_point = sup_point[0]
#            f.supply_point = sup_point
#
        f.save()
        print f


    def load_facilities(self, data):
        for d in data:
            if not d[self.order['facility']]:
                continue
            _district = d[self.order['district']].capitalize()
            _county = d[self.order['county']].capitalize()
            _subcounty = d[self.order['sub_county']].capitalize()
            _parish = d[self.order['parish']].capitalize()
            _facility = d[self.order['facility']]
            _facility = ' '.join([i.capitalize() for i in _facility.split()])
            _facility_type = d[self.order['facility_type']].replace(' ', '').lower()
            _owner = d[self.order['owner']]
            _auth = d[self.order['authority']]
            _point = d[self.order['point']]

            facility_data = {'district': _district, 'county': _county, 'sub_county': _subcounty,
                    'parish': _parish, 'facility': _facility, 'facility_type': _facility_type,
                    'point': _point, 'owner': _owner, 'authority': _auth}
            facility_exists, facility = self.does_facility_exist(facility_data)
            if facility_exists:
                print "Oooops Facility %s %s exists"%(facility_data['facility'], facility_data['facility_type'])
                facility.owner = facility_data['owner']
                facility.authority = facility_data['authority']
                facility.save()
            else:
                #we've got a new facility
                self.create_new_facility(facility_data)



