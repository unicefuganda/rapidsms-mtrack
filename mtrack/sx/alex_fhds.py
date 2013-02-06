import datetime
import xlwt
from healthmodels.models import HealthProvider
ezxf = xlwt.easyxf

FHDS = HealthProvider.objects.filter(groups__name__iexact='fhd')

def write_xls(file_name, sheet_name, headings, data, heading_xf, data_xfs):
    book = xlwt.Workbook()
    sheet = book.add_sheet(sheet_name)
    rowx = 0
    for colx, value in enumerate(headings):
        sheet.write(rowx, colx, value, heading_xf)
    sheet.set_panes_frozen(True) # frozen headings instead of split panes
    sheet.set_horz_split_pos(rowx+1) # in general, freeze after last heading row
    sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
    for row in data:
        rowx += 1
        for colx, value in enumerate(row):
            sheet.write(rowx, colx, value, data_xfs[colx])
    book.save(file_name)


def create_report():
    mkd = datetime.date
    heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center')
    hdngs = ['Name', 'Phone', 'Last Reporting date', 'Number of Reports', 'Facility', 'District']
    data = [[h.name,h.phone,h.last_reporting_date,h.xformsubmissionextras_set.count(),str(h.facility),
             str(h.facility.district)] for h in FHDS if h.facility and h.contact_ptr.is_active]

    kinds =  'text    text          date         text         text    text'.split()

    kind_to_xf_map = {
        'date': ezxf(num_format_str='yyyy-mm-dd'),
        'int': ezxf(num_format_str='#,##0'),
        'text': ezxf(),
        }

    data_xfs = [kind_to_xf_map[k] for k in kinds]
    write_xls('report.xls', 'Report', hdngs, data, heading_xf, data_xfs)