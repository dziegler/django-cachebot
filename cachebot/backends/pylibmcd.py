from __future__ import with_statement
from django.core.cache.backends.base import BaseCache
from django.utils.encoding import smart_unicode, smart_str
from django.conf import settings

from cachebot.backends import version_key_decorator
from cachebot.logger import CacheLogger

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
        
    def __init__(self, server, params):
        super(CacheClass, self).__init__(params)
        mc = pylibmc.Client(server.split(';'))
        mc.behaviors = PYLIBMC_BEHAVIORS
        self._pool = pylibmc.ThreadMappedPool(mc)
        self._logger = CacheLogger()

    def _call(self, method, *params):
        with self._pool.reserve() as mc:
            return getattr(mc, method)(*params)

    @version_key_decorator
    def add(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return self._call('add', smart_str(key), value,
                self.default_timeout if timeout is None else timeout)

    @version_key_decorator
    def replace(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return self._call('replace', smart_str(key), value,
                self.default_timeout if timeout is None else timeout)
    
    @version_key_decorator
    def get(self, key, default=None):
        val = self._call('get', smart_str(key))
        if val is None:
            return default
        else:
            if isinstance(val, basestring):
                return smart_unicode(val)
            else:
                return val
    
    @version_key_decorator
    def set(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        self._call('set', smart_str(key), value,
                self.default_timeout if timeout is None else timeout)
            
    @version_key_decorator
    def delete(self, key):
        self._call('delete', smart_str(key))
    
    @version_key_decorator
    def get_many(self, keys):
        if not keys:
            return {}
        return self._call('get_multi', map(smart_str, keys))
    
    @version_key_decorator
    def set_many(self, mapping, timeout=None):
        return self._call('set_multi',
                dict((smart_str(key), val) for key, val in mapping.iteritems()),
                self.default_timeout if timeout is None else timeout)
    
    def close(self, **kwargs):
        self._pool.master.disconnect_all()
    
    @version_key_decorator
    def prepend(self, key, value):
        self._call("prepend", smart_str(key), value)
    
    @version_key_decorator
    def append(self, key, value):
        return self._call("append", smart_str(key), value)
    
    @version_key_decorator
    def incr(self, key, delta=1):
        return self._call('incr', smart_str(key), delta)
    
    @version_key_decorator
    def smart_incr(self, key, delta=1, default=0, timeout=None):
        try:
            return self.incr(key, delta=1)
        except pylibmc.NotFound:
            val = default + delta
            self.add(key, val, timeout=timeout)
            return val
    
    @version_key_decorator
    def decr(self, key, delta=1):
        return self._call('decr', smart_str(key), delta)
    
    @version_key_decorator
    def smart_decr(self, key, delta=1, default=0, timeout=None):
        try:
            return self.incr(key, delta=1)
        except pylibmc.NotFound:
            val = default - delta
            self.add(key, val, timeout=timeout)
            return val
    
    @version_key_decorator
    def delete_many(self, keys):
        self._call('delete_multi', map(smart_str, keys))

    def clear(self):
        self._call('flush_all')
        