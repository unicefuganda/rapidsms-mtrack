from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from healthmodels.models.HealthProvider import HealthProvider
from rapidsms_xforms.models import XForm, XFormSubmission
from rapidsms_xforms.views import make_submission_form
from django.http import HttpResponse
from django.utils import simplejson

def data_entry(request):
    #consider a list
    districts = Location.objects.filter(type__name='district').values('id', 'name').order_by('name')
    facilities = HealthFacility.objects.all().values('id', 'name', 'type__slug').order_by('name')
    reporters = [(0, 'Select Reporter')]
    xforms = XForm.objects.all().values('id', 'name', 'keyword').order_by('name')
    if request.method == 'POST':
        print request.POST
        xform = request.POST['xform']
        reporterid = request.POST['reporter']
        reporter = HealthProvider.objects.get(pk=reporterid)
        the_xform = XForm.on_site.get(pk=xform)
        form_class = make_submission_form(the_xform)

        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            #now lets create a submission for this xform
            submission = XFormSubmission.objects.create(xform=the_xform, connection=reporter.default_connection)
            the_xform.update_submission_from_dict(submission, form.cleaned_data)
            #remember to set the reporter
            submission.save()
    else:
        pass
    return render_to_response('mtrack/data_entry.html', {'districts': districts,
                                                         'facilities': facilities,
                                                         'xforms': xforms,
                                                         },
                              context_instance=RequestContext(request))

def ajax_portal(request):
    xtype = request.GET.get('xtype', '')
    xid = request.GET.get('xid', '')
    if xtype == 'district':
        district_locs = Location.objects.get(pk=xid).get_descendants(include_self=True)

        facilities = list(HealthFacility.objects.filter(catchment_areas__in=district_locs).\
                          values('id', 'name', 'type__slug').order_by('name').distinct())
        response = facilities
    elif xtype == 'facility':
        response = list(HealthProvider.objects.exclude(connection=None).filter(facility=xid)\
                        .values('id', 'name', 'connection__identity').order_by('name'))
    elif xtype == 'xform':
        xform = XForm.on_site.get(pk=xid)
        fields = xform.fields.all().order_by('order').values('name', 'command', 'field_type')
        response = list(fields)
    else:
        response = []
    json = simplejson.dumps(response)
    #from django.db import connection
    #print connection.queries
    return HttpResponse(json, mimetype='application/json')

