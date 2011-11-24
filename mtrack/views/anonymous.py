from django.shortcuts import get_object_or_404
from .models import AnonymousReport
from django.core.urlresolvers import reverse

def reportit(req, report_id):
    report = get_object_or_404(AnonymousReport, pk=report_id)
    #return HttpResponseRedirect(reverse(
