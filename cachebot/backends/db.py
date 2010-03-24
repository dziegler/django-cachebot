"Database cache backend."

from django.core.cache.backends import db
from django.db import connection, transaction

from cachebot.backends import version_key_decorator
from cachebot.logger import CacheLogger


class CacheClass(db.CacheClass):
    
    def __init__(self, *args, **kwargs):
        super(CacheClass, self).__init__(*args, **kwargs)
        self._logger = CacheLogger()
    
    @version_key_decorator
    def add(self, *args, **kwargs):
        return super(CacheClass, self).add(*args, **kwargs)
    
    @version_key_decorator
    def get(self, *args, **kwargs):
        return super(CacheClass, self).get(*args, **kwargs)
    
    @version_key_decorator
    def set(self, *args, **kwargs):
        return super(CacheClass, self).set(*args, **kwargs)
    
    @version_key_decorator
    def delete(self, *args, **kwargs):
        return super(CacheClass, self).delete(*args, **kwargs)
    
    @version_key_decorator
    def get_many(self, *args, **kwargs):
        return super(CacheClass, self).get_many(*args, **kwargs)
    
    @version_key_decorator
    def set_many(self, *args, **kwargs):
        return super(CacheClass, self).set_many(*args, **kwargs)
    
    @version_key_decorator
    def incr(self, *args, **kwargs):
        return super(CacheClass, self).incr(*args, **kwargs)
    
    @version_key_decorator
    def decr(self, *args, **kwargs):
        return super(CacheClass, self).decr(*args, **kwargs)
    
    # not atomic...should not use this in production
    
    @transaction.commit_on_success
    def prepend(self, key, value):
        self.set(key, value + self.get(key))
    
    @transaction.commit_on_success
    def append(self, key, value):
        self.set(key, self.get(key) + value)
    
    # multi operations, not in 1.1 yet, but are in 1.2
    
    @version_key_decorator
    def set_many(self, data, timeout=0):
        for key, value in data.items(): 
            self.set(key, value, timeout) 
            
    @version_key_decorator
    def delete_many(self, keys):
        for key in keys: 
            self.delete(key) 

    def clear(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM %s' % self._table)
    
    def close(self, **kwargs):
        pass
    
    