from alerts import Alert
from alerts.models import Notification, NotificationComment, NotificationType
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from datetime import datetime, timedelta
from uganda_common.utils import total_attribute_value
from django.contrib.auth.models import User
from rapidsms_xforms.models import XFormSubmission, XFormSubmissionValue
from healthmodels.models.HealthProvider import HealthProvider
from django.conf import settings

DEBUG_ALERTS = getattr(settings, 'DEBUG_ALERTS', True)
def mk_notifiable_disease_alert(disease, alert_type, reporting_period, loc, district_data):
    notif = Notification(alert_type=alert_type)
    rr = "%s_%s" % (reporting_period[0].date().strftime('%F'), reporting_period[0].strftime('%H:%M-') + reporting_period[1].strftime('%H:%M'))
    notif.uid = 'disease_%s_%s_%s' % (disease, rr, loc.code)
    txt = "Urgent - "
    has_cases = False
    for d in district_data['data'].values():
        if d['val'] > 0:
            has_cases = True
            txt += "%s at %s %s reported %s cases of %s" % (','.join(d['reporters']), d['name'], d['type'], d['val'], disease)
    if has_cases:
        notif.text = txt
        notif.sms_text = txt
    else: notif.text = ''
    notif.url = None
    notif.originating_location = loc
    return notif

CASES_METRICS = {
          'malaria': {'threshold':3, 'slug':'epi_ma', 'gen': mk_notifiable_disease_alert},
          'accute flacid paralysis': {'threshold':1, 'slug':'cases_af', 'gen': mk_notifiable_disease_alert},
          'animal bites': {'threshold':1, 'slug':'cases_ab', 'gen': mk_notifiable_disease_alert},
          'rabies': {'threshold':1, 'slug':'cases_rb', 'gen': mk_notifiable_disease_alert},
          'cholera':{'threshold':1, 'slug':'cases_ch', 'gen': mk_notifiable_disease_alert},
          'dysentery': {'threshold':1, 'slug':'cases_dy', 'gen': mk_notifiable_disease_alert},
          'guinea worm': {'threshold':1, 'slug':'cases_gw', 'gen': mk_notifiable_disease_alert},
          'measles': {'threshold':1, 'slug':'cases_me', 'gen': mk_notifiable_disease_alert},
          'bacterial meningitis': {'threshold':1, 'slug':'', 'gen': mk_notifiable_disease_alert},
          'neonatal tetanus': {'threshold':1, 'slug':'cases_nt', 'gen':mk_notifiable_disease_alert},
          'plague': {'threshold':1, 'slug':'cases_pl', 'gen': mk_notifiable_disease_alert},
          'yellow fever': {'threshold':1, 'slug':'cases_yf', 'gen': mk_notifiable_disease_alert},
          'other viral naemorrhagic fevers': {'threshold':1, 'slug':'cases_vf', 'gen': mk_notifiable_disease_alert},
          'severe acute respiratory infections':{'threshold':1, 'slug':'cases_sa', 'gen': mk_notifiable_disease_alert},
          'adverse events following immunization':{'threshold':1, 'slug':'cases_ai', 'gen': mk_notifiable_disease_alert},
          'typhoid fever':{'threshold':1, 'slug':'cases_tf', 'gen': mk_notifiable_disease_alert},
          'other emerging infectious diseases':{'threshold':1, 'slug':'cases_id', 'gen': mk_notifiable_disease_alert},
          }

DEATH_METRICS = {
          'malaria': {'threshold':3, 'slug':'epi_ma', 'gen': mk_notifiable_disease_alert},
          'accute flacid paralysis': {'threshold':1, 'slug':'death_af', 'gen': mk_notifiable_disease_alert},
          'animal bites': {'threshold':1, 'slug':'death_ab', 'gen': mk_notifiable_disease_alert},
          'rabies': {'threshold':1, 'slug':'death_rb', 'gen': mk_notifiable_disease_alert},
          'cholera':{'threshold':1, 'slug':'death_ch', 'gen': mk_notifiable_disease_alert},
          'dysentery': {'threshold':1, 'slug':'death_dy', 'gen': mk_notifiable_disease_alert},
          'guinea worm': {'threshold':1, 'slug':'death_gw', 'gen': mk_notifiable_disease_alert},
          'measles': {'threshold':1, 'slug':'death_me', 'gen': mk_notifiable_disease_alert},
          'bacterial meningitis': {'threshold':1, 'slug':'', 'gen': mk_notifiable_disease_alert},
          'neonatal tetanus': {'threshold':1, 'slug':'death_nt', 'gen':mk_notifiable_disease_alert},
          'plague': {'threshold':1, 'slug':'death_pl', 'gen': mk_notifiable_disease_alert},
          'yellow fever': {'threshold':1, 'slug':'death_yf', 'gen': mk_notifiable_disease_alert},
          'other viral naemorrhagic fevers': {'threshold':1, 'slug':'death_vf', 'gen': mk_notifiable_disease_alert},
          'severe acute respiratory infections':{'threshold':1, 'slug':'death_sa', 'gen': mk_notifiable_disease_alert},
          'adverse events following immunization':{'threshold':1, 'slug':'death_ai', 'gen': mk_notifiable_disease_alert},
          'typhoid fever':{'threshold':1, 'slug':'death_tf', 'gen': mk_notifiable_disease_alert},
          'other emerging infectious diseases':{'threshold':1, 'slug':'death_id', 'gen': mk_notifiable_disease_alert},
                }

