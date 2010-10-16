from itertools import chain

from django.core.cache import cache
from django.utils.http import urlquote
from django.utils.hashcompat import md5_constructor
from django.db.models.signals import class_prepared, post_save, pre_delete
from django.core.management.color import no_style
from django.core.signals import request_finished
from cachebot import conf
from cachebot.models import CacheBotSignals, post_update
from cachebot.utils import get_invalidation_key, get_values
from cachebot.backends import version_key

if conf.CACHEBOT_ENABLE_LOG:
    request_finished.connect(cache._logger.reset)
    
class CacheSignals(object):
    """
    An object that handles installed cache signals. Keep a local copy of the signals
    so we don't hammer memcache
    """
    
    __shared_state = dict(
        ready = False,
        local_signals = dict()
    )
    
    def __init__(self):
        self.__dict__ = self.__shared_state
 
    def get_lookup_key(self, model_class):
        return version_key('.'.join(('cachesignals', model_class._meta.db_table)))
    
    def get_local_signals(self, model_class):
        accessor_set = self.local_signals.get(model_class._meta.db_table)
        if not accessor_set:
            accessor_set = set()
        return accessor_set
    
    def get_global_signals(self, model_class):
        lookup_key = self.get_lookup_key(model_class)
        accessor_set = cache.get(lookup_key)
        if not accessor_set:
            accessor_set = set()
        self.local_signals[model_class._meta.db_table] = accessor_set
        return accessor_set
    
    def set_signals(self, model_class, accessor_set):
        lookup_key = self.get_lookup_key(model_class)
        self.local_signals[model_class._meta.db_table] = accessor_set
        cache.set(lookup_key, accessor_set, 0)
        
    def register(self, model_class, accessor_path, lookup_type, negate=False):
        path_tuple = (accessor_path, lookup_type, negate)
        if path_tuple not in self.get_local_signals(model_class):
            # not in local cache, check the global cache
            accessor_set = self.get_global_signals(model_class)
            if path_tuple not in accessor_set:
                # can't use get_or_create here
                try:               
                    CacheBotSignals.objects.filter(
                        table_name=model_class._meta.db_table,
                        accessor_path=accessor_path,
                        lookup_type=lookup_type,
                        exclude=negate
                    )[0]
                except IndexError:
                    CacheBotSignals.objects.create(
                        table_name=model_class._meta.db_table,
                        accessor_path=accessor_path,
                        lookup_type=lookup_type,
                        exclude=negate
                    )
                accessor_set.add(path_tuple)
                self.set_signals(model_class, accessor_set)

cache_signals = CacheSignals()


def load_cache_signals(sender, **kwargs):
    """On startup, sync signals with registered models"""
    from django.db import connection

    if not cache_signals.ready:
        # Have to load directly from db, because CacheBotSignals is not prepared yet
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM %s" % CacheBotSignals._meta.db_table)
        except Exception:
            # This should only happen on syncdb when CacheBot tables haven't been created yet, 
            # but there's not really a good way to catch this error
            sql, references = connection.creation.sql_create_model(CacheBotSignals, no_style())
            cursor.execute(sql[0])
            cursor.execute("SELECT * FROM %s" % CacheBotSignals._meta.db_table)

        results = cursor.fetchall()
        tables = [r[1] for r in results]
        mapping = cache.get_many(tables)
        for r in results:
            key = version_key('.'.join(('cachesignals', r[1])))
            accessor_set = mapping.get(key)
            if accessor_set is None:
                accessor_set = set()
            accessor_set.add(r[2:5])
            mapping[key] = accessor_set
        cache.set_many(mapping, 0)
        cache_signals.ready = True
        
class_prepared.connect(load_cache_signals)


### INVALIDATION FUNCTIONS ###
def post_update_cachebot(sender, queryset, **kwargs):
    invalidate_cache(sender, queryset)
post_update.connect(post_update_cachebot)

def post_save_cachebot(sender, instance, **kwargs):
    invalidate_cache(sender, (instance,))
post_save.connect(post_save_cachebot)

def pre_delete_cachebot(sender, instance, **kwargs):
    invalidate_cache(sender, (instance,))
pre_delete.connect(pre_delete_cachebot)

def invalidate_object(instance):
    invalidate_cache(type(instance), (instance,))

def invalidate_cache(model_class, objects, **extra_keys):
    """
    Flushes the cache of any cached objects associated with this instance.

    Explicitly set a None value instead of just deleting so we don't have any race
    conditions where:
        Thread 1 -> Cache miss, get object from DB
        Thread 2 -> Object saved, deleted from cache
        Thread 1 -> Store (stale) object fetched from DB in cache
    Five second should be more than enough time to prevent this from happening for
    a web app.
    """
    invalidation_dict = {}
    accessor_set = cache_signals.get_global_signals(model_class)
    for obj in objects:
        for (accessor_path, lookup_type, negate) in accessor_set:
            if lookup_type != 'exact' or negate:
                invalidation_key = get_invalidation_key(
                    model_class._meta.db_table, 
                    accessor_path = accessor_path, 
                    negate = negate,
                    value = '')
                invalidation_dict[invalidation_key] = None
            else:
                for value in get_values(obj, accessor_path):
                    invalidation_key = get_invalidation_key(
                        model_class._meta.db_table, 
                        accessor_path = accessor_path, 
                        negate = negate,
                        value = value)
                    invalidation_dict[invalidation_key] = None
    
    if invalidation_dict:
        invalidation_dict.update(cache.get_many(invalidation_dict.keys()))

        cache_keys = set()
        for obj_key, cache_key_list in invalidation_dict.iteritems():
            if cache_key_list:
                cache_keys.update(cache_key_list.split(','))

        keys_to_invalidate = dict([(key, None) for key in chain(cache_keys, invalidation_dict.keys())])
        keys_to_invalidate.update(extra_keys)
        cache.set_many(keys_to_invalidate, 5)
        cache.delete_many(keys_to_invalidate.keys())

def invalidate_template_cache(fragment_name, *variables):
    args = md5_constructor(u':'.join(map(urlquote, variables)).encode('utf-8')).hexdigest()
    cache_key = 'template.cache.%s.%s' % (fragment_name, args)
    cache.delete(cache_key)


