"Dummy cache backend"

from django.core.cache.backends import dummy

from cachebot.logger import CacheLogDecorator

@CacheLogDecorator
class DummyCache(dummy.DummyCache):
    
    def append(self, **kwargs):
        pass
    
    def prepend(self, **kwargs):
        pass

    def replace(self, **kwargs):
        pass
        
    def smart_incr(self, **kwargs):
        pass
    
    def smart_decr(self, **kwargs):
        pass