from __future__ import with_statement
from django.core.cache.backends.base import BaseCache
from django.utils.encoding import smart_unicode, smart_str
from django.conf import settings
from cachebot.backends import CachebotBackendMeta, version_key

import pylibmc

PYLIBMC_BEHAVIORS = getattr(settings, 'PYLIBMC_BEHAVIORS', {
                        "cache_lookups": True, 
                        "no_block": False,
                        "tcp_nodelay": True
                        })

class CacheClass(BaseCache):
    """
    Stole this from http://gist.github.com/334682
    """
    
    __metaclass__ = CachebotBackendMeta
    
    def __init__(self, server, params):
        super(CacheClass, self).__init__(params)
        mc = pylibmc.Client(server.split(';'))
        mc.behaviors = PYLIBMC_BEHAVIORS
        self._pool = pylibmc.ThreadMappedPool(mc)

    def _call(self, method, *params):
        with self._pool.reserve() as mc:
            return getattr(mc, method)(*params)

    def add(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return self._call('add', smart_str(key), value,
                self.default_timeout if timeout is None else timeout)

    def get(self, key, default=None):
        val = self._call('get', smart_str(key))
        if val is None:
            return default
        else:
            if isinstance(val, basestring):
                return smart_unicode(val)
            else:
                return val

    def set(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        self._call('set', smart_str(key), value,
                self.default_timeout if timeout is None else timeout)

    def delete(self, key):
        self._call('delete', smart_str(key))

    def get_many(self, keys):
        if not keys:
            return {}
        return self._call('get_multi', map(smart_str, keys))

    def set_many(self, mapping, timeout=None):
        return self._call('set_multi',
                dict((smart_str(version_key(key)), val) for key, val in mapping.iteritems()),
                self.default_timeout if timeout is None else timeout)
    
    def close(self, **kwargs):
        self._pool.master.disconnect_all()

    def incr(self, key, delta=1):
        return self._call('incr', smart_str(key), delta)

    def decr(self, key, delta=1):
        return self._call('decr', smart_str(key), delta)
     
    def delete_many(self, keys):
        self._call('delete_multi', map(smart_str, keys))

    def clear(self):
        self._call('flush_all')
        