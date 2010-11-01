from cachebot.models import ThirdModel
from cachebot.tests.base_tests import BasicCacheTests, RelatedCacheTests, ExtraRelatedCacheTests

class ValuesBasicCacheTests1(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values()
        self.func = self.manager.filter


class ValuesBasicCacheTests2(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values().cache()
        self.func = self.manager.filter


class ValuesBasicCacheTests3(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values('text')
        self.func = self.manager.filter


class ValuesBasicCacheTests4(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('text').cache()
        self.func = self.manager.filter
        

class ValuesBasicCacheTests5(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('text')
        self.func = self.manager.filter
        self.append_cache = True
        
        
class ValuesRelatedCacheTests1(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values()
        self.func = self.manager.filter


class ValuesRelatedCacheTests2(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values().cache()
        self.func = self.manager.filter


class ValuesRelatedCacheTests3(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values('text','obj__text')
        self.func = self.manager.filter


class ValuesRelatedCacheTests4(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('text','obj__text').cache()
        self.func = self.manager.filter


class ValuesRelatedCacheTests5(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('text','obj__text')
        self.func = self.manager.filter
        self.append_cache = True
        
        
class ValuesExtraRelatedCacheTests1(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values()
        self.func = self.manager.filter
        

class ValuesExtraRelatedCacheTests2(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values().cache()
        self.func = self.manager.filter


class ValuesExtraRelatedCacheTests3(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.cache().values('obj__text','obj__obj__text')
        self.func = self.manager.filter


class ValuesExtraRelatedCacheTests4(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('obj__text','obj__obj__text').cache()
        self.func = self.manager.filter


class ValuesExtraRelatedAppendCacheTests4(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.manager = ThirdModel.objects.values('text','obj__text','obj__obj__text')
        self.func = self.manager.filter
        self.append_cache = True

