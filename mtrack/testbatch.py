# quick util script for batching up anonymous reports (not used anywhere else in the production)
from .models import AnonymousReport
from rapidsms_httprouter.models import Message
import datetime

hour_range = [i+1 for i in range(10*24)]
end_epoch = datetime.datetime.now()
get_all = []
for hour in hour_range:
    try:
        # go through all messages (inbound through Yo8200
        messagi = Message.objects.filter(connection__backend__name="yo8200", direction="I",
            date__range=[end_epoch-datetime.timedelta(hours=hour),end_epoch])
        get_all.append(ars)
    except IndexError:
        pass