class NotifiableDiseaseThresholdAlert(NotificationType):
    escalation_levels = ['district', 'moh']

    def users_for_escalation_level(self, esc_level):
        if esc_level == 'district':
            #all users with reporting_district = district
            return [c.user for c in Contact.objects.filter(reporting_location=self.originating_location) if c.user]
        elif esc_level == 'moh':
            #all users with group 'moh'
            return [User.objects.get(username='admin')] #todo: is there an moh 'group'?

    def auto_escalation_interval(self, esc_level):
        return timedelta(minutes=5) #days=14)

    def escalation_level_name(self, esc_level):
        return {
            'district': 'district team',
            'moh': 'ministry of health',
            }[esc_level]
    def sms_users(self):
        hps = HealthProvider.objects.exclude(reporting_location=None, connection=None).filter(groups__name__in=['DHT']).\
        filter(reporting_location__type='district', reporting_location__name=self.originating_location.name)
        return hps

def get_facility_indicator_notification(metric, info, debug=False):
    if DEBUG_ALERTS:
        reporting_range = (datetime(2011, 1, 1, 0, 0, 0), datetime.now())
    else:
        reporting_range = (datetime.now() - datetime.timedelta(minutes=15), datetime.now())
    res = {}
    subs = XFormSubmissionValue.objects.filter(submission__has_errors=False,
            submission__created__range=reporting_range, value_int__gt=info['threshold'],
            ).filter(attribute__slug=info['slug'])
    for sub in subs:
        if not sub.submission.connection or not sub.submission.connection.contact:
            continue
        if not sub.submission.connection.contact.healthproviderbase.healthprovider.facility:
            continue
        facility = sub.submission.connection.contact.healthproviderbase.healthprovider.facility
        loc = sub.submission.connection.contact.reporting_location
        if not loc:
            continue
        if loc.type.name == 'district':
            district = loc
        else:
            r = loc.get_ancestors().filter(type='district')
            if r:
                district = r[0]
            else: continue #we possibly have country
        val = sub.value_int
        if district.pk  not in res:
            if debug:
                res[district.pk] = {'name':district.name, 'data':{facility.id:{'name':facility.name, 'type':facility.type.name, 'val':val, 'submission':sub.submission.pk}}}
            else:
                reporter = '%s(%s)' % (sub.submission.connection.contact.name, sub.submission.connection.identity)
                res[district.pk] = {'name':district.name, 'data':{facility.id:{'name':facility.name, 'type':facility.type.name, 'val':val, 'reporters':[reporter]}}}
        else:
            if facility.id not in res[district.pk]['data']:
                if debug:
                    res[district.pk]['data'] = {facility.id:{'name':facility.name, 'type':facility.type.name, 'val':val, 'submission':sub.submission.pk}}
                else:
                    reporter = '%s(%s)' % (sub.submission.connection.contact.name, sub.submission.connection.identity)
                    res[district.pk]['data'] = {facility.id:{'name':facility.name, 'type':facility.type.name , 'val':val, 'reporters':[reporter] }}
            else:
                res[district.pk]['data'][facility.id]['val'] += val
                reporter = '%s(%s)' % (sub.submission.connection.contact.name, sub.submission.connection.identity)
                if not (res[district.pk]['data'][facility.id]['reporters'].__contains__(reporter)):
                    res[district.pk]['data'][facility.id]['reporters'].append(reporter)
    return res

def notifiable_disease_test2():
    if DEBUG_ALERTS:
        reporting_period = (datetime(2011, 1, 1, 0, 0, 0), datetime.now())
    else:
        reporting_period = (datetime.now() - datetime.timedelta(minutes=15), datetime.now())
    for metric, info in CASES_METRICS.iteritems():
        #todo: is the end date inclusive or exclusive?
        data = get_facility_indicator_notification(metric, info, False)
        for key in data.keys():
            loc = Location.objects.get(id=key)
            district_data = data[key]
            yield info['gen'](metric, 'alerts._prototyping.NotifiableDiseaseThresholdAlert', reporting_period, loc, district_data)

    for metric, info in DEATH_METRICS.iteritems():
        #todo: is the end date inclusive or exclusive?
        data = get_facility_indicator_notification(metric, info, False)
        for key in data.keys():
            loc = Location.objects.get(id=key)
            district_data = data[key]
            yield info['gen'](metric, 'alerts._prototyping.NotifiableDiseaseThresholdAlert', reporting_period, loc, district_data)

