from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings

def stock_level_viz(request):
    dict = {
            'geoserver_url':getattr(settings, 'GEOSERVER_URL', 'http://localhost/geoserver/'),
        }
    return render_to_response('mtrack/partials/viz/stock_levels_map.html',
                              dict,
                              context_instance=RequestContext(request));
