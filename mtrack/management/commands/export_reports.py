#!/var/www/env/prod/bin/python
# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extras
import sys
import os
import datetime
import getopt

from tempfile import TemporaryFile
from time import strftime
from xlwt import Workbook

dbname = "mtrack"
dbuser = "postgres"
dbpasswd = "postgres"
dbhost = "dbserver"

cmd = sys.argv[1:]
opts, args = getopt.getopt(cmd, 's:e:o:t:d:l:ha', ['star-date', 'end-date', 'output-file',
            'report-type', 'district', 'district-list', 'all'])

conn = psycopg2.connect("dbname=" + dbname + " host= " + dbhost + " user=" + dbuser + " password=" + dbpasswd)

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#cur = conn.cursor()
def usage():
    return """
usage: python excel_reports.py [-s <start-date>] [-e <end-date>] [-d <district-name>] [-l <district-list>] [-a]
    -a Generate excel for all districts

    -d Generate excel for district passed under this option

    -e start date for report

    -h Show this message

    -l list of districts for which to generate excel exports

    -o output filename

    -t report type e.g. 033b, vht, etc..

    -s end date for report

    Without any options passed, a report is generated for each district
    """

rtype = '033b'
report_keywords_where_clause = {'033b':"keyword IN('cases','deaths','opd','test','treat','act','mal','rdt','rutf','epi','qun') AND ",
                        'vht': "keyword IN ('med','doc', 'com') AND "}
default_kw_clause = "keyword IN('cases','deaths','opd','test','treat','act','mal','rdt','rutf','epi','qun') AND "

#report_names_where clause = {'033b':"name IN('ACT Report','Disease Report','Death Report','ITP/OTP Treatment Report', 'Epi Report', 'OPD report', 'QUN report', 'RDT report', 'OTC/ITC Stock Report', 'TEST report', 'TREAT report') ",
#                            'vht': "name IN('MED Report','DOC Report','VHT Report') "}
default_pre_surfix = ''

sql_2 = ""
district = ""
GEN_ALL = False
for option, parameter in opts:
    if option == '-o':
        fname = "%s" % (parameter)
    if option == '-s':
        sql_2 += "date >= '%s' AND " % (parameter)
    if option == '-e':
        sql_2 += "date <= '%s' AND " % (parameter)
    if option == '-d':
        sql_2 += "district = '%s' AND " % (parameter)
        district = parameter
    if option == '-a':
        GEN_ALL = True
        sql_2 += "district ILIKE '%%' AND "
    if option == '-l':
        district = parameter
    if option == '-t':
        rtype = parameter
    if option == '-h':
        print usage()
        sys.exit(1)

sql_2 += report_keywords_where_clause.get(rtype, default_kw_clause)
sql_2 += " TRUE"
print rtype, sql_2
#sys.exit(1)

#headings = {'slug':['prefered_name', order]}
headings = {'report_id':{'header':'report_id', 'order':0},
            'report': {'header':'report', 'order':1},
            'date': {'header':'date', 'order':2},
            'reporter':{'header':'reporter', 'order':3},
            'reporter_id': {'header':'reporter_id', 'order':4},
            'phone':{'header':'phone', 'order':5},
            'district':{'header':'district', 'order':6},
            'facility':{'header':'facility', 'order':7},
            'village':{'header':'village', 'order':8},
            'valid':{'header':'valid', 'order':9},
            'approved':{'header':'approved', 'order':10},
        }

INITIAL_KEYS = ['report_id', 'report', 'date', 'reporter', 'reporter_id', 'phone',
                'district', 'facility', 'village', 'valid', 'approved']

offset = 10 #excel column offset
if rtype == 'vht':
    headings.pop('approved')
    INITIAL_KEYS.pop(INITIAL_KEYS.index('approved'))
    default_pre_surfix = '_vht'
    offset = 9
KEYS_FOR_VALUES = [] + INITIAL_KEYS
#get all the other headings
cur.execute("SELECT name, description, slug FROM xformfields_view WHERE %s TRUE"%report_keywords_where_clause.get(rtype,
    default_kw_clause))
res = cur.fetchall()
for r in res:
    offset += 1
    d = {}
    d['header'] = '%(name)s:%(description)s' % (r)
    d['order'] = offset
    slug = '%(slug)s' % r
    headings[slug] = d
    if slug not in KEYS_FOR_VALUES:
        KEYS_FOR_VALUES.append(slug)

#preload the data
print "Generating preliminary data....."
cur.execute("SELECT report_id, report, to_char(date, 'yyyy-mm-dd HH24:MI:SS') as date, reporter, reporter_id, phone, district, facility, village, valid, approved FROM xform_submissions_view WHERE %s" % sql_2)
data = cur.fetchall()[:65530]
row_len = len(data)

inner_sql = ("SELECT submission, name, slug, value FROM submissions_values_view")
VALUES_DICT = {}
print "Loading report values........"
cur.execute(inner_sql)
values = cur.fetchall()
for v in values:
    if v['submission'] not in VALUES_DICT:
        VALUES_DICT[v['submission']] = [v]
    else:
        VALUES_DICT[v['submission']].append(v)
print "Finished loading report values........"
#Get all the districts

cur.execute("SELECT name from locations_location WHERE type_id = 'district' ORDER BY name")
res = cur.fetchall()
if district:
    #with this you can pass comma separated districts
    res = [{'name':d} for d in district.split(',')]
    #res = [{'name':district}]
if GEN_ALL:
    district = "all"
    res = [{'name':'all'}]

for r in res:
    district = r['name']
    print "start generating for %s" % ('all districts' if district == 'all' else district)
    book = Workbook(encoding='utf-8')
    sheet1 = book.add_sheet('Sheet 1')

    headers_len = len(KEYS_FOR_VALUES)
    intial_headers_len = len(INITIAL_KEYS)
    i = 0
    for k in KEYS_FOR_VALUES:
        sheet1.write(0, i, headings[k]['header'])
        sheet1.col(i).width = 4050
        i += 1

    s = 0
    for i in xrange(row_len):
        #continue immediately if not for the required district
        if GEN_ALL:
            pass
        else:
            if data[i]['district'] <> district:
                continue
        s += 1
        row = sheet1.row(s)
        #print data[i]
        for k in xrange(intial_headers_len):
            row.write(k, data[i][k])
        report_id = data[i]['report_id']
        if report_id in VALUES_DICT:
            for val in VALUES_DICT[data[i]['report_id']]:
                #print val[0]
                #print val
                idx = KEYS_FOR_VALUES.index(val[2])
                row.write(idx, '%s' % val[3])
    print "Done with Everything for %s........." % ('all districts' if district == 'all' else district)

    sheet1.flush_row_data()
    #fname = "mtrack-"+datetime.date.today().strftime('%Y%m%d')+"-"+strftime('%H%M%S')+".xls"
    if district == 'all':
        fname = "reports%s.xls" % default_pre_surfix
    else:
        fname = "reports%s_%s.xls" % (default_pre_surfix,district)
    fpath = "/var/www/prod/mtrack/mtrack_project/rapidsms_mtrack/mtrack/static/spreadsheets/" + fname
    #fpath = "/tmp/"+fname
    book.save(fpath)
#now close connection
conn.close()
