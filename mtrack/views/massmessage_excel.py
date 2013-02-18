import datetime
import os
from django.conf import settings
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse
import xlwt
from contact.models import MassText
from mtrack.decorators import login_required
from uganda_common.utils import get_location_for_user

ezxf = xlwt.easyxf

__author__ = 'kenneth'


def _all_mass_messages(request):
    location = get_location_for_user(request.user)
    messages = MassText.objects.filter(
        contacts__reporting_location__in=location.get_descendants(include_self=True))
    return messages


def _all_mass_messages_sender(request):
    messages = _all_mass_messages(request)
    return messages.values_list('user__username', flat=True).distinct()


def _all_mass_messages_by_sender(request, user, date_range=None):
    messages = _all_mass_messages(request).filter(user__username=user)
    if date_range:
        messages = _all_mass_messages(request).filter(user__username=user, date__range=date_range)
    return messages.count()


def write_xls(file_name, sheet_name, headings, data, heading_xf, data_xfs):
    book = xlwt.Workbook()
    sheet = book.add_sheet(sheet_name)
    rowx = 0
    for colx, value in enumerate(headings):
        sheet.write(rowx, colx, value, heading_xf)
    sheet.set_panes_frozen(True) # frozen headings instead of split panes
    sheet.set_horz_split_pos(rowx + 1) # in general, freeze after last heading row
    sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
    for row in data:
        rowx += 1
        for colx, value in enumerate(row):
            sheet.write(rowx, colx, value, data_xfs[colx])
    book.save(file_name)

@login_required
def create_report(request):
    d = datetime.datetime.now()
    current_month = d - datetime.timedelta(days=30)
    last_six_months = d - datetime.timedelta(days=30 * 6)
    heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center')
    hdngs = ['User Login Name', 'Number of Messages sent', 'Number of Messages Sent In Current Month',
             'Number of Messages Sent in Last Six Months']
    data = [[user, _all_mass_messages_by_sender(request, user),
             _all_mass_messages_by_sender(request, user, date_range=[current_month, d]),
             _all_mass_messages_by_sender(request, user, date_range=[last_six_months, d])] for user in
            _all_mass_messages_sender(request)]

    kinds = 'text    int          int         int'.split()

    kind_to_xf_map = {
        'date': ezxf(num_format_str='yyyy-mm-dd'),
        'int': ezxf(num_format_str='#,##0'),
        'text': ezxf(),
    }

    data_xfs = [kind_to_xf_map[k] for k in kinds]
    write_path = os.path.join(os.path.join(os.path.join(os.path.join(settings.MTRACK_ROOT, 'mtrack'),
                                                        'static'), 'spreadsheets'),
                              '%s_mass_messages.xls' % request.user.username)

    write_xls(write_path, 'Report', hdngs, data, heading_xf, data_xfs)
    response = HttpResponse(FileWrapper(open(write_path)), content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=%s_mass_messages.xls'% request.user.username
    return response