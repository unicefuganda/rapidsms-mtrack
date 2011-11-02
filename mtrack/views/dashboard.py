#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from rapidsms.contrib.locations.models import Location
from uganda_common.utils import get_location_for_user
from mtrack.utils import non_reporting_facilities, non_reporting_vhts, total_facilities, total_vhts

def admin(request):
    location = Location.tree.root_nodes()[0]
    if request.user:
        location = get_location_for_user(request.user) or location

    return render_to_response('mtrack/partials/dashboard_admin.html', {
            'bad_facilities':non_reporting_facilities(location),
            'bad_vhts':non_reporting_vhts(location),
            'total_facilities':total_facilities(location),
            'total_vhts':total_vhts(location),
        },
        context_instance=RequestContext(request))
