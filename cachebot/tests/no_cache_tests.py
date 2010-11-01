from cachebot import conf
from cachebot.models import FirstModel, NoCacheModel
from cachebot.tests.base_tests import BaseTestCase

class BlacklistCacheTests(BaseTestCase):
    
    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        conf.CACHEBOT_TABLE_BLACKLIST = self._CACHEBOT_TABLE_BLACKLIST
    
    def setUp(self):
        BaseTestCase.setUp(self)
        self.obj = FirstModel.objects.create(text="test")
        self.func = FirstModel.objects.get
        self._CACHEBOT_TABLE_BLACKLIST = conf.CACHEBOT_TABLE_BLACKLIST
        conf.CACHEBOT_TABLE_BLACKLIST += (FirstModel._meta.db_table,)
        
    def test_lookup_not_in_cache(self):
        obj = self.func(id=self.obj.id)
        self.assertFalse(obj.from_cache)
        obj = self.func(id=self.obj.id)
        self.assertFalse(obj.from_cache)

class CacheGetFalseCacheTests(BlacklistCacheTests):
    
    def setUp(self):
        BlacklistCacheTests.setUp(self)
        self.obj = NoCacheModel.objects.create(text="test")
        self.func = NoCacheModel.objects.get
    