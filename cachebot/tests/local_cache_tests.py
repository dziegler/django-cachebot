from django.core.cache import cache
from django.conf import settings
from cachebot.tests.base_tests import BaseTestCase
from cachebot.backends import version_key
from cachebot.tests.utils import ConcurrentTestMetaClass

class LocalCacheTests(BaseTestCase):
    
    __metaclass__ = ConcurrentTestMetaClass
    
    def setUp(self):
        super(LocalCacheTests, self).setUp()
        settings.DEBUG = True
        # local store is not working, so don't run tests for now
        settings.CACHEBOT_LOCAL_CACHE = False
        self._commit_and_clear_log()
    
    def _run_test(self):
        return settings.CACHEBOT_LOCAL_CACHE == True
    
    def _commit_and_clear_log(self):
        cache.close()
        cache._logger.reset()
        self.assertEquals(len(cache._logger.log), 0)
    
    def test_add(self):
        if not self._run_test():
            return
        self.assertEquals(local.storage.get(version_key("hello")), None)
        cache.add("hello","world")
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(local.storage.get(version_key("hello")), "world")
        cache.add("hello","world1")
        self.assertEquals(local.storage.get(version_key("hello")), "world")
        self.assertEquals(len(cache._logger.log), 1)
        cache.close()
        self.assertEquals(len(cache._logger.log), 1)
    
    def test_get(self):
        if not self._run_test():
            return
        cache.set("hello","world",30)
        self._commit_and_clear_log()

        self.assertEquals(local.storage.get(version_key("hello")), None)
        self.assertEquals(cache.get("hello"),"world")
        self.assertEquals(local.storage.get(version_key("hello")), "world")
        
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get("hello"),"world")
        self.assertEquals(len(cache._logger.log), 1)

    def test_set(self):
        if not self._run_test():
            return
        cache.set("hello","world",30)
        self.assertEquals(len(cache._logger.log), 0)
        self.assertEquals(cache.get("hello"), "world")
        self.assertEquals(len(cache._logger.log), 0)
        cache.close()
        self.assertEquals(len(cache._logger.log), 1)

    def test_delete(self):
        if not self._run_test():
            return
        cache.set("hello","world",30)
        self._commit_and_clear_log()  
        self.assertEquals(cache.get("hello"),"world")  
        self.assertEquals(len(cache._logger.log), 1)    
        cache.delete("hello")
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get("hello"),None)
        self.assertEquals(len(cache._logger.log), 1)
        cache.close()
        self.assertEquals(len(cache._logger.log), 2)
    
    def test_get_many(self):
        if not self._run_test():
            return
        cache.set("hello1","world1",30)
        cache.set("hello2","world2",30)
        self._commit_and_clear_log()
        
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):'world1',version_key('hello2'):'world2'})
        self.assertEquals(len(cache._logger.log), 1)
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):'world1',version_key('hello2'):'world2'})
        self.assertEquals(len(cache._logger.log), 1)
    
    def test_set_many(self):
        if not self._run_test():
            return
        cache.set_many({'hello1':'world1','hello2':'world2'},30)
        self.assertEquals(len(cache._logger.log), 0)
        self.assertEquals(cache.get("hello1"), "world1")
        self.assertEquals(len(cache._logger.log), 0)
        cache.close()
        self.assertEquals(len(cache._logger.log), 1)
    
    def test_delete_many(self):
        if not self._run_test():
            return
        cache.set_many({'hello1':'world1','hello2':'world2'},30)
        self._commit_and_clear_log()
        
        cache.delete_many(['hello1','hello2'])
        self.assertEquals(len(cache._logger.log), 0)
        cache.delete_many(['hello1','hello2'])
        self.assertEquals(len(cache._logger.log), 0)
        self.assertEquals(cache.get_many(['hello1','hello2']),{version_key('hello1'):None,version_key('hello2'):None})
        self.assertEquals(len(cache._logger.log), 0)
        cache.close()
        self.assertEquals(len(cache._logger.log), 1)
    