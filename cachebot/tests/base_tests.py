from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models.query import ValuesQuerySet
from django.db.models import Q
from django.test import TestCase

from cachebot.models import FirstModel, SecondModel, ThirdModel, GenericModel, ManyModel
from cachebot.utils import flush_cache

class BaseTestCase(TestCase):
    
    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        cache._logger.reset()
    
    def setUp(self):
        super(BaseTestCase, self).setUp()
        flush_cache(hard=False)

class BasicCacheTests(BaseTestCase):
    
    def setUp(self):
        super(BasicCacheTests, self).setUp()
        self.append_cache = False
        self.firstmodel = FirstModel.objects.create(text="test1")
        self.secondmodel = SecondModel.objects.create(text="test2", obj=self.firstmodel)
        self.thirdmodel = ThirdModel.objects.create(text="test3", obj=self.secondmodel)
        ctype = ContentType.objects.get_for_model(self.secondmodel)
        self.genericmodel = GenericModel.objects.create(text="test4", content_type=ctype, object_id=self.secondmodel.id)
        self.manymodel = ManyModel.objects.create(text='test5')
        self.manymodel.firstmodel.add(self.firstmodel)
        self.manymodel.thirdmodel.add(self.thirdmodel)
        self.manager = ThirdModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id}
     
    def _test_cache_lookup(self, from_cache=False):
        try:
            if self.append_cache:
                results = self.func(**self.kwargs).cache()
            else:
                results = self.func(**self.kwargs)
        except (self.obj.DoesNotExist, self.obj.MultipleObjectsReturned):
            self.assertEqual(from_cache, False)
            return
        
        if isinstance(results, ValuesQuerySet):        
            if hasattr(results,'__iter__'):
                for obj in results:
                    self.assertEqual(obj['from_cache'], from_cache)
            else:
                self.assertEqual(results['from_cache'], from_cache)
        else:
            if hasattr(results,'__iter__'):
                for obj in results:
                    self.assertEqual(obj.from_cache, from_cache)
            else:
                self.assertEqual(results.from_cache, from_cache)
        return results

    def _test_lookup(self):
        self._test_cache_lookup(from_cache=False)
        results = self._test_cache_lookup(from_cache=True)
        return results
    
    def test_lookup(self):
        self._test_lookup()

    def test_save_signal(self, obj=None):
        if obj is None:
            obj = self.obj
        self._test_lookup()
        obj.text = "jedi"
        obj.save()
        self._test_cache_lookup(from_cache=False)
    
    def test_delete_signal(self, obj=None):
        if obj is None:
            obj = self.obj
        self._test_lookup()
        obj.delete()
        self._test_cache_lookup(from_cache=False)
    
    def test_new_obj(self, obj=None, kwargs=None):
        if obj is None:
            obj = self.obj
        if kwargs is None:
            self.kwargs = {'text':obj.text}
        else:
            self.kwargs = kwargs
        self._test_lookup()
        new_obj = obj.__class__(text=obj.text)
        if hasattr(new_obj,'obj_id'):
            new_obj.obj = obj.obj
        if hasattr(new_obj,'firstmodel_id'):
            new_obj.firstmodel = obj.firstmodel
        if hasattr(new_obj,'secondmodel_id'):
            new_obj.secondmodel = obj.secondmodel
        if hasattr(new_obj,'content_type_id'):
            new_obj.content_type_id = obj.content_type_id
            new_obj.object_id = obj.object_id
        new_obj.save()
        self._test_cache_lookup(from_cache=False)
    

class FieldCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.kwargs = {'text':self.obj.text}
    
    
class GenericCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.manager = GenericModel.objects
        self.func = self.manager.cache().filter
        self.obj = self.genericmodel
        
        
class RelatedCacheTests(BasicCacheTests):

    def setUp(self):
        BasicCacheTests.setUp(self)
        self.func = self.manager.cache().filter
        self.kwargs = {'obj':self.secondmodel}

    def test_related_save_signal(self):
        self.test_save_signal(obj=self.obj.obj)

    def test_related_delete_signal(self):
        self.test_delete_signal(obj=self.obj.obj)

    def test_related_new_obj(self):
        if hasattr(self.obj, 'obj'):
            kwargs = {'obj__text':self.obj.obj.text}
            self.test_new_obj(obj=self.obj.obj, kwargs=kwargs)


class RelatedIDCacheTests(RelatedCacheTests):

    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.kwargs = {'obj__id':self.secondmodel.id}


class RelatedFieldCacheTests(RelatedCacheTests):

    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.kwargs = {'obj__text':self.secondmodel.text}
           
              
class ExtraRelatedCacheTests(RelatedCacheTests):

    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.func = self.manager.cache().filter
        self.kwargs = {'obj__obj':self.firstmodel}
        
    def test_extra_related_save_signal(self):
        self.test_save_signal(obj=self.obj.obj.obj)

    def test_extra_related_delete_signal(self):
        self.test_delete_signal(obj=self.obj.obj.obj)
    
    def test_extra_related_new_obj(self):
        if hasattr(self.obj, 'obj') and hasattr(self.obj.obj, 'obj') :
            kwargs = {'obj__obj__text':self.obj.obj.obj.text}
            self.test_new_obj(obj=self.obj.obj.obj, kwargs=kwargs)


class ExtraRelatedIDCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj__id':self.firstmodel.id}


class ExtraRelatedFieldCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj__text':self.firstmodel.text}

   
class ExtraRelatedAppendCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.append_cache = True


class SelectiveCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.append_cache = True
        self.func = self.manager.cache('obj__obj').filter


class SelectiveCacheIDTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.append_cache = True
        self.func = self.manager.cache('obj__obj_id').filter
        

class ComplexQueryCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)

    def _test_cache_lookup(self, from_cache=False):
        try:
            if self.append_cache:
                results = self.func(Q(obj__obj__id=self.firstmodel.id)|Q(obj__obj__text='blah blah blah')).cache()
            else:
                results = self.func(Q(obj__obj__id=self.firstmodel.id)|Q(obj__obj__text='blah blah blah'))
        except (self.obj.DoesNotExist, self.obj.MultipleObjectsReturned):
            self.assertEqual(from_cache, False)
            return
        
        if isinstance(results, ValuesQuerySet):        
            if hasattr(results,'__iter__'):
                for obj in results:
                    self.assertEqual(obj['from_cache'], from_cache)
            else:
                self.assertEqual(results['from_cache'], from_cache)
        else:
            if hasattr(results,'__iter__'):
                for obj in results:
                    self.assertEqual(obj.from_cache, from_cache)
            else:
                self.assertEqual(results.from_cache, from_cache)
        return results
    
    def _test_lookup(self):
        self._test_cache_lookup(from_cache=False)
        results = self._test_cache_lookup(from_cache=True)
        return results
    
    def test_lookup(self):
        self._test_lookup()
    
    def test_extra_related_new_obj(self):
        pass
            