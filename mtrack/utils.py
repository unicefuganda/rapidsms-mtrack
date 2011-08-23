from rapidsms_httprouter.models import Message

def get_dashboard_messages(request=None):
    # FIXME: implement full functionality
    return Message.objects.filter(direction='I')
