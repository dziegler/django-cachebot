import logging
import os
from time import time

from django.template import Template, Context
from django.utils.translation import ugettext as _

try:
    from cloghandler import ConcurrentRotatingFileHandler as RFHandler
except ImportError:
    from warnings import warn
    warn("ConcurrentLogHandler package not installed.  Using builtin log handler")
    from logging.handlers import RotatingFileHandler as RFHandler

from cachebot import CACHEBOT_LOG

log_handler = RFHandler(CACHEBOT_LOG, "a", 512*1024, 10)
cachebot_log = logging.getLogger('cachebot')
cachebot_log.addFilter(logging.Filter('cachebot'))
cachebot_log.setLevel(logging.DEBUG)
cachebot_log.addHandler(log_handler)

class CacheLogger(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.log = []

cache_log = CacheLogger()


class CacheLogInstance(object):

    def __init__(self, name, key):
        self.name = name
        self.key = key
    
    def __repr__(self):
        return ' - '.join((self.name, str(self.key)))

def logged_func(func):
    def inner(instance, key, *args, **kwargs):
        instance._logger.log.append(CacheLogInstance(func.func_name, key))
        t = time()

        val = func(instance, key, *args, **kwargs)

        instance._logger.log[-1].time = 1000 * (time() - t)
        if func.func_name == 'get':
            instance._logger.log[-1].hit = val != args[0]
        elif func.func_name == 'get_many':
            instance._logger.log[-1].hit = bool(val)
        
        logging.getLogger("cachebot").debug(instance._logger.log[-1])

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
            # Aggregate stats.
            stats = {'hit': 0, 'miss': 0, 'time': 0}
            for log in cache_log.log:
                if hasattr(log, 'hit'):
                    stats[log.hit and 'hit' or 'miss'] += 1
                stats['time'] += log.time

            # No ngettext, too many combos!
            stats['time'] = round(stats['time'], 2)
            return _('%(hit)s hits, %(miss)s misses in %(time)sms') % stats

        def content(self):
            context = {'logs': cache_log.log}
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