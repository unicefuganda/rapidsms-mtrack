from rapidsms_xforms.views import edit_submission
from django.http import HttpResponseRedirect
from mtrack.utils import last_reporting_period
from django.shortcuts import get_object_or_404, redirect
from rapidsms_xforms.models import XFormSubmission

def edit_report(req, submission_id):
    submission = get_object_or_404(XFormSubmission, pk=submission_id)
    toret = edit_submission(req, submission_id)

    if type(toret) == HttpResponseRedirect:
        d = last_reporting_period()
        if d[0] < submission.created and d[1] > submission.created:
            return redirect('/approve')
        else:
            return redirect('/hc/reports/')
    else:
        return toret
