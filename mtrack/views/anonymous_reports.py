from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse
from mtrack.models import AnonymousReport
from mtrack.forms import EditAnonymousReportForm
from django.template import RequestContext
    
@login_required
def view_report(request, report_pk):
    report = get_object_or_404(AnonymousReport, pk=report_pk)
    anonymous_edit_form = EditAnonymousReportForm(instance=report)
    # when message sent to anonymous reporter, this should get shown in the responses column 
    # match this by anonymous reporter's connection
    responses = ['test response']
    return render_to_response('mtrack/partials/anon_view.html', 
		{'form':anonymous_edit_form, 'responses':responses }, context_instance=RequestContext(request))

@login_required
def delete_report(request, report_pk):
    report = get_object_or_404(AnonymousReport, pk=report_pk)
    if request.method == 'POST':
        report.delete()
    return HttpResponse(status=200)

@login_required
def edit_report(request, anonymous_report_pk):        
    anonymous_report = AnonymousReport.objects.get(pk=anonymous_report_pk)
    message = anonymous_report.message.text
    edit_report_form = EditAnonymousReportForm(instance=anonymous_report)
    if request.method == 'POST':
        edit_report_form = EditAnonymousReportForm(request.POST, instance=anonymous_report)
        if edit_report_form.is_valid:
            edit_report_form.save()
        else:
            return render_to_response('mtrack/partials/anon_edit_row.html',
                    { 'report_form':edit_report_form, 'anonymous_report':anonymous_report, 'message':message }, context_instance=RequestContext(request))
        return render_to_response('mtrack/partials/anon_row.html',
                { 'object':AnonymousReport.objects.get(pk=anonymous_report_pk),'selectable':True }, context_instance=RequestContext(request))
    else:
        return render_to_response('mtrack/partials/anon_edit_row.html',
                { 'report_form':edit_report_form, 'anonymous_report':anonymous_report, 'message':message },context_instance=RequestContext(request))