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
            self.country = Location.objects.get(type__name='country')
        except Location.MultipleObjectsReturned:
            print "There should only be one 'country' specified."
            exit()
        self.regions = self.create_regions()
        self.assign_districts(args[0])
    
    def create_regions(self):
        region_type, created = LocationType.objects.get_or_create(name='region', slug='region')
        regions = {}
        for region in region_names:
            code = region.lower()
            reg, created = Location.objects.get_or_create(code=code)
            if created:
                reg.name = region
                reg.type = region_type
                reg.parent = self.country
                reg.save()
            regions[code] = reg
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
            district.tree_parent = self.regions[region_code]
            district.save()
        print "%s districts assigned." % districts_assigned
        print "%s lines had errors." % error_count
        

