from django.db.models import Manager

from cachebot import conf
from cachebot.queryset import CachedQuerySet

class CacheBotManager(Manager):

    def __init__(self, cache_all=conf.CACHEBOT_CACHE_ALL, cache_get=conf.CACHEBOT_CACHE_GET, **kwargs):
        super(CacheBotManager, self).__init__(**kwargs)
        self.cache_all = cache_all
        if cache_all:
            self.cache_get = True
        else:
            self.cache_get = cache_get

    def get_query_set(self):
        qs = CachedQuerySet(self.model, using=self.db)
        if self.cache_all:
            return qs.cache()
        else:
            return qs

    def cache(self, *args):
        return self.get_query_set().cache(*args)

    def select_reverse(self, *args, **kwargs):
        return self.get_query_set().select_reverse(*args, **kwargs)
