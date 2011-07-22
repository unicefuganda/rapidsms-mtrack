"""
Basic tests for mTrack
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.test.client import Client
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from rapidsms.messages.incoming import IncomingMessage
from rapidsms.models import Contact
from rapidsms_xforms.models import *
from rapidsms.models import Contact, Connection, Backend
from rapidsms_xforms.app import App
from rapidsms.messages.incoming import IncomingMessage
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from eav.models import Attribute
from cvs.tests.util import fake_incoming
from mtrack.loader import mtrack_init_demo
from logistics.models import ProductReport
from healthmodels.models import *
import datetime

from django.test import TestCase

class MTrackTests(TestCase):
    def setUp(self):
        mtrack_init_demo()
        ProductReport.objects.all().delete()
        self.contact = Contact.objects.all()[0]

    def testNoFacility(self):
        sent = fake_incoming('act 1 2 3 4 5 6 7 8 9 10')
        self.assertEquals(sent.response, 'You are not associated with a facility. Please contact an administrator.')
    
    def testBasicSubmission(self):
        from healthmodels.models import HealthFacility, HealthProvider
        # associate contact with a facility
        hp  = HealthProvider.objects.get(contact_ptr=self.contact.pk)
        hp.facility = HealthFacility.objects.all()[0]
        hp.save()
        sent = fake_incoming('act 1 2 3 4 5 6 7 8 9 10', self.contact.default_connection)
        self.assertEquals(sent.response, 'Thank you for reporting your stock on hand')
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
        hf.catchment_areas.add(Location.objects.all()[1])
        hf.save()
        self.assertNotEquals(hf.supply_point, None)
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
        self.assertEquals(hf.supply_point.location.name,'uganda')
        