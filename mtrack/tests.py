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

    def testBasicSubmission(self):
        fake_incoming('act 1 2 3 4 5 6 7 8 9 10')
        self.assertEquals(XFormSubmission.objects.count(), 1)
        self.assertEquals(ProductReport.objects.count(), 10)

