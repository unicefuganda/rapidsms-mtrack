"""
Basic tests for mTrack
"""

from django.test import TestCase
from rapidsms.models import Contact
from rapidsms_xforms.models import *
from cvs.tests.util import fake_incoming
from mtrack.loader import mtrack_init_demo
from logistics.models import ProductReport

class MTrackTests(TestCase):
    def setUp(self):
        ProductReport.objects.all().delete()
        web_user = User.objects.create_user('test', 'test@test.com', 'passw0rd')
        self.contact = Contact.objects.create(name='mtrack_contact', user=web_user)

    def testNoFacility(self):
        sent = fake_incoming('act 1 2 3 4 5 6 7 8 9 10')
        self.assertEquals(sent.response, 'You are not associated with a facility. Please contact an administrator.')

    def testBasicSubmission(self):
        from healthmodels.models import HealthFacility, HealthProvider
        # associate contact with a facility
        hp = HealthProvider.objects.create(pk=self.contact.pk, name='vht reporter')
        hp.facility = HealthFacility.objects.all()[0]
        hp.save()
        sent = fake_incoming('act 1 2 3 4 5 6 7 8 9 10', self.contact.default_connection)
        self.assertEquals(sent.response, 'You reported 6 tablet pack dispensed 1,6 pack balance on hand 2,12 tabled pack dispensed 3,12 pack on hand 4,18 tabled pack dispensed 5,18 pack on hand 6,24 tablet pack dispensed 7, and 24 pack on hand 8.If there is an error,please resend.')
        self.assertEquals(XFormSubmission.objects.count(), 1)
        self.assertEquals(ProductReport.objects.count(), 10)

    def testAutoGenerateSupplyPoint(self):
        from healthmodels.models import HealthFacility, HealthFacilityType
        from rapidsms.contrib.locations.models import Location, Point
        #test create
        hf_type = HealthFacilityType.objects.all()[0]
        point = Point.objects.create(latitude="0.1", longitude="0.1")
        hf = HealthFacility(name='new facility', 
                            code='nf', 
                            type=hf_type, 
                            location=point)
        hf.save()
        transaction.commit()
        hf.catchment_areas.add(Location.objects.all()[1])
        hf.save()
        transaction.commit()
        self.assertNotEquals(hf, None)
        self.assertTrue('supply_point' in dir(hf))
        print type(hf.supply_point)
        self.assertEquals(hf.supply_point.name, hf.name)
        self.assertEquals(hf.supply_point.type.code, hf.type.slug)
        # test update
        hf_type2 = HealthFacilityType.objects.all()[1]
        hf.type = hf_type2
        hf.save()
        self.assertEquals(hf.supply_point.type.code, hf.type.slug)
        self.assertEquals(hf.supply_point.location.name,'Dangme East')
        hf.catchment_areas.add(Location.objects.all()[2])
        hf.save()
        self.assertEquals(hf.supply_point.location.name,'UG')



#class TestWithSelenium(TestCase):
#
#    @classmethod
#    def setUpClass(cls):
#        cls.selenium = webdriver.WebDriver()
#        super(TestWithSelenium, cls).setUpClass()