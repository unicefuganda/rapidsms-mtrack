import sys
from django.db.transaction import TransactionManagementError
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
from django.db import transaction

class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args) < 1:
            print "Please specify file with reporters"
            return
        self.order = getattr(settings, 'REPORTER_EXCEL_FIELDS', {
                'name':0, 'phone':1,
                'district':3, 'role':2,
                'facility':5, 'facility_type':6,
                'village':4, 'village_type':7, #'pvht':8, 'village_name':9,
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
        print l
        return l

    def _clean_name(self,name):
        _name = name.strip().lower().split()
        return " ".join([n.capitalize() for n in _name])

    def _clean_phones(self,phone):
        return phone.strip().replace('.','').split('e')[0].replace('-', '').replace(" ","").split("/")

    def _clean_role(self,role):
        _role = role.strip().upper().split(',')
        print _role, role
        return Group.objects.filter(name__in =_role)

    def _clean_district(self,district):
        _district = district.strip()
        return find_closest_match(_district, Location.objects.filter(type='district'))

    def _clean_facility(self,facility,facility_type,district):
        _facility = HealthFacility.objects.filter(name__iexact="%s" % facility,
                        type__name=facility_type).filter(catchment_areas__in=district.get_descendants(include_self=True))
        if not _facility:
            _facility = HealthFacility.objects.filter(name__iexact=facility).filter(catchment_areas__in=district.get_descendants())
        return _facility[0] if _facility else None

    def _clean_village(self,village,village_type):
        return find_closest_match(village, Location.objects.filter(type__in=[village_type]))

    @transaction.commit_manually
    def _already_exists(self,phone):
        try:
            transaction.commit()
            Connection.objects.get(identity=phone)
            transaction.commit()
            return True
        except Connection.DoesNotExist: return False

    @transaction.commit_manually
    def load_reporters(self, data):
        n = 0
        transaction.commit()
        self.already_in = []
        for d in data:
            print 'Start'
            if not d[self.order['name']] or not d[self.order['phone']]:
                print "no name"
                continue
            print d
            _name = d[self.order['name']]
            name = self._clean_name(_name)
            _phone = '%s' % d[self.order['phone']]
            phones = self._clean_phones(_phone)
            print "=====================>", phones
            _district = d[self.order['district']]
            district = self._clean_district(_district)
            _role = d[self.order['role']]
            role = self._clean_role(_role)
            _fac = d[self.order['facility']]
            _fac_type = d[self.order['facility_type']].replace(' ','').lower()
            facility = self._clean_facility(_fac,_fac_type,district)
            transaction.commit()
            print facility
            _village = d[self.order['village']].strip()
            _village_type = d[self.order['village_type']].strip()
            village = self._clean_village(_village,_village_type)
            print name, phones, role

            transaction.commit()
            p = len(phones)-1
            while p >= 0:
                transaction.commit()
                exist = False
                try:
                    exist,d_ = self._has_different_facility(phones[p],facility)
                except TransactionManagementError:
                    pass
                transaction.commit()
                if exist:
                    print "User already attached to different facility ==> %s" %phones.pop(p)
                    self.already_in.append(d_)
                    #TODO Create excel with all these numbers
                p -= 1
#            transaction.commit()
#            continue

            if not phones:
                print "==>Phones list seems empty"
                transaction.commit()
                continue


            if not district:
                print "==>District not found (%s)"%_district
                transaction.commit()
                continue

            if not village:
                print "Village not found (%s - %s)"%(_village,_village_type)
                transaction.commit()

            if not facility:
                print "==============>Facility not found (%s - %s)"%(_fac,_fac_type)
                transaction.commit()
                continue

            phone,phone2 = phones[0],None
            if len(phones) > 1:
                phone2 = phones[1]

            msisdn, backend = assign_backend(phone)
            print msisdn, village

            if phone2:
                msisdn2, backend2 = assign_backend(phone2)

            try:
                connection = Connection.objects.get(identity=msisdn, backend=backend)
            except Connection.DoesNotExist:
                connection = Connection.objects.create(identity=msisdn, backend=backend)
                transaction.commit()
            except Connection.MultipleObjectsReturned:
                connection = Connection.objects.filter(identity=msisdn, backend=backend)[0]
            # a second phone number
            connection2 = None
            if phone2:
                try:
                    connection2 = Connection.objects.get(identity=msisdn2, backend=backend2)
                except Connection.DoesNotExist:
                    connection2 = Connection.objects.create(identity=msisdn2, backend=backend2)
                except Connection.MultipleObjectsReturned:
                    connection2 = Connection.objects.filter(identity=msisdn2, backend=backend2)[0]

            try:
                contact = connection.contact or HealthProvider.objects.get(name=_name, \
                                      reporting_location=(village or  district), \
                                      village=village, \
                                      village_name=_village)
            except Contact.DoesNotExist, Contact.MultipleObjectsReturned:
                contact = HealthProvider.objects.create()
                transaction.commit()



            connection.contact = contact
            connection.save()
            contact.name = name
            contact.facility = facility
            transaction.commit()
            if village:
                contact.reporting_location = village
                contact.village = village
                contact.village_name = None
            else:
                if district:
                    contact.reporting_location = district
                else:
                    contact.reporting_location = Location.tree.root_nodes()[0]
                contact.village_name = _village
                contact.village = None
            transaction.commit()

            contact.groups.clear()
            for r in role:
                contact.groups.add(r)

            if connection2:
                contact.connection_set.add(connection2)
            contact.save()
            transaction.commit()
            print contact.id
        print self.already_in
        transaction.commit()

    @transaction.commit_manually
    def _has_different_facility(self, phone,facility):
        transaction.commit()
        if self._already_exists(phone):
            transaction.commit()
            connection = Connection.objects.get(identity=phone)
            old_facility = connection.contact.healthproviderbase.facility if connection.contact else None
            transaction.commit()
            if connection.contact and connection.contact.is_active and old_facility and facility and old_facility != facility:
                d = {'phone':phone,'facility':old_facility,'new_facility':facility}
                transaction.commit()
                return True,d
        return False,None
