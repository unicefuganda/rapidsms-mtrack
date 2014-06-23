import xlwt
import datetime
from time import strftime
from django.db.models import Q, Count
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from mtrack.utils import write_xls
from poll.models import Poll
from django.utils import simplejson


@login_required
def export_poll(request, poll_id=0):
    book = xlwt.Workbook(encoding="utf8")
    headings = [
        "Phone Number", "Role", "Health Facility",
        "Health Facility Type", "District", "Response",
        "Date"
    ]
    data_set = []
    poll = Poll.objects.get(id=poll_id)
    for resp in poll.responses.all():
        contact = resp.contact
        if not contact.default_connection:
            continue
        msisdn = contact.default_connection.identity
        facility = ''
        facility_type = ''
        district = ''
        try:
            if hasattr(contact, 'healthproviderbase'):
                reporter = contact.healthproviderbase
                if reporter:
                    if hasattr(reporter, 'facility'):
                        if reporter.facility:
                            facility = reporter.facility.name
                            facility_type = reporter.facility.type.name.upper()
                            district = reporter.facility.district.capitalize()
            groups = '#'.join(['%s' % g.name for g in contact.groups.all()])
            resp_msg = resp.message.text.replace(',', '#')
            resp_date = resp.date.strftime('%Y-%m-%d %H:%M')
            data_set.append([msisdn, groups, facility, facility_type, district, resp_msg, resp_date])
        except:
            continue
    write_xls(sheet_name="Poll Responses", headings=headings, data=data_set, book=book)
    response = HttpResponse(mimetype="application/vnd.ms-excel")
    fname_prefix = datetime.date.today().strftime('%Y%m%d') + "-" + strftime('%H%M%S')
    response["Content-Disposition"] = 'attachment; filename=%s_%s.xls' % (fname_prefix, poll.name.replace(' ', '_'))
    book.save(response)
    return response

@login_required
def get_poll_responses(request):
    if request.user.is_superuser:
        polls = Poll.objects.all()
    else:
        polls = Poll.objects.filter(user=request.user)
    if request.method == 'POST':
        poll_id = request.POST['poll']
        return redirect('export_poll', poll_id=poll_id)
    return render_to_response('mtrack/poll_download.html', {'polls': polls},
                              context_instance=RequestContext(request))

def get_poll_data(request):
    xtype = request.GET.get('xtype', '')
    xid = request.GET.get('xid', '')
    if xtype == 'poll':
        response = list(Poll.objects.filter(pk=xid).annotate(Count('responses')).\
        values('id', 'name', 'start_date', 'end_date', 'question', 'default_response', 'responses__count'))
        print response
        response[0]['start_date'] = response[0]['start_date'].\
            strftime('%y-%m-%d') if response[0]['start_date'] else ''
        response[0]['end_date'] = response[0]['end_date'].\
            strftime('%y-%m-%d') if response[0]['end_date'] else ''
    else:
        response = []
    json = simplejson.dumps(response)
    return HttpResponse(json, mimetype='application/json')

