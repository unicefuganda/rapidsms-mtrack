import datetime
from django.core import urlresolvers
from django.template import RequestContext
from django.shortcuts import render_to_response
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from healthmodels.models.HealthProvider import HealthProvider
from rapidsms_xforms.models import XForm, XFormSubmission
from rapidsms_xforms.views import make_submission_form
from rapidsms_httprouter.models import Message
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.conf import settings
from mtrack.models import XFormSubmissionExtras
from mtrack.utils import current_reporting_week_number, last_reporting_period

def data_entry(request):
    #consider a list
    locs = Location.objects.filter(type__name='district').values_list('name',flat='TRUE')
    locs = [l.upper() for l in locs]
    if request.user.username in locs:
        districts = Location.objects.filter(type__name='district', name=request.user.username.capitalize()).values('id','name')
    else:
        districts = Location.objects.filter(type__name='district').values('id', 'name').order_by('name')
    #facilities = HealthFacility.objects.all().values('id', 'name', 'type__slug').order_by('name')
    facilities = [(0, 'Select Facility')]
    reporters = [(0, 'Select Reporter')]
    xforms = []
    today = datetime.date.today()
    week_ranges = []
    #weeks_this_year = int(datetime.date(today.year,12,31).strftime('%W'))
    cur_week_num = current_reporting_week_number()
    for n in xrange(1,cur_week_num+1):
        d = {}
        d['week'] = '%02d'% n
        #_range = _getWeekDetails(n,today.year,2) #Monday = 2
        _range = last_reporting_period(period=(cur_week_num-n))
        d['range'] = ' (%s - %s)' %(_range[0].strftime('%Y-%m-%d'), _range[1].strftime('%Y-%m-%d'))
        week_ranges.append(d)
    #xforms = XForm.objects.all().values('id', 'name', 'keyword').order_by('name')
    if request.method == 'POST':
        xform = request.POST['xform']
        reporterid = request.POST['reporter']
        reporter = HealthProvider.objects.get(pk=reporterid)
        the_xform = XForm.on_site.get(pk=xform)
        is_late = getattr(request.POST,'islate',False)
        rweek = request.POST['rweek']
        submitted_by = request.POST['submitted_by']

        if is_late == True:
            #3 days after start of reporting period
            rdate = last_reporting_period(period=cur_week_num - int(rweek))[0] + datetime.timedelta(days=3)
        else:
            #6 days after start of reporting period
            rdate = last_reporting_period(period=cur_week_num - int(rweek))[0] + datetime.timedelta(days=6)

        form_class = make_submission_form(the_xform)

        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            msg = the_xform.keyword.upper()
            for k,v in form.cleaned_data.iteritems():
                if k not in ['districts','reporter', 'facility', 'submitted_by', 'rtype', 'rweek', 'islate']:
                    if v or v in ('0',0):
                        msg +="." + "%s."%k + "%s"%v
            #create message here and insert into database!!
            #cdate = datetime.datetime.strptime(rdate, '%Y-%m-%d')
            MsgObj = None
            if len(msg) > len(the_xform.keyword):
                MsgObj = Message.objects.create(text=msg, direction='I', status='H',
                        connection=reporter.default_connection)
                MsgObj.date = rdate
                MsgObj.save()
            #now lets create a submission for this xform
            submission = XFormSubmission.objects.create(xform=the_xform, connection=reporter.default_connection)
            the_xform.update_submission_from_dict(submission, form.cleaned_data)
            #remember to set the reporter
            if MsgObj:
                submission.message = MsgObj
                submission.created = rdate
                XFormSubmissionExtras.objects.create(submission=submission,
                        submitted_by=submitted_by+":"+request.user.username, is_late_report=is_late)
            submission.save()
            return HttpResponseRedirect(urlresolvers.reverse('dataentry'))
    else:
        pass
    return render_to_response('mtrack/data_entry.html', {'districts': districts,
                                                         'facilities': facilities,
                                                         'xforms': xforms,
                                                         'weeks': week_ranges,
                                                         'hmis_reports': getattr(settings, "HMIS_REPORTS",
                                                             [
                                                                 {'name':'HMIS 033B Report',
                                                                     'keywords':'act,opd,com,test,treat,rdt,qun,epi,rutf,cases,death'
                                                                    }
                                                                 ])
                                                         },
                              context_instance=RequestContext(request))

def ajax_portal(request):
    xtype = request.GET.get('xtype', '')
    xid = request.GET.get('xid', '')
    if xtype == 'district':
        district_locs = Location.objects.get(pk=xid).get_descendants(include_self=True)

        facilities = list(HealthFacility.objects.filter(catchment_areas__in=district_locs).\
                          values('id', 'name', 'type__slug').order_by('name').distinct())
        response = facilities
    elif xtype == 'facility':
        response = list(HealthProvider.objects.exclude(connection=None).filter(facility=xid)\
                        .exclude(groups__name__in=['FHD'])\
                        .values('id', 'name', 'connection__identity').order_by('name'))
    elif xtype == 'xform':
        xform = XForm.on_site.get(pk=xid)
        fields = xform.fields.all().order_by('order').values('name', 'command', 'field_type')
        response = list(fields)
    elif xtype == 'report':
        qq = xid.split(',')
        response = list(XForm.objects.filter(keyword__in=qq).values('id', 'name', 'keyword').order_by('name'))
    else:
        response = []
    json = simplejson.dumps(response)
    #from django.db import connection
    #print connection.queries
    return HttpResponse(json, mimetype='application/json')

