from django.core.cache.backends import memcached
from django.core.cache.backends.base import InvalidCacheBackendError
from django.conf import settings
from django.utils.encoding import smart_unicode, smart_str

from cache_utils.backends import version_key_decorator, version_key

try:
    import cmemcache as memcache
except ImportError:
    try:
        import memcache
    except:
        raise InvalidCacheBackendError("libmemcached backend requires either the 'python-memcached' or 'cmemcached' library")

class CacheClass(memcached.CacheClass):

    @version_key_decorator
    def add(self, key, value, timeout=0):
        return super(CacheClass,self).add(key, value, timeout=timeout)
    
    @version_key_decorator
    def get(self, key, default=None):
        return super(CacheClass,self).get(key, default=default)
    
    @version_key_decorator
    def set(self, key, value, timeout=0):
        return super(CacheClass,self).set(key, value, timeout=timeout)

    @version_key_decorator
    def delete(self, key):
        return super(CacheClass,self).delete(key)
     
    @version_key_decorator   
    def get_many(self, keys):
        return super(CacheClass,self).get_many(keys)

    @version_key_decorator
    def incr(self, key, delta=1):
        return super(CacheClass,self).incr(key, delta=delta)

    @version_key_decorator
    def decr(self, key, delta=1):
        return super(CacheClass,self).decr(key, delta=delta)

    # multi operations, not in 1.1 yet, but are in 1.2

    def set_many(self, data, timeout=0):
        safe_data = {}
        for key, value in data.items():
            key = version_key(key)
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            safe_data[smart_str(key)] = value
        self._cache.set_multi(safe_data, timeout or self.default_timeout)

    @version_key_decorator
    def delete_many(self, keys):
        self._cache.delete_multi(map(smart_str, keys))

    def clear(self):
        self._cache.flush_all()
