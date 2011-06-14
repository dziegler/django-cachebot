"Dummy cache backend"

from django.core.cache.backends import dummy

from cachebot.logger import CacheLogDecorator

@CacheLogDecorator
class DummyCache(dummy.DummyCache):

    def replace(self, **kwargs):
        pass
        
    def smart_incr(self, **kwargs):
        pass
    
    def smart_decr(self, **kwargs):
        pass