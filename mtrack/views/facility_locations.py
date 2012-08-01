import datetime
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from rapidsms.contrib.locations.models import Location
from healthmodels.models.HealthFacility import HealthFacility
from rapidsms_httprouter.models import Message
from django.http import HttpResponse
from django.utils import simplejson
from django.conf import settings

def facility_cas(request):
    #consider a list
    locs = Location.objects.filter(type__name='district').values_list('name',flat=True)
    locs = [l.upper() for l in locs]
    districts = Location.objects.filter(type__name='district').values('id', 'name').order_by('name')
    #facilities = HealthFacility.objects.all().values('id', 'name', 'type__slug').order_by('name')
    facilities = [(0, 'Select Facility')]

    if request.method == 'POST':
       pass
    else:
        pass
    return render_to_response('mtrack/facility_locations.html', {'districts': districts,
                                                         'facilities': facilities,
                                                         },
                              context_instance=RequestContext(request))

def ajax_portal2(request):
    xtype = request.GET.get('xtype', '')
    xid = request.GET.get('xid', '')
    if xtype == 'district':
        district_locs = Location.objects.get(pk=xid).get_descendants(include_self=True)

        facilities = list(HealthFacility.objects.filter(catchment_areas__in=district_locs).\
                          values('id', 'name', 'type__slug').order_by('name').distinct())
        response = facilities
    elif xtype == 'facility':
        response = list(HealthFacility.objects.get(pk=xid).catchment_areas.all().values('name','type'))
    else:
        response = []
    json = simplejson.dumps(response)
    return HttpResponse(json, mimetype='application/json')

