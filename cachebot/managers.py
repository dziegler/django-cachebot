from django.db import models
from cachebot import CACHEBOT_CACHE_GET, CACHEBOT_CACHE_ALL
from cachebot.queryset import CachedQuerySet

### TODO: This is not DRY. Needs to be integrated with patch_django_manger ###

class CacheBotManager(models.Manager):
    """
    Queries made through CacheBotManager will be cached.
    
    @cache_all - If True, all queries made with this manager will automatically be cached
    @cache_get - If True, all get queries will automatically be cached
    
    NOTE: It's recommended that you use the patch_django_manager command which
    will make this the default manager used by Django.
    """
    def __init__(self, cache_all=CACHEBOT_CACHE_ALL, cache_get=CACHEBOT_CACHE_GET, *args, **kwargs):
        super(CacheBotManager, self).__init__(*args, **kwargs)
        self.cache_all = cache_all
        self.cache_get = cache_get
    
    def get_query_set(self):
        if self.cache_all:
            return CachedQuerySet(self.model).cache()
        else:
            return CachedQuerySet(self.model)
    
    def get_or_create(self, *args, **kwargs):
        if self.cache_get:
            return self.get_query_set().cache().get_or_create(*args, **kwargs)
        else:
            return self.get_query_set().get_or_create(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self.cache_get:
            return self.get_query_set().cache().get(*args, **kwargs)
        else:
            return self.get_query_set().get(*args, **kwargs)

    def cache(self, *args):
        return self.get_query_set().cache(*args)
    
    def select_reverse(self, *args, **kwargs):
        return self.get_query_set().select_reverse(*args, **kwargs)
    
        
    