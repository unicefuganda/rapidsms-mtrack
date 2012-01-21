import csv
import sys
from django.core.management.base import BaseCommand
from mtrack import loader as mtrack_loader
from rapidsms.contrib.locations.models import Location, LocationType

region_names = ('Northern', 'Eastern', 'Central', 'Western')

class Command(BaseCommand):
    help = "Create regions and assign districts accordingly"

    def handle(self, *args, **options):
        if len(args) != 1:
            print "Please specify the csv file from where to load district-region mappings"
            print "It should be of the format 'district, region', with one tuple per line"
            return
        try:
            country = LocationType.objects.get(name='country')
        except LocationType.DoesNotExist:
            country = LocationType(name='country', slug='country')
            country.save()
        try:
            district = LocationType.objects.get(name='district')
        except LocationType.DoesNotExist:
            district = LocationType(name='district', slug='district')
            district.save()
        try:
            self.country = Location.objects.get(type__name='country')
        except Location.MultipleObjectsReturned:
            print "There should only be one 'country' specified."
            exit()
        except Location.DoesNotExist:
            self.country = Location(type=country, name='Uganda', code='uganda')
            self.country.save()
        self.regions = self.create_regions()
        self.assign_districts(args[0])
    
    def create_regions(self):
        region_type, created = LocationType.objects.get_or_create(name='region', slug='region')
        regions = {}
        for region in region_names:
            code = region.lower()
            reg, created = Location.objects.get_or_create(code=code)
            if not created:
                print 'Modifying location %s %s to be children of "uganda"' % (reg.name, reg.pk)
            reg.name = region
            reg.type = region_type
            reg.save()
            # TODO: is this right???
            reg.move_to(self.country, 'last-child')
            reg.save()
            regions[code] = reg
        # verify that new regions have been added to the country
        country = Location.objects.get(pk=self.country.pk)
        country_children_pks = [c.pk for c in country.get_children()]
        for x in regions:
            assert regions[x].pk in country_children_pks
        return regions

    def assign_districts(self, filename):
        district_type = LocationType.objects.get(slug='district')
        reader = csv.reader(open(filename, 'rb'), delimiter=',', quotechar='"')
        line_number = -1
        error_count = 0
        districts_assigned = 0
        for row in reader:
            line_number = line_number + 1
            region_code = row[1].lower()
            if region_code not in self.regions:
                print "  ERROR: region code %s on line %s not recognized" % (region_code, line_number)
                error_count = error_count + 1
                continue
            district_code = row[0].lower()
            try:
                district = Location.objects.get(name__iexact=district_code, type=district_type)
            except Location.DoesNotExist:
                print "  ERROR: district code %s on line %s not recognized" % (district_code, line_number)
                error_count = error_count + 1
                continue
            if district.tree_parent != self.country:
                print "  District %s is already set to have %s as its parent" % (district_code, self.country)
                continue
            # TODO: is this right???
            region = Location.objects.get(pk=self.regions[region_code].pk)
            region_children_count = region.get_children().count()
            district.move_to(region, 'last-child')
            district.save()
            
            # verify that new districts have been added to the region
            region = Location.objects.get(pk=self.regions[region_code].pk)
            new_region_children_count = region.get_children().count()
            assert new_region_children_count == region_children_count + 1
            assert district.get_ancestors(ascending=True)[0] == region
        print "%s districts assigned." % districts_assigned
        print "%s lines had errors." % error_count
        

