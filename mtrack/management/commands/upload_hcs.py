from django.core.management.base import BaseCommand
from django.db import transaction
import csv

class Command(BaseCommand):
    help = "Initialize static data health facilities"

    def create_location_safe(self, name, type, tree_parent):
        from rapidsms.contrib.locations.models import Location
        try:
            return Location.objects.get(name=name, type=type, tree_parent=tree_parent)
        except Location.DoesNotExist:
            l = Location.objects.create(name=name, type=type, tree_parent=tree_parent)
            if not l.pk:
                return Location.objects.get(name=name, type=type, tree_parent=tree_parent)
        except Location.MultipleObjectsReturned:
            return Location.objects.filter(name=name, type=type, tree_parent=tree_parent)[0]


    @transaction.commit_manually
    def handle(self, *args, **options):
        from rapidsms.contrib.locations.models import Location, LocationType, Point
        from healthmodels.models import HealthFacility, HealthFacilityType
        c = csv.reader(open('/home/david/Desktop/mtrac_hc.csv'), delimiter="\t")
        rows = []
        for row in c:
            rows.append(row)

        rows = rows[1:]

        uganda = Location.tree.root_nodes()[0]
        moh = HealthFacility.objects.get(name__icontains='ministry')
        t_district = LocationType.objects.get(name='district')
        t_county = LocationType.objects.get(name='county')
        t_subcounty = LocationType.objects.get(name='sub_county')
        t_parish = LocationType.objects.get(name='parish')
        t_hc = {
           'HC II':HealthFacilityType.objects.get(slug='hcii'),
           'HC III':HealthFacilityType.objects.get(slug='hciii'),
           'HC IV':HealthFacilityType.objects.get(slug='hciv'),
           'HOSPITAL':HealthFacilityType.objects.get(slug='hospital'),
           'DHO':HealthFacilityType.objects.get(slug='dho'),
        }
        hcs = []
        prev_subcounty = None
        prev_district = None
        move_to_subcounty = False
        dho = None
        rnum = 0
        for r in rows:
            try:
                if rnum % 100 == 0:
                    print "%d / %d" % (rnum, len(rows))
                    transaction.commit()
                rnum += 1
                district_name = ' '.join([d.capitalize() for d in r[0].lower().split()])
                county_name = ' '.join([d.capitalize() for d in r[1].lower().split()])
                subcounty_name = ' '.join([d.capitalize() for d in r[2].lower().split()])
                parish_name = ' '.join([d.capitalize() for d in r[3].lower().split()])
                district = self.create_location_safe(name=district_name, type=t_district, tree_parent=uganda)
                county = self.create_location_safe(name=county_name, type=t_county, tree_parent=district)
                subcounty = self.create_location_safe(name=subcounty_name, type=t_subcounty, tree_parent=county)
                parish = self.create_location_safe(name=parish_name, type=t_parish, tree_parent=subcounty)
                if prev_district is None or prev_district.pk != district.pk:
                    dho = HealthFacility.objects.create(name=district_name, type=t_hc['DHO'], report_to=moh)
                    prev_district = district
                    dho.catchment_areas.add(district)
                if prev_subcounty and prev_subcounty.pk != subcounty.pk:
                    if move_to_subcounty:
                        for h in hcs:
                            h.catchment_areas.clear()
                            h.catchment_areas.add(subcounty)
                    move_to_subcounty = False
                    hcs = []
                    prev_subcounty = subcounty
                if r[4].strip() and r[5].strip() and r[6].strip() and r[6].strip() == 'GOVT':
                    health_facility_name = ' '.join([d.capitalize() for d in r[4].lower().split()])
                    h = HealthFacility.objects.create(name=health_facility_name, type=t_hc[r[5].strip()], report_to=dho)
                    latlon = r[8] or r[9] or r[10] or None
                    if latlon:
                        lon, lat = latlon.split(',')
                        h.location, _ = Point.objects.get_or_create(latitude=lat, longitude=lon)
                    h.save()
                    h.catchment_areas.add(parish)
                    hcs.append(h)
                else:
                    move_to_subcounty = True
            except Exception, e:
                import pdb;pdb.set_trace()
                print "Bummer"
