"Dummy cache backend"

from django.core.cache.backends import dummy

class CacheClass(dummy.CacheClass):

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