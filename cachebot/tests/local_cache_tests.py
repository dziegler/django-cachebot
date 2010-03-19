from django.core.cache import cache
from django.conf import settings
from cachebot.tests.base_tests import BaseTestCase
from cachebot.localstore import local
from cachebot.backends import version_key

class LocalCacheTests(BaseTestCase):
    
    def setUp(self):
        super(LocalCacheTests, self).setUp()
        settings.DEBUG = True
        cache.clear()
        self._clear_local_cache()
    
    def _clear_local_cache(self):
        local.clear()
        cache._logger.reset()
        self.assertEquals(len(cache._logger.log), 0)
    
    def test_add(self):
        self.assertEquals(local.get(version_key("hello")), None)
        cache.add("hello","world")
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(local.get(version_key("hello")), "world")
        cache.add("hello","world")
        self.assertEquals(local.get(version_key("hello")), "world")
        self.assertEquals(len(cache._logger.log), 2)
    
    def test_get(self):
        cache.set("hello","world",30)
        self._clear_local_cache()

        self.assertEquals(local.get(version_key("hello")), None)
        self.assertEquals(cache.get("hello"),"world")
        self.assertEquals(local.get(version_key("hello")), "world")
        
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get("hello"),"world")
        self.assertEquals(len(cache._logger.log), 1)

    def test_set(self):
        cache.set("hello","world",30)
        self.assertEquals(len(cache._logger.log), 1)
        cache.set("hello","world",30)
        self.assertEquals(len(cache._logger.log), 2)
        self.assertEquals(cache.get("hello"),"world")
        self.assertEquals(len(cache._logger.log), 2)

    def test_delete(self):
        cache.set("hello","world",30)
        self._clear_local_cache()        
        cache.delete("hello")
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get("hello"),None)
        self.assertEquals(len(cache._logger.log), 2)
    
    def test_get_many(self):
        cache.set("hello1","world1",30)
        cache.set("hello2","world2",30)
        self._clear_local_cache()
        
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):'world1',version_key('hello2'):'world2'})
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):'world1',version_key('hello2'):'world2'})
        self.assertEquals(len(cache._logger.log), 1)
    
    
    def test_delete_many(self):
        cache.set_many({'hello1':'world1','hello2':'world2'},30)
        self._clear_local_cache()
        
        cache.delete_many(['hello1','hello2'])
        self.assertEquals(len(cache._logger.log), 1)
        cache.delete_many(['hello1','hello2'])
        self.assertEquals(len(cache._logger.log), 2)
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):None,version_key('hello2'):None})
        self.assertEquals(len(cache._logger.log), 3)
    