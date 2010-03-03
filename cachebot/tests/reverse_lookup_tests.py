from cache_utils.tests.base_tests import RelatedCacheTests, ExtraRelatedCacheTests
from cache_utils.tests.models import FirstModel, SecondModel, ThirdModel

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
    
