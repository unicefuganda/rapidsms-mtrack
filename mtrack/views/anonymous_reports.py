from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse
from mtrack.models import AnonymousReport
from mtrack.forms import EditAnonymousReportForm
from django.template import RequestContext
from django.views.generic.base import TemplateView
import xlwt
from mtrack.utils import *
from healthmodels.models.HealthFacility import HealthFacilityBase
@login_required
def delete_report(request, report_pk):
    report = get_object_or_404(AnonymousReport, pk=report_pk)
    if request.method == 'POST':
        report.delete()
    return HttpResponse(status=200)

@login_required
def edit_anonymous_report(request, anonymous_report_pk):
    #anonymous_report = get_object_or_404(AnonymousReport, pk=anonymous_report_pk)
    anonymous_report = AnonymousReport.objects.get(pk=anonymous_report_pk)
    edit_report_form = EditAnonymousReportForm(request.POST, instance=anonymous_report)
    if request.method == "GET":
        return render_to_response('mtrack/partials/anon_edit_row.html', {'anonymous_report':anonymous_report, 'report_form':EditAnonymousReportForm(
            initial={
                'district':anonymous_report.district,
                'health_facility': anonymous_report.health_facility,
                'action' : anonymous_report.action,
                'comments' : anonymous_report.comments
            }
        ), 'facilities':get_facilities(), 'pk':getattr(anonymous_report.health_facility, 'pk', '')}, context_instance=RequestContext(request))

    if request.method == 'POST':
        if edit_report_form.is_valid:
            edit_report_form.save()
        else:
            return render_to_response('mtrack/partials/anon_edit_row.html',
                    { 'report_form':edit_report_form, 'anonymous_report':anonymous_report }, context_instance=RequestContext(request))
        return render_to_response('mtrack/partials/anon_row.html',
                { 'object':AnonymousReport.objects.get(pk=anonymous_report_pk), 'selectable':True }, context_instance=RequestContext(request))
    else:
        return render_to_response('mtrack/partials/anon_edit_row.html',
                { 'report_form':edit_report_form, 'anonymous_report':anonymous_report }, context_instance=RequestContext(request))

@login_required
def create_excel(request):
    book = xlwt.Workbook(encoding="utf8")
    headings = ["Facility", "District", "Date", "Reports", "Status", "Comments"]
    data_set = []
    for ar in AnonymousReport.objects.all():
        try:
            if not ar.comments:
                ar.comments = "Missing"
            if not ar.health_facility and not ar.district:
                data_set.append(["Missing", "Missing", ar.date, ar.messages.values()[0]['text'], ar.get_action_display(), ar.comments])
            if not ar.health_facility:
                data_set.append(["Missing", ar.district.__unicode__(), ar.date, ar.messages.values()[0]['text'], ar.get_action_display(), ar.comments])
            if not ar.district:
                data_set.append([ar.health_facility.__unicode__(), "Missing", ar.date, ar.messages.values()[0]['text'], ar.get_action_display(), ar.comments])
            else:
                data_set.append([ar.health_facility.__unicode__(), ar.district.__unicode__(), ar.date, ar.messages.values()[0]['text'], ar.get_action_display(), ar.comments])
        except:
            pass
    #data_set = [[ar.health_facility, ar.district, ar.date, ar.messages.values()[0], ar.action, ar.comments] for ar in AnonymousReport.objects.all()]
    write_xls(sheet_name="Anonymous Reports", headings=headings, data=data_set, book=book)
    response = HttpResponse(mimetype="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename=anonymous_report.xls'
    book.save(response)
    return response
