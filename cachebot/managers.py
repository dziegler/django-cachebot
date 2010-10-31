def patch_manager():
    from django.db import models
    from cachebot import conf
    
    class CachebotManager(models.Manager):

        def __init__(self, cache_all=conf.CACHEBOT_CACHE_ALL, cache_get=conf.CACHEBOT_CACHE_GET, **kwargs):
            super(CachebotManager, self).__init__(**kwargs)
            self.cache_all = cache_all
            if cache_all:
                self.cache_get = True
            else:
                self.cache_get = cache_get
    
        def get_query_set(self):
            qs = super(CachebotManager, self).get_query_set()
            if self.cache_all:
                return qs.cache()
            else:
                return qs

        def cache(self, *args):
            return self.get_query_set().cache(*args)

        def select_reverse(self, *args, **kwargs):
            return self.get_query_set().select_reverse(*args, **kwargs)
    
    models.Manager = CachebotManager

def patch_queryset():
    from django.db.models import query
    from cachebot.queryset import CachedQuerySet
    query.QuerySet = CachedQuerySet

def patch_all(manager=True, queryset=True):
    if manager:
        patch_manager()
    if queryset:
        patch_queryset()
