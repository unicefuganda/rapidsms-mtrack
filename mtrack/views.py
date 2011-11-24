from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

@login_required
def delete_report(requestion, report_id):
    report = get_object_or_404(AnonymousReport, pk=report_id)
    if request.method == 'POST':
        report.delete()
    return HttpResponse(status=200)
