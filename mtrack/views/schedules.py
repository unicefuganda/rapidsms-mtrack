from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from mtrack.forms import ScheduleForm

def broadcasts(request):
    form = ScheduleForm()

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('schedule_creator'))
    return render_to_response('mtrack/schedule.html', {'form':form},context_instance=RequestContext(request))