from django.core.cache.backends import memcached
from django.core.cache.backends.base import InvalidCacheBackendError
from django.utils.encoding import smart_str

from cachebot.backends import version_key_decorator
from cachebot.logger import CacheLogger

try:
    import cmemcache as memcache
except ImportError:
    try:
        import memcache
    except:
        raise InvalidCacheBackendError("libmemcached backend requires either the 'python-memcached' or 'cmemcached' library")

class CacheClass(memcached.CacheClass):
    
    def __init__(self, *args, **kwargs):
        super(CacheClass, self).__init__(*args, **kwargs)
        self._logger = CacheLogger()

    @version_key_decorator
    def add(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if timeout is None:
            timeout = self.default_timeout
        return self._cache.add(smart_str(key), value, timeout)
    
    @version_key_decorator
    def get(self, *args, **kwargs):
        return super(CacheClass, self).get(*args, **kwargs)
    
    @version_key_decorator
    def set(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if timeout is None:
            timeout = self.default_timeout
        return self._cache.set(smart_str(key), value, timeout)
    
    @version_key_decorator
    def delete(self, *args, **kwargs):
        return super(CacheClass, self).delete(*args, **kwargs)
    
    @version_key_decorator
    def get_many(self, *args, **kwargs):
        return super(CacheClass, self).get_many(*args, **kwargs)
    
    @version_key_decorator
    def incr(self, *args, **kwargs):
        return super(CacheClass, self).incr(*args, **kwargs)
    
    @version_key_decorator
    def smart_incr(self, key, delta=1, default=0, timeout=None):
        try:
            return self.incr(key, delta=1)
        except ValueError:
            val = default + delta
            self.add(key, val, timeout=timeout)
            return val
    
    @version_key_decorator
    def decr(self, *args, **kwargs):
        return super(CacheClass, self).decr(*args, **kwargs)
    
    @version_key_decorator
    def smart_decr(self, key, delta=1, default=0, timeout=None):
        try:
            return self.incr(key, delta=1)
        except ValueError:
            val = default - delta
            self.add(key, val, timeout=timeout)
            return val
    
    @version_key_decorator
    def prepend(self, key, value):
        return self._cache.prepend(smart_str(key), value)
    
    @version_key_decorator
    def append(self, key, value):
        return self._cache.append(smart_str(key), value)
    
    @version_key_decorator
    def replace(self, key, value, timeout=None):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if timeout is None:
            timeout = self.default_timeout
        return self._cache.replace(smart_str(key), value, timeout)
        
    # multi operations, not in 1.1 yet, but are in 1.2
    
    @version_key_decorator
    def set_many(self, data, timeout=None):
        safe_data = {}
        for key, value in data.items():
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            safe_data[smart_str(key)] = value
        if timeout is None:
            timeout = self.default_timeout
        self._cache.set_multi(safe_data, timeout)
    
    @version_key_decorator
    def delete_many(self, keys):
        self._cache.delete_multi(map(smart_str, keys))

    def clear(self):
        self._cache.flush_all()
    
    
