from threading import local

from django.core.cache.backends import memcached

from cachebot.logger import CacheLogDecorator

@CacheLogDecorator
class BaseMemcachedCache(memcached.BaseMemcachedCache):
        
    def _get_memcache_timeout(self, timeout):
        if timeout is None:
            timeout = self.default_timeout
        return timeout
    
    def append(self, key, value, version=None):
        key = self.make_key(key, version=version)
        self._cache.append(key, value)
    
    def prepend(self, key, value, version=None):
        key = self.make_key(key, version=version)
        self._cache.prepend(key, value)
    
    def smart_incr(self, key, delta=1, default=0, **kwargs):
        try:
            return self.incr(key, delta=1)
        except ValueError:
            val = default + delta
            self.add(key, val, **kwargs)
            return val

    def smart_decr(self, key, delta=1, default=0, **kwargs):
        try:
            return self.incr(key, delta=1)
        except ValueError:
            val = default - delta
            self.add(key, val, **kwargs)
            return val
    
    def replace(self, key, value, timeout=0, version=None):
        key = self.make_key(key, version=version)
        return self._cache.replace(key, value, self._get_memcache_timeout(timeout))


class MemcachedCache(BaseMemcachedCache):
    "An implementation of a cache binding using python-memcached"
    def __init__(self, server, params):
        import memcache
        super(MemcachedCache, self).__init__(server, params,
                                             library=memcache,
                                             value_not_found_exception=ValueError)

class PyLibMCCache(BaseMemcachedCache):
    "An implementation of a cache binding using pylibmc"
    def __init__(self, server, params):
        import pylibmc
        self._local = local()
        super(PyLibMCCache, self).__init__(server, params,
                                           library=pylibmc,
                                           value_not_found_exception=pylibmc.NotFound)

    @property
    def _cache(self):
        # PylibMC uses cache options as the 'behaviors' attribute.
        # It also needs to use threadlocals, because some versions of
        # PylibMC don't play well with the GIL.
        client = getattr(self._local, 'client', None)
        if client:
            return client

        client = self._lib.Client(self._servers)
        if self._options:
            client.behaviors = self._options

        self._local.client = client

        return client