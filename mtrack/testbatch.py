# quick util script for batching up anonymous reports (not used anywhere else in the production)
from .models import AnonymousReport
from rapidsms_httprouter.models import Message
import datetime

hour_range = [i+1 for i in range(10*24)]
end_epoch = datetime.datetime.now()
get_all = []
messagi = Message.objects.filter(connection__backend__name="yo8200", direction="I")
for msg in messagi:
    ar = AnonymousReport.objects.create(date=msg.date, connection=msg.connection)
    ar.message.add(msg)
    ar.save()
