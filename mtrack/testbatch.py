from .models import AnonymousReportBatch, AnonymousReport
import datetime

hour_range = [i+1 for i in range(10*24)]
end_epoch = datetime.datetime.now()
get_all = []
for hour in hour_range:
    try:
        ars = AnonymousReport.objects.filter(date__range=[end_epoch-datetime.timedelta(hours=hour), end_epoch])
        get_all.append(ars)
    except IndexError:
        pass

if AnonymousReportBatch.objects.filter(date__range=[start_epoch, end_epoch], connection__in=Connection.objects.filter(id=message.connection.id)).exists():

all_areports = AnonymousReport.objects.all()
d = datetime.datetime.now() - datetime.timedelta(hours=1)