# this will not work if imported from cache_utils.managers

class SimpleCacheManager(DjangoManager):
    
    def __init__(self, cache_all=False, *args, **kwargs):
        super(SimpleCacheManager, self).__init__(*args, **kwargs)
        self.cache_all = cache_all
    
    def get_query_set(self):
        if self.cache_all:
            return CachedQuerySet(self.model).cache()
        else:
            return CachedQuerySet(self.model)
    
    def get_or_create(self, *args, **kwargs):
        return self.get_query_set().cache().get_or_create(*args, **kwargs)
    
    def get(self, *args, **kwargs):
        return self.get_query_set().cache().get(*args, **kwargs)

    def cache(self, *args):
        return self.get_query_set().cache(*args)
    
    def select_reverse(self, *args, **kwargs):
        return self.get_query_set().select_reverse(*args, **kwargs)
    
        
    