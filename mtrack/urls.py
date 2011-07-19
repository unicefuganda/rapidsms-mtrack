from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^facility/(?P<code>\w+)/config/?$',
       'mtrack.views.facility_detail',
       name='facility_detail'), 
)