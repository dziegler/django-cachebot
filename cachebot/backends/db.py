"Database cache backend."

from django.core.cache.backends import db
from django.db import connection, transaction

from cachebot.backends import CachebotBackendMeta, version_key


class CacheClass(db.CacheClass):
    __metaclass__ = CachebotBackendMeta
    
    # multi operations, not in 1.1 yet, but are in 1.2

    def set_many(self, data, timeout=0):
        for key, value in data.items(): 
            key = version_key(key)
            self.set(key, value, timeout) 

    def delete_many(self, keys):
        for key in keys: 
            self.delete(key) 

    def clear(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM %s' % self._table)
    
    # not atomic...should not use this in production
    
    @transaction.commit_on_success
    def prepend(self, key, value):
        self.set(key, value + self.get(key))
    
    @transaction.commit_on_success
    def append(self, key, value):
        self.set(key, self.get(key) + value)