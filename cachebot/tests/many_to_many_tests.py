from cachebot.models import ManyModel
from cachebot.tests.base_tests import BasicCacheTests, RelatedCacheTests

class BasicManyToManyCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ManyModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.manymodel
        self.related_obj = self.firstmodel
        self.kwargs = {'id':self.obj.id}
        
    def test_lookup(self):
        self._test_lookup()

class RelatedManyToManyCacheTests(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ManyModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.manymodel
        self.related_obj = self.firstmodel
        self.kwargs = {'firstmodel':self.related_obj}
    
    def test_related_save_signal(self):
        # these will fail until we get many to many signals
        pass
    
    def test_related_delete_signal(self):
        self._test_lookup()
        obj = self.related_obj
        obj.text = "mind"
        obj.delete()
        self._test_cache_lookup(from_cache=False)
    
