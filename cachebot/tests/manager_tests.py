import time

from django.db import connection
from django.conf import settings

from cachebot import conf
from cachebot.models import FirstModel
from cachebot.tests.base_tests import BaseTestCase, BasicCacheTests, FieldCacheTests, RelatedCacheTests, ExtraRelatedCacheTests

class GetBasicCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.func = self.manager.get


class GetRelatedCacheTests(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.func = self.manager.get


class GetExtraRelatedCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.func = self.manager.get


class GetOrCreateCacheTests(BaseTestCase):

    def test_get_then_create(self):
        self.assertRaises(FirstModel.DoesNotExist, FirstModel.objects.get, **{'text':'new'})
        FirstModel.objects.create(text='new')
        time.sleep(conf.CACHE_INVALIDATION_TIMEOUT)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,False)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,True)
    
    def test_get_or_create(self):
        obj, created = FirstModel.objects.get_or_create(text='new')
        self.assertEqual(created, True)
        time.sleep(conf.CACHE_INVALIDATION_TIMEOUT)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,False)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,True)

class SelectRelatedCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.func = self.manager.select_related().cache().filter
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id}

class ExcludeCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id+1}
        self.func = self.manager.cache().exclude


class ExcludeFieldCacheTests(FieldCacheTests):
    
    def setUp(self):
        FieldCacheTests.setUp(self)
        self.kwargs = {'text':'this text is not in any model'}
        self.func = self.manager.cache().exclude
        

class ExtraRelatedExcludeCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj':self.obj.obj.obj.id+1}
        self.func = self.manager.cache().exclude


class ExcludeAndFilterCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id+1}
        self.func = self.manager.cache().filter(id=self.obj.id).exclude


class ExcludeAndFilterFieldCacheTests(FieldCacheTests):
    
    def setUp(self):
        FieldCacheTests.setUp(self)
        self.kwargs = {'text':'this text is not in any model'}
        self.func = self.manager.cache().filter(text=self.obj.text).exclude
        
        
class ExtraRelatedExcludeAndFilterCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj':self.obj.obj.obj.id+1}
        self.func = self.manager.cache().filter(obj__obj=self.obj.obj.obj).exclude
       
       
class RangeCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj__in':[self.firstmodel]}
        
        
class NestedQuerysetCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        queryset = FirstModel.objects.all()
        self.kwargs = {'obj__obj__in':queryset}

# disable these tests 
        
class CountCacheTests(BasicCacheTests):
    
    def setUp(self):
        settings.DEBUG = True
        BasicCacheTests.setUp(self)
        # call count to create any CacheBotSignals first
        self.func(**self.kwargs).count()
    
    def test_lookup(self, count=1):
        return
        connection.queries = []
        self.assertEqual(self.func(**self.kwargs).count(), count)
        self.assertEqual(len(connection.queries), 1)
        self.assertEqual(self.func(**self.kwargs).count(), count)
        self.assertEqual(len(connection.queries), 1)
        
    
    def test_save_signal(self, obj=None):
        return
        if obj is None:
            obj = self.obj
        self.test_lookup(count=1)
        obj.save()
        self.test_lookup(count=1)
    
    def test_delete_signal(self, obj=None):
        return
        if obj is None:
            obj = self.obj
        self.test_lookup(count=1)
        obj.delete()
        self.test_lookup(count=0)

class ExtraRelatedCountCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        settings.DEBUG = True
        ExtraRelatedCacheTests.setUp(self)
        # call count to create any CacheBotSignals first
        self.func(**self.kwargs).count()
        
    def test_related_save_signal(self):
        return
        self.test_save_signal(obj=self.obj.obj)
    
    def test_related_delete_signal(self):
        return
        self.test_delete_signal(obj=self.obj.obj)
    
    def test_extra_related_save_signal(self):
        return
        self.test_save_signal(obj=self.obj.obj.obj)
    
    def test_extra_related_delete_signal(self):
        return
        self.test_delete_signal(obj=self.obj.obj.obj)
        
    