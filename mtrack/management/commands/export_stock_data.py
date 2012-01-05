from django.core.management.base import BaseCommand
from rapidsms_xforms.models import XFormSubmissionValue
from mtrack.utils import last_reporting_period
from rapidsms.contrib.locations.models import Location
from django.db.models import Q
from geoserver.models import BasicClassLayer
from django.conf import settings

class Command(BaseCommand):
    help = """Loads stock data into BasicClasssLayer for geoserver"""
    def handle(self, *args, **opts):
        districts = {}
        for pk in Location.objects.filter(type__name='district').values_list('name', flat=True):
            districts[pk] = ['nodata', 0]
        last_rp = last_reporting_period()
        rd = XFormSubmissionValue.objects.filter(submission__has_errors=False, \
                        submission__created__range=last_rp, \
                        value_int=0).filter(Q(attribute__slug__in=['act_sps', 'act_tps', 'act_eps', 'act_fps']))
        for l in rd:
            if l.submission.connection:
                district_pk = l.submission.connection.contact.reporting_location.get_ancestors().\
                filter(type__slug='district')[0].name
                districts[district_pk][0] = 'red'
                districts[district_pk][1] = districts[district_pk][1] + 1
        yl = XFormSubmissionValue.objects.filter(submission__has_errors=False, \
                        submission__created__range=last_rp).filter(
                                Q(attribute__slug='act_sps', value_int__lte=75, submission__connection__contact__healthproviderbase__facility__type__name='hcii') | \
                                Q(attribute__slug='act_tps', value_int__lte=30, submission__connection__contact__healthproviderbase__facility__type__name='hcii') | \
                                Q(attribute__slug='act_eps', value_int__lte=150, submission__connection__contact__healthproviderbase__facility__type__name='hcii') | \
                                Q(attribute__slug='act_fps', value_int__lte=150, submission__connection__contact__healthproviderbase__facility__type__name='hcii') | \
                                Q(attribute__slug='act_sps', value_int__lte=120, submission__connection__contact__healthproviderbase__facility__type__name='hciii') | \
                                Q(attribute__slug='act_tps', value_int__lte=45, submission__connection__contact__healthproviderbase__facility__type__name='hciii') | \
                                Q(attribute__slug='act_eps', value_int__lte=225, submission__connection__contact__healthproviderbase__facility__type__name='hciii') | \
                                Q(attribute__slug='act_fps', value_int__lte=300, submission__connection__contact__healthproviderbase__facility__type__name='hciii') | \
                                Q(attribute__slug='act_sps', value_int__lte=150, submission__connection__contact__healthproviderbase__facility__type__name='hciv') | \
                                Q(attribute__slug='act_tps', value_int__lte=45, submission__connection__contact__healthproviderbase__facility__type__name='hciv') | \
                                Q(attribute__slug='act_eps', value_int__lte=300, submission__connection__contact__healthproviderbase__facility__type__name='hciv') | \
                                Q(attribute__slug='act_fps', value_int__lte=375, submission__connection__contact__healthproviderbase__facility__type__name='hciv') | \
                                Q(attribute__slug='act_sps', value_int__lte=375, submission__connection__contact__healthproviderbase__facility__type__name='hospital') | \
                                Q(attribute__slug='act_tps', value_int__lte=120, submission__connection__contact__healthproviderbase__facility__type__name='hospital') | \
                                Q(attribute__slug='act_eps', value_int__lte=750, submission__connection__contact__healthproviderbase__facility__type__name='hospital') | \
                                Q(attribute__slug='act_fps', value_int__lte=750, submission__connection__contact__healthproviderbase__facility__type__name='hospital'))
        for y in yl:
            if y.submissin.connection:
                district_pk = y.submission.connection.contact.reporting_location.get_ancestors().\
                filter(type__slug='district')[0].name
                if districts[district_pk][0] <> 'red':
                    districts[district_pk][0] = 'yellow'
                    districts[district_pk][1] = districts[district_pk][1] + 1
        gr = XFormSubmissionValue.objects.filter(submission__has_errors=False, submission__created__range=last_rp).\
        filter(Q(attribute__slug__in=['act_sps', 'act_tps', 'act_eps', 'act_fps'])).distinct()
        for g in gr:
            if g.submission.connection:
                district_pk = g.submission.connection.contact.reporting_location.get_ancestors().\
                filter(type__slug='district')[0].name
                if districts[district_pk][0] not in ['red', 'yellow']:
                    districts[district_pk][0] = 'green'
                    districts[district_pk][1] = districts[district_pk][1] + 1
        for k, v in districts.items():
            d, _ = BasicClassLayer.objects.using('geoserver').get_or_create(district=k.upper(), \
                                                  deployment_id=getattr(settings, 'DEPLOYMENT_ID', 5), \
                                                  layer_id=0)
            d.style_class = v[0]
            d.description = "%s: %s occurrences" % (k.title(), v[1])
            d.save()
