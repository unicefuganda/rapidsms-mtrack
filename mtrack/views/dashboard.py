#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from uganda_common.utils import get_location_for_user
from mtrack.utils import reporting_facilities, reporting_vhts, last_reporting_period, total_registered_facilities, total_vhts, get_facility_reports, last_reporting_period_number, current_reporting_week_number

def admin(request):
    location = get_location_for_user(request.user)

    return render_to_response('mtrack/partials/dashboard_admin.html', {
            #change period = 1 for the last reporting                                                           
            'good_facilities':reporting_facilities(location, date_range=last_reporting_period(period=0)),
            'good_vhts':reporting_vhts(location),
            'total_facilities':total_registered_facilities(location),
            'total_vhts':total_vhts(location),
            'reporting_period': last_reporting_period_number(),
            'current_week': current_reporting_week_number()
        },
        context_instance=RequestContext(request))

def approve(request):
    location = get_location_for_user(request.user)

    return render_to_response('mtrack/partials/dashboard_approve.html', {
            'reports':get_facility_reports(location, date_range=last_reporting_period(weekday=0, period=0), count=True, approved=False),
            'total_reports':get_facility_reports(location, date_range=last_reporting_period(weekday=0, todate=True), count=True, approved=False),
            'reporting_period': last_reporting_period_number(),
            'current_week': current_reporting_week_number()
        },
        context_instance=RequestContext(request))
