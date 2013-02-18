from django.test import TestCase
from healthmodels.models.HealthFacility import HealthFacilityBase, HealthFacility
from logistics.models import SupplyPoint, SupplyPointType
from mock import *
from rapidsms_mtrack.mtrack.loader import add_supply_points_to_facilities
from rapidsms.contrib.locations.models import Location, Point


class TestMtrackInit(TestCase):


    @patch('rapidsms_mtrack.mtrack.loader.create_supply_point_from_facility')
    def test_loader_calls_save_without_cascade_update(self, mock_supply_point):
        facility = HealthFacility(name = "aa")
        facility.save(cascade_update=False)

        location = Location.objects.create(name='Greater Accra Region',code='gar')
        hctype, created = SupplyPointType.objects.get_or_create(code="clinic")

        some_point = SupplyPoint.objects.create(code='dedh', name='Dangme East District Hospital',location=location, active=True,type=hctype, supplied_by=None)

        mock_supply_point.return_value = some_point

        with patch.object(HealthFacility,'save') as mock_save:
            mock_save.return_value = True
            add_supply_points_to_facilities()
            mock_save.assert_called_once_with(cascade_update=False)


    @patch('rapidsms_mtrack.mtrack.loader.create_supply_point_from_facility')
    def test_loader_add_supply_points_to_new_facilities(self, mock_supply_point):
        facility = HealthFacility(name = "aa")
        facility.save(cascade_update=False)

        location = Location.objects.create(name='Greater Accra Region',code='gar')
        hctype, created = SupplyPointType.objects.get_or_create(code="clinic")

        some_point = SupplyPoint.objects.create(code='dedh', name='Dangme East District Hospital',location=location, active=True,type=hctype, supplied_by=None)

        mock_supply_point.return_value = some_point

        add_supply_points_to_facilities()

        facility = HealthFacility.objects.get(id = facility.id)

        self.failUnless(facility.supply_point)

