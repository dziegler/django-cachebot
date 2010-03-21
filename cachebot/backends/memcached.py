from django.core.cache.backends import memcached
from django.core.cache.backends.base import InvalidCacheBackendError
from django.conf import settings
from django.utils.encoding import smart_unicode, smart_str

from cachebot.backends import CachebotBackendMeta

try:
    import cmemcache as memcache
except ImportError:
    try:
        import memcache
    except:
        raise InvalidCacheBackendError("libmemcached backend requires either the 'python-memcached' or 'cmemcached' library")

class CacheClass(memcached.CacheClass):

    __metaclass__ = CachebotBackendMeta
    
    # multi operations, not in 1.1 yet, but are in 1.2

    def set_many(self, data, timeout=0):
        safe_data = {}
        for key, value in data.items():
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            safe_data[smart_str(key)] = value
        self._cache.set_multi(safe_data, timeout or self.default_timeout)

    def delete_many(self, keys):
        self._cache.delete_multi(map(smart_str, keys))

    def clear(self):
        self._cache.flush_all()
    
    def prepend(self, key, value):
        self._cache.prepend(smart_str(key), value)
    
    def append(self, key, value):
        self._cache.append(smart_str(key), value)
