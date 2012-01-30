from django.template import RequestContext
from django.shortcuts import render_to_response
from django.conf import settings
from django.db.models import Count
from geoserver.models import BasicClassLayer
from mtrack.utils import last_reporting_period_number

def stock_level_viz(request):
    dict = {
            'geoserver_url':getattr(settings, 'GEOSERVER_URL', 'http://localhost/geoserver/'),
            'week':last_reporting_period_number(),
        }
    return render_to_response('mtrack/partials/viz/stock_levels_map.html',
                              dict,
                              context_instance=RequestContext(request))

def stock_level_piechart(request):
    num = BasicClassLayer.objects.using('geoserver').all().count()
    b = BasicClassLayer.objects.using('geoserver').values('style_class').order_by().annotate(Count('style_class'))
    z = dict([(x['style_class'], float('%.2f' % ((x['style_class__count'] / (num + 0.0)) * 100))) for x in b])
    [z.setdefault(i, 0) for i in ['red', 'green', 'yellow', 'nodata']]

    response_dict = {
            'series':z,
            'title':'Health Facility Stock Levels',
        }
    return render_to_response('mtrack/partials/viz/stock_levels_pchart.html',
                              {'response_dict':response_dict},
                              context_instance=RequestContext(request))
