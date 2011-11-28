from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

@login_required
def delete_report(request, id):
    AnonymousReport.objects.get(id=id).delete()
    return HttpResponseRedirect('repdelete/')
