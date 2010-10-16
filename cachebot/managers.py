def patch_manager():
    from django.db.models import Manager
    from cachebot import conf

    old_init = Manager.__init__

    def __init__(self, cache_all=conf.CACHEBOT_CACHE_ALL, cache_get=conf.CACHEBOT_CACHE_GET, **kwargs):
        old_init(self, **kwargs)
        self.cache_all = cache_all
        if cache_all:
            self.cache_get = True
        else:
            self.cache_get = cache_get
    
    def get_query_set(self):
        from cachebot.queryset import CachedQuerySet
        if self.cache_all:
            return CachedQuerySet(self.model).cache()
        else:
            return CachedQuerySet(self.model)

    def cache(self, *args):
        return self.get_query_set().cache(*args)

    def select_reverse(self, *args, **kwargs):
        return self.get_query_set().select_reverse(*args, **kwargs)

    Manager.__init__ = __init__
    Manager.get_query_set = get_query_set
    Manager.cache = cache
    Manager.select_reverse = select_reverse
    Manager.cache_get = conf.CACHEBOT_CACHE_GET
    Manager.cache_all = conf.CACHEBOT_CACHE_ALL
    
