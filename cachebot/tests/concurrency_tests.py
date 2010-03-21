from django.db import transaction, IntegrityError

from cachebot.tests.utils import test_concurrently, CONCURRENCY_LEVEL
from cachebot.tests.base_tests import BaseTestCase
from cachebot.tests.models import UniqueModel

class BasicConcurrencyCacheTests(BaseTestCase):
        
    def setUp(self):
        BaseTestCase.setUp(self)
    
    @transaction.commit_on_success
    def _create_or_get(self, model_class, **kwargs):
        defaults = kwargs.pop('defaults', {})
        try:
            params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
            params.update(defaults)
            obj = model_class.objects.create(**params)
            created = True
        except IntegrityError:
            transaction.commit()
            obj = model_class.objects.get(**kwargs)
            created = False
        return obj, created
    
    @test_concurrently(CONCURRENCY_LEVEL)
    def _test_get_or_create(self):
        self._create_or_get(UniqueModel, text="test")
        UniqueModel.objects.get_or_create(text="test")
    
    def test_get_or_create(self):
        self._test_get_or_create()
        obj = UniqueModel.objects.get(text="test")
        self.assertEquals(obj.from_cache, True)
    
    @test_concurrently(CONCURRENCY_LEVEL)
    def _test_save(self, obj):
        obj.save()
    
    def test_save(self):
        obj, created = UniqueModel.objects.get_or_create(text="test")
        self._test_save(obj)
        obj = UniqueModel.objects.get(text="test")
        self.assertEquals(obj.from_cache, False)
    
