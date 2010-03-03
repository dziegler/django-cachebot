"Database cache backend."

from django.core.cache.backends import db
from django.db import connection

from cachebot.backends import version_key_decorator, version_key


class CacheClass(db.CacheClass):
    
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
        for key, value in data.items(): 
            key = version_key(key)
            self.set(key, value, timeout) 

    @version_key_decorator
    def delete_many(self, keys):
        for key in keys: 
            self.delete(key) 

    def clear(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM %s' % self._table)

