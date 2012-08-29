import sys
import xlrd
from django.core.management.base import BaseCommand
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection, Contact
from healthmodels.models.HealthFacility import HealthFacility
from healthmodels.models.HealthProvider import HealthProvider
from script.utils.handling import find_closest_match
from django.contrib.auth.models import Group
from uganda_common.utils import assign_backend
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        if (len(args) < 1):
            print "Please specify file with reporters"
            return
        self.order = getattr(settings, 'REPORTER_EXCEL_FIELDS', {
                'name':0, 'phone':1,
                'district':3, 'role':2,
                'facility':4, 'facility_type':5,
                'village':6, 'village_type':7, 'pvht':8, 'village_name':9,
                })


        l = self.read_all_reporters(args[0])

        self.load_reporters(l[1:])

    def read_all_reporters(self, filename):
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
        #print l
        return l

    def load_reporters(self, data):
        for d in data:
            if not d[self.order['name']] or not d[self.order['phone']]:
                continue
            print d
            _name = d[self.order['name']].strip()
            _phone = '%s' % d[self.order['phone']]
            print "=====================>",_phone
            _district = d[self.order['district']].strip()
            _role = d[self.order['role']].strip()
            _fac = d[self.order['facility']].strip()
            _fac_type = d[self.order['facility_type']]
            _village = d[self.order['village']].strip()
            _village_type = d[self.order['village_type']].strip()
            _pvht = d[self.order['pvht']]
            _phone = _phone.split('e')[0].split('.')[0].replace('-','')
            nums = _phone.split('/')
            _phone2 = ''
            _village_name = d[self.order['village_name']].capitalize()
            already_exists = False
            print nums
            if len(nums) > 1:
                _phone = nums[0]
                _phone2 = nums[1]

            print _name, _phone, _role
            district = find_closest_match(_district, Location.objects.filter(type='district'))
            #roles = list(Group.objects.filter(name__in=_role.split(',')))

            try:
                facility = find_closest_match(_fac, HealthFacility.objects.filter(type__name__in=[_fac_type]).\
                        filter(catchment_areas__in=district.get_descendants(include_self=True)))
            except HealthFacility.MultipleObjectsReturned:
                xx = HealthFacility.objects.filter(name=_fac,type__name=_fac_type).\
                        filter(catchment_areas__in=district.get_descendants(include_self=True))
                facility = xx[0] if xx else ''
            if not facility:
                xx = HealthFacility.objects.filter(name=_fac,type__name=_fac_type).\
                        filter(catchment_areas__in=district.get_descendants(include_self=True))
                facility = xx[0] if xx else ''
                if not facility:
                    continue
            village = None
            if _village:
                if district:
                    #village = find_closest_match(_village, district.get_descendants(include_self=True).filter(type__in=[_village_type]))
                    village = district.get_descendants(include_self=True).filter(name=_village, type__name=_village_type)[0]
                    print "***********",_village,"*********",village
                else:
                    village = find_closest_match(_village, Location.objects.filter(type__in=[_village_type]))
            if _name:
                _name = ' '.join([n.capitalize() for n in _name.lower().split()])
            msisdn, backend = assign_backend(_phone)
            print msisdn,village

            if _phone2:
                msisdn2, backend2 = assign_backend(_phone2)

            connection2 = None
            try:
                connection = Connection.objects.get(identity=msisdn, backend=backend)
            except Connection.DoesNotExist:
                connection = Connection.objects.create(identity=msisdn, backend=backend)
            except Connection.MultipleObjectsReturned:
                connection = Connection.objects.filter(identity=msisdn, backend=backend)[0]
            # a second phone number
            if _phone2:
                try:
                    connection2 = Connection.objects.get(identity=msisdn2, backend=backend2)
                except Connection.DoesNotExist:
                    connection2 = Connection.objects.create(identity=msisdn2, backend=backend2)
                except Connection.MultipleObectsReturned:
                    connection2 = Connection.objects.filter(identity=msisdn2, backend=backend2)[0]

            try:
                contact = connection.contact or HealthProvider.objects.get(name=_name, \
                                      reporting_location=(village or  district), \
                                      village=village, \
                                      village_name=_village)
                already_exists = True
            except Contact.DoesNotExist, Contact.MultipleObectsReturned:
                contact = HealthProvider.objects.create()

            connection.contact = contact
            connection.save()
            if _name:
                contact.name = _name

            if facility:
                contact.facility = facility

            if village:
                contact.reporting_location = village
                contact.village = village
                contact.village_name = _village_name or None
            else:
                if district:
                    contact.reporting_location = district
                else:
                    contact.reporting_location = Location.tree.root_nodes()[0]
                contact.village_name = _village_name or _village
                contact.village = None

            current_groups = list(contact.groups.all().values_list('name',flat=True))
            new_roles = list(set(_role.split(',') + current_groups))
            roles = list(Group.objects.filter(name__in=new_roles))

            contact.groups.clear()
            for role in roles:
                contact.groups.add(role)

            if connection2:
                contact.connection_set.add(connection2)
            contact.save()
