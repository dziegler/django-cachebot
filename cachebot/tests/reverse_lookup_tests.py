from cachebot.models import FirstModel
from cachebot.tests.base_tests import RelatedCacheTests, ExtraRelatedCacheTests

class ReverseRelatedCacheTests(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = FirstModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.secondmodel
        self.kwargs = {'secondmodel':self.obj}

    def test_related_new_obj(self):
        kwargs = {'secondmodel__text':self.secondmodel.text}
        self.test_new_obj(obj=self.secondmodel, kwargs=kwargs)


class ReverseExtraRelatedCacheTests(ReverseRelatedCacheTests, ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = FirstModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.thirdmodel
        self.kwargs = {'secondmodel__thirdmodel':self.obj}
    
    def test_extra_related_new_obj(self):
        kwargs = {'secondmodel__thirdmodel__text':self.thirdmodel.text}
        self.test_new_obj(obj=self.thirdmodel, kwargs=kwargs)


class ReverseRelatedValuesCacheTests(ReverseRelatedCacheTests, RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = FirstModel.objects
        self.func = self.manager.cache().values().filter
        self.obj = self.secondmodel
        self.kwargs = {'secondmodel':self.obj}


class ReverseExtraRelatedValuesCacheTests(ReverseExtraRelatedCacheTests, ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = FirstModel.objects
        self.func = self.manager.cache().values().filter
        self.obj = self.thirdmodel
        self.kwargs = {'secondmodel__thirdmodel':self.obj}
    

class ReverseExtraRelatedExcludeCacheTests(ReverseRelatedCacheTests, ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = FirstModel.objects
        self.func = self.manager.cache().exclude(secondmodel__thirdmodel__id=500).filter
        self.obj = self.thirdmodel
        self.kwargs = {'secondmodel__thirdmodel':self.obj}
    
    def test_extra_related_new_obj(self):
        pass


