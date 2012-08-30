import datetime
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from rapidsms_xforms.models import XForm
from rapidsms_httprouter.models import Message
from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.models import Group
from django.conf import settings
from mtrack.models import Schedules, ScheduleExtras

def broadcasts(request):
    #consider a list
    locs = Location.objects.filter(type__name='district').values_list('name',flat='TRUE')
    locs = [l.upper() for l in locs]
    if request.user.username in locs:
        districts = Location.objects.filter(type__name='district', name=request.user.username.capitalize()).values('id','name')
    else:
        districts = Location.objects.filter(type__name='district').values('id', 'name').order_by('name')
    groups = Group.objects.all().order_by('name')
    xforms = XForm.objects.all().values('id', 'name', 'keyword').order_by('name')

    if request.method == 'POST':
        #if form.is_valid():
        setup = request.POST['setup']
        loc_type = request.POST['loc_type']
        location = request.POST['location']
        location2 = request.POST['location2']
        rtype = request.POST['rtype']
        gtype = request.POST['gtype']
        grp = request.POST['grp']
        grp2 = request.POST['grp2']
        xformtype = request.POST['xformtype']
        xform = request.POST['xform']
        xform2 = request.POST['xform2']
        reporter = request.POST['reporter']
        hrs = request.POST['hrs']
        mins = request.POST['mins']
        sdate = request.POST['sdate']
        msg = request.POST['msg']
        handler = request.POST['handler']
        args = request.POST['args']
        edate = request.POST['edate']
        edate = None if not edate else edate
        interval = request.POST['interval']
        repeat_day = request.POST.getlist('repeat_day') if ('repeat_day' in request.POST) else []
        repeat_day = ','.join(repeat_day)
        week_number = request.POST['week_number']

        loc = location2.replace('\r\n',',') if loc_type == 'list' else location
        group = grp2 if gtype == 'list' else grp
        missing_xforms = xform2 if xformtype == 'list' else xform
        msg_is_temp = False if setup == 'basic' else True

        print loc, group, missing_xforms, interval, repeat_day
        b = Schedules.objects.create(created_by='sam', start_date= sdate, end_date=edate,
                start_time='%s:%s'%(hrs,mins), message_type=setup, message=msg, recur_interval=interval,
                recur_frequency=0, recur_day=repeat_day, recur_weeknumber = week_number)

        c = ScheduleExtras.objects.create(schedule=b, recipient_location_type=loc_type,
                recipient_location=loc, allowed_recipients=rtype, recipient_group_type=gtype,
                missing_reports=missing_xforms, expected_reporter=reporter, group_ref=group,
                is_message_temp=msg_is_temp, message_args=args, return_code=handler)
        print b, c



    else:
        #print "We're in a GET request"
        pass

    return render_to_response('mtrack/schedule.html', {'districts': districts,
                                                         'xforms': xforms,
                                                         'groups': groups,
                                                         'hrs': range(24),
                                                         'mins': range(60),
                                                         },
                              context_instance=RequestContext(request))

