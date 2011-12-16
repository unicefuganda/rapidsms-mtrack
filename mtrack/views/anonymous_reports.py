from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse
from mtrack.models import AnonymousReport
from mtrack.forms import EditAnonymousReportForm
from django.template import RequestContext

@login_required
def delete_report(request, report_pk):
    report = get_object_or_404(AnonymousReport, pk=report_pk)
    if request.method == 'POST':
        report.delete()
    return HttpResponse(status=200)

@login_required
def edit_report(request, anonymous_report_pk):            
    #anonymous_report = get_object_or_404(AnonymousReport, pk=anonymous_report_pk)
    anonymous_report = AnonymousReport.objects.get(pk=anonymous_report_pk)
    edit_report_form = EditAnonymousReportForm(request.POST, instance=anonymous_report)
    if request.method == "GET":
        return render_to_response('mtrack/partials/anon_edit_row.html',{'anonymous_report':anonymous_report, 'report_form':EditAnonymousReportForm(
            initial={
                'district':anonymous_report.district,
                'health_facility': anonymous_report.health_facility,
                'action' : anonymous_report.action,
                'comments' : anonymous_report.comments
            }
        )}, context_instance=RequestContext(request))

    if request.method == 'POST':
        if edit_report_form.is_valid:
            edit_report_form.save()
        else:
            return render_to_response('mtrack/partials/anon_edit_row.html',
                    { 'report_form':edit_report_form, 'anonymous_report':anonymous_report }, context_instance=RequestContext(request))
        return render_to_response('mtrack/partials/anon_row.html',
                { 'object':AnonymousReport.objects.get(pk=anonymous_report_pk),'selectable':True }, context_instance=RequestContext(request))
    else:
        return render_to_response('mtrack/partials/anon_edit_row.html',
                { 'report_form':edit_report_form, 'anonymous_report':anonymous_report },context_instance=RequestContext(request))