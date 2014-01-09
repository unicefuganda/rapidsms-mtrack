import xlwt
import datetime
from time import strftime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from mtrack.utils import write_xls
from poll.models import Poll


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
    response["Content-Disposition"] = 'attachment; filename=%s_%s.xls' % (fname_prefix, poll.name)
    book.save(response)
    return response
