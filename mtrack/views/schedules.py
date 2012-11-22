from django.core.urlresolvers import reverse
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from mtrack.forms import ScheduleForm
from mtrack.models import Schedules

def broadcasts(request):
    form = ScheduleForm()

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('reminder-schedules'))
    return render_to_response('mtrack/schedule.html', {'form':form},context_instance=RequestContext(request))

def edit_schedule(request,id):
    schedule = get_object_or_404(Schedules,id=id)
    #So the temporary plan is to populate this form manually as we come up with a django plan
    initial_data = {'setup':schedule.message_type,'locations':schedule.extras.recipient_location.split(","),'group':schedule.extras.group_ref.split(","),
                     'reporter':schedule.extras.expected_reporter.split(","),'xforms':schedule.extras.missing_reports.split(","),
                     'start_date':schedule.start_date,'end_date':schedule.end_date,'interval':schedule.recur_interval,
                     'week_number':schedule.recur_weeknumber,'repeat_day':schedule.recur_day.split(","),'hour':schedule.start_time.hour,
                     'minutes':schedule.start_time.minute,'message':schedule.message,'user_type':'live'}
    form = ScheduleForm(initial_data)
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.update()
            return HttpResponseRedirect(reverse('reminder-schedules'))
    return render_to_response('mtrack/schedule.html', {'form':form},context_instance=RequestContext(request))
@require_POST
@csrf_exempt
def delete_schedule(request,id):
    schedule = get_object_or_404(Schedules,id=id)
    schedule.delete()
    return HttpResponse(status=200)