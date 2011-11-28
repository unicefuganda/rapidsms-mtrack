from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from mtrack.models import AnonymousReport
from mtrack.forms import AnonymousEditReportForm
from generic.views import generic_row
from django.template import RequestContext


@login_required
def delete_report(request, id):
    AnonymousReport.objects.get(id=id).delete()
    return HttpResponseRedirect('repdelete/')


@login_required
def edit_report(req, id):
	import pdb; pdb.set_trace()
	anonymous_report = get_object_or_404(AnonymousReport, pk=id)
	edit_report_form = AnonymousEditReportForm(instance=anonymous_report)
	if req.method == 'POST':
		edit_report_form = AnonymousEditReportForm(instance=anonymous_report, data=request.POST)
		if edit_report_form.is_valid:
			edit_report_form.save()
			return generic_row(req, model=AnonymousReport,pk=id, partial_row="mtrack/partials/anon_row.html")
		else:
			return render_to_response('mtrack/partials/anon_edit_row.html')
	return render_to_response('/mtrack/partials/anon_edit_form.html', {'form':edit_report_form}, context_instance=RequestContext(req))