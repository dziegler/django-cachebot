"Dummy cache backend"

from django.core.cache.backends import dummy
from cachebot.logger import CacheLogger

class CacheClass(dummy.CacheClass):

    def __init__(self, *args, **kwargs):
        super(CacheClass, self).__init__(*args, **kwargs)
        self._logger = CacheLogger()
        
    # multi operations, not in 1.1 yet, but are in 1.2

    def set_many(self, *args, **kwargs):
        pass

    def delete_many(self, *args, **kwargs): 
        pass

    def clear(self): 
        pass
    
    def append(self, *args, **kwargs):
        pass
    
    def prepend(self, *args, **kwargs):
        pass
    
    def close(self, **kwargs):
        pass
    
    def smart_incr(self, **kwargs):
        pass
    
    def smart_decr(self, **kwargs):
        pass