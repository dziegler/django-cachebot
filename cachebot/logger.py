import logging
import threading
from time import time

from django.template import Template, Context
from django.utils.translation import ugettext as _

from cachebot import conf

cachebot_log = logging.getLogger(__name__)

LOG_FUNCS = ('append', 'prepend', 'replace', 'add', 'get', 'set', 'delete', 'get_many', 'incr', 'set_many', 'delete_many')

def CacheLogDecorator(klass):
    orig_init = klass.__init__
    
    def __init__(self, *args, **kwargs):
        self._logger = CacheLogger()
        orig_init(self, *args, **kwargs)
    
    if conf.CACHEBOT_ENABLE_LOG:
        for func in LOG_FUNCS:
            setattr(klass, func, logged_func(getattr(klass, func)))
    
    klass.__init__ = __init__
    return klass
    
class CacheLogger(threading.local):

    def __init__(self):
        self.reset()

    def reset(self, **kwargs):
        self.log = []


class CacheLogInstance(object):

    def __init__(self, name, key, end, hit=None):
        self.name = name
        self.key = key
        self.time = end
        self.hit = hit
    
    def __repr__(self):
        return ' - '.join((self.name, str(self.key)))
    
def logged_func(func):
    def inner(instance, key, *args, **kwargs):
        t = time()
        val = func(instance, key, *args, **kwargs)
        
        if conf.CACHEBOT_ENABLE_LOG:
            end = 1000 * (time() - t)
            hit = None
            if func.func_name == 'get':
                hit = val != None
            elif func.func_name == 'get_many':
                hit = bool(val)
            log = CacheLogInstance(func.func_name, key, end, hit=hit)
            instance._logger.log.append(log)
            cachebot_log.debug(str(log))

        return val
    return inner

try:
    from debug_toolbar.panels import DebugPanel
    
    class CachePanel(DebugPanel):

        name = 'Cache'
        has_content = True

        def nav_title(self):
            return _('Cache')

        def title(self):
            return _('Cache Queries')

        def nav_subtitle(self):
            from django.core.cache import cache
            # Aggregate stats.
            stats = {'hit': 0, 'miss': 0, 'time': 0}
            for log in cache._logger.log:
                if hasattr(log, 'hit'):
                    stats[log.hit and 'hit' or 'miss'] += 1
                stats['time'] += log.time

            # No ngettext, too many combos!
            stats['time'] = round(stats['time'], 2)
            return _('%(hit)s hits, %(miss)s misses in %(time)sms') % stats

        def content(self):
            from django.core.cache import cache
            context = {'logs': cache._logger.log}
            return Template(template).render(Context(context))

        def url(self):
            return ''

        def process_request(self, request):
            from django.core.cache import cache
            cache._logger.reset()
            


    template = """
    <style type="text/css">
      #djDebugCacheTable tr.hit.djDebugOdd { background-color: #d7f3bc; }
      #djDebugCacheTable tr.hit.djDebugEven { background-color: #c7fcd3; }
    </style>
    <table id="djDebugCacheTable">
      <thead>
        <tr>
          <th>{{ _('Time (ms)') }}</th>
          <th>{{ _('Method') }}</th>
          <th>{{ _('Key') }}</th>
        </tr>
      </thead>
      <tbody>
        {% for log in logs %}
          {% if log.hit %}
          <tr class="hit {% cycle 'djDebugOdd' 'djDebugEven' %}">
          {% else %}
          <tr class="{% cycle 'djDebugOdd' 'djDebugEven' %}">
          {% endif %}
            <td>{{ log.time|floatformat:"2" }}</td>
            <td class="{{ log.name }} method">{{ log.name }}</td>
            <td>{{ log.key }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    """
except ImportError:
    pass
