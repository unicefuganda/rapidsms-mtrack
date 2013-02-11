from datetime import date, timedelta
from optparse import make_option
from django.core.management import BaseCommand
from rapidsms_httprouter.models import Message
from rapidsms_httprouter.router import get_router

class Command(BaseCommand):


    option_list = BaseCommand.option_list + (
        make_option('-f', '--f', dest='f'),
        make_option('-d','--date',dest='date'),
        )

    def handle(self, **options):
        router=get_router()
        if not options['f']:
            print 'Log file not found'
            print "provide log file to parse eg --f=path/to/file"
            return
        file = options['f']
        log=open(file)
        lines=log.readlines()
        start_date = date.today() - timedelta(1) if not options['date'] else date(int(options['date'][4:8]),int(options['date'][2:4]),int(options['date'][0:2]))
        try:
            for line in lines:
                r = line.split(']')[1].split('?')[1].split()[0]
                b = r.split('&')[1].split('=')[1]
                s = r.split('&')[2].split('=')[1].replace('%2B','')
                m = r.split('&')[3].split('=')[1]
                if not Message.objects.filter(direction="I",text=m,connection__identity=s,date__gte=start_date):
                    router.handle_incoming(b,s,m)
                    print b,s,m
        except Exception, e:
            print 'Error:', str(e)
