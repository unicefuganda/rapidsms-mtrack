import random
from django.core.management.base import BaseCommand
from mtrack.utils import last_reporting_period, current_reporting_week_number
from healthmodels.models.HealthFacility import HealthFacility
from healthmodels.models.HealthProvider import HealthProvider
from rapidsms_httprouter.models import Message
from rapidsms.models import Connection
from rapidsms.contrib.locations.models import Location
from rapidsms_xforms.models import XForm, XFormSubmission, XFormSubmissionValue
from mtrack.models import Schedules, ScheduleExtras
from django.db.models import Q, Sum
from datetime import datetime
from django.db import connections

def weekday():
    return datetime.now().weekday() + 1

class Command(BaseCommand):
    help = """Handle the scheduled broadcasts/reminders"""
    wdays = ['none','mon','tue','wed','thu','fri','sat','sun']
    day_today = wdays[weekday()]
    time_now = datetime.now().strftime('%H:%M')
    date_now = datetime.now().date()
    day_of_month = datetime.now().day
    #XXX Debug
    #current_reporting_period = last_reporting_period(period=19)
    current_reporting_period = last_reporting_period(period=0)
    cur_week = current_reporting_week_number()
    last_week = cur_week - 1

    #Let's get a cursor
    cur = connections['default'].cursor()
    sql = ("SELECT id FROM schedules WHERE enabled = %s AND start_time = '%s' AND (" # = instead of > on start_time
            "( recur_interval = 'none' AND start_date = '%s') OR "
            "( recur_interval = 'day' AND ( end_date IS NULL OR  end_date >= '%s') ) OR "
            "( recur_interval = 'week' AND strpos(recur_day,'%s') > 0 AND ( end_date IS NULL OR end_date >= '%s') ) OR "
            "( recur_interval = 'month' AND EXTRACT(DAY FROM start_date) = %s AND (end_date IS NULL OR end_date >= '%s') )"
            ")")
    #here strpos replaces LIKE '%%%s%%' which is failing us
    #sql = sql % (True, time_now,date_now,date_now,day_today,date_now,day_of_month,date_now)
    sql = sql % (True, '8:00',date_now,date_now,day_today,date_now,day_of_month,date_now)
    #print sql
    cur.execute(sql)
    res = cur.fetchall()
    #print res
    ids = [l[0] for l in res ]

    schedules = Schedules.objects.filter(pk__in=ids)

    def handle(self, *args, **options):
        #globals()['my_function']('Samuel')
        self.gen_reminders(self.schedules)

    def gen_reminders(self,schedules):
        for sched in schedules:
            #get districts for which to generate reminders
            if sched.extras.recipient_location_type == 'all':
                districts = Location.objects.filter(type='district')
            elif sched.extras.recipient_location_type == 'list':
                districts = Location.objects.filter(type='district',name__in=sched.extras.recipient_location.split(','))
            else:
                districts = Location.objects.filter(type='district', name=sched.extras.recipient_location)

            my_handler = sched.extras.return_code
            grps = sched.extras.group_ref.split(',')
            missing_reports = sched.extras.missing_reports.split(',')
            expected_reporter = sched.extras.expected_reporter
            #used to filter out live and training mode users
            apply_to_all_users = True if sched.extras.allowed_recipients == 'all' else False
            allowed_recipient_filter = True if sched.extras.allowed_recipients == 'live' else False
            #for each district get the facilities =>Non reporting
            for district in districts:
                print district
                facilities = HealthFacility.objects.filter(catchment_areas__in=district.\
                        get_descendants(include_self=True)).select_related('HealthFacilityTypeBase').\
                        distinct()
                total_facilities = facilities.count()
                reporting_facility_count = 0
                non_reporting_facilities = []
                stocked_out_facilities = []
                for facility in facilities:
                    #print self.get_facility_xform_aggregate(facility,'cases',last_reporting_period(period=19))
                    #print self.stockout_reporting_vhts(facility,'act',last_reporting_period(period=19),active=False)
                    proposed_recipients = HealthProvider.objects.filter(facility=facility,groups__name__in=grps)
                    if not apply_to_all_users:
                        proposed_recipients = proposed_recipients.filter(active=allowed_recipient_filter)
                    proposed_recipients = proposed_recipients.exclude(connection__identity=None)

                    if not proposed_recipients:
                        continue
                    conns = Connection.objects.filter(contact__in=proposed_recipients)
                    if conns:
                        if not self.facility_has_sent_report(facility,missing_reports,expected_reporter):
                            non_reporting_facilities.append('%s %s' % (facility.name, facility.type.name.upper()))
                            if my_handler == 'non_reporting_facility':
                                args_dict = {'facility':'%s %s' % (facility.name, facility.type.name.upper())}
                                #print sched.message % args_dict
                                reminder_msg = sched.message % args_dict
                                Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')
                            elif my_handler == '':
                                Message.mass_text(sched.message, conns, status='Q',batch_status='Q')
                        else:
                            reporting_facility_count += 1

                        #XXX remember to remove active=False
                        if my_handler == 'vht_summary':
                            args_dict = self.non_reporting_vhts(facility, missing_reports,
                                    active=allowed_recipient_filter,lp=last_reporting_period(period=0))
                            if args_dict:
                                args_dict.update({'week':self.last_week})
                                reminder_msg = sched.message % args_dict
                                #print "#######=>",reminder_msg
                                Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')
                        elif my_handler == 'vht_aggregate':
                            #here missing_reports serves as
                            args_dict = self.non_reporting_vhts(facility, missing_reports[0],
                                    active=False,lp=last_reporting_period(period=0))
                            args_dict.update({
                                'aggregate': self.get_facility_xform_aggregate(facility,missing_reports[0],
                                    last_reporting_period(period=0)),
                                'week': self.last_week
                                })
                            reminder_msg = sched.message % args_dict
                            Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')
                        elif my_handler == 'stockouts_facility':
                            self.manage_stock_outs(facility, stocked_out_facilities,last_reporting_period(period=0))

                        elif my_handler == 'stockouts_vht':
                            args_dict = self.stockout_reporting_vhts(facility,missing_reports[0],
                                    last_reporting_period(period=19),active=False)
                            if args_dict['list']:
                                # send reminder
                                args_dict.update({'week':self.last_week})
                                reminder_msg = sched.message % args_dict
                                Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')

                #here we only send to DHTs
                dhts = HealthProvider.objects.filter(facility__in=facilities, groups__name__in=['DHT']).\
                        exclude(connection__identity=None).distinct()
                conns = Connection.objects.filter(contact__in=dhts)
                if conns:
                    if my_handler == 'dht_summary':
                        args_dict = {'district': district.name, 'total':total_facilities, 'week':self.last_week,
                                'reporting': reporting_facility_count, 'list': ', '.join(non_reporting_facilities)}
                        reminder_msg = sched.message % args_dict
                        Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')
                        #print reminder_msg
                    elif my_handler == 'stockouts_facility':
                        if stocked_out_facilities:
                            args_dict = {'stocked_out':len(stocked_out_facilities),
                                    'total': total_facilities, 'list': ', '.join(stocked_out_facilities)}
                        if args_dict['list']:
                            args_dict.update({'week':self.last_week})
                            reminder_msg = sched.message % args_dict
                            Message.mass_text(reminder_msg, conns, status='Q',batch_status='Q')


    def facility_has_sent_report(self,facility, xforms,reporter_type,active=True):
        reporters = HealthProvider.objects.filter(groups__name__in=[reporter_type], facility=facility, active=active)
        reports = XFormSubmission.objects.filter(xform__keyword__in=xforms, message__connection__contact__in=reporters,
                created__range=self.current_reporting_period)
        return True if reports else False

    def non_reporting_vhts(self,facility,xforms, active=True,lp=last_reporting_period(period=0)):
        reporters = HealthProvider.objects.filter(groups__name='VHT', facility=facility, active=active)
        total_vhts = reporters.count()
        if not total_vhts: return ''
        reporting = XFormSubmission.objects.filter(xform__keyword__in=xforms,
                message__connection__contact__in=reporters)\
                .filter(created__range=lp)\
                .filter(has_errors=False)\
                .values('message__connection__contact')
        non_reporting = reporters.exclude(contact_ptr__in=reporting).values_list('name', flat=True)
        args_dict = {'facility': '%s %s' % (facility.name, facility.type.name.upper()),
            'reporting':reporting.count(), 'total':total_vhts, 'list':', '.join(non_reporting)}
        return args_dict

    def get_facility_xform_aggregate(self, facility, xform,rp=last_reporting_period(period=0)):
        vals = XFormSubmissionValue.objects.filter(submission__connection__contact__healthproviderbase__facility=facility,
                submission__has_errors=False, submission__xform__keyword=xform,
                submission__created__range=rp).\
                        values('attribute__slug','attribute__name').annotate(value=Sum('value_int'))

        return ', '.join(['%(value)s %(attribute__name)s'%v for v in vals])

    def manage_stock_outs(self,facility,stock_o_f, rp=last_reporting_period(period=0)):
        vals = XFormSubmissionValue.objects.filter(submission__connection__contact__healthproviderbase__facility=facility,
                submission__has_errors=False, submission__xform__keyword='act',
                submission__created__range=rp).\
                        values('submission__xform__keyword').annotate(value=Sum('value_int'))
        if vals:
            if vals[0]['value'] == 0:
                stock_o_f.append('%s %s'%(facility.name,facility.type.name))

    def stockout_reporting_vhts(self,facility,xform, rp=last_reporting_period(period=0),active=True):
        reporters = HealthProvider.objects.filter(groups__name='VHT', facility=facility, active=active)
        total_vhts = reporters.count()
        if not total_vhts: return ''
        vals = XFormSubmissionValue.objects.filter(submission__connection__contact__healthproviderbase__facility=facility,
                submission__has_errors=False, submission__xform__keyword=xform,
                submission__created__range=rp).filter(value_int=0)
        reporting = vals.count()
        vals = vals.values_list('submission__connection__contact__healthproviderbase__name',flat=True)

        args_dict = {'facility': '%s %s' % (facility.name, facility.type.name.upper()),
                'reporting': reporting, 'total':total_vhts, 'list': ', '.join(vals)}
        return args_dict
