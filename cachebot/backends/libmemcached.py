from django.core.cache.backends.base import InvalidCacheBackendError
from django.conf import settings
from django.utils.encoding import smart_unicode, smart_str

from cache_utils.backends import memcached

try:
    import cmemcached as memcache
except ImportError:
    try:
        import memcache
    except:
        raise InvalidCacheBackendError("libmemcached backend requires either the 'python-memcached' or 'python-libmemcached' library")

class CacheClass(memcached.CacheClass):
    def __init__(self, server, params):
        super(memcached.CacheClass, self).__init__(server, params)
        self._cache = memcache.Client(server.split(';'))
    
    # python-libmemcached doesn't support set_multi
    def set_many(self, data, timeout=0):
        for key, value in data.items():
            key = version_key(key)
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            self.set(smart_str(key), value, timeout or self.default_timeout)
