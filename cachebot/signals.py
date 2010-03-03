from itertools import chain
from time import time

import django.dispatch
from django.core.cache import cache
from django.dispatch.dispatcher import _make_id
from django.conf import settings
from django.utils.http import urlquote
from django.utils.hashcompat import md5_constructor
from django.db.models.signals import post_save, pre_delete, class_prepared


from cache_utils import CACHE_SECONDS, CACHE_VERSION
from cache_utils.models import SimpleCacheSignals
from cache_utils.utils import get_invalidation_key, get_values


class CacheSignals(object):
    """
    A cache that stores installed cache signals.
    """
    # Use the Borg pattern to share state between all instances. Details at
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    try:
        __shared_state = dict(
            simplecache_signals = {},
            simplecache_signal_imports = dict([(s.__unicode__(), s.accessor_path) for s in SimpleCacheSignals.objects.all()]),
        )
    except:
        __shared_state = dict(
            simplecache_signals = {},
            simplecache_signal_imports = {},
        )
        
    def __init__(self):
        self.__dict__ = self.__shared_state

    def create_signal(self, model_class, accessor_path, lookup_type, negate):
        post_update.connect(post_update_simplecache, sender=model_class)
        post_save.connect(post_save_simplecache, sender=model_class)
        pre_delete.connect(pre_delete_simplecache, sender=model_class)
        lookup_key = _make_id(model_class)
        accessor_set = self.simplecache_signals.get(lookup_key, set())
        accessor_set.add((accessor_path, lookup_type, negate))
        self.simplecache_signals[lookup_key] = accessor_set
        
    def register(self, model_class, accessor_path, lookup_type, negate=False):
        lookup_key = _make_id(model_class)
        accessor_set = self.simplecache_signals.get(lookup_key, set())
        if (accessor_path, lookup_type, negate) not in accessor_set:  
            # can't use get_or_create here
            try:               
                SimpleCacheSignals.objects.filter(
                    import_path=model_class.__module__,
                    module_name=model_class.__name__,
                    accessor_path=accessor_path,
                    lookup_type=lookup_type,
                    exclude=negate
                )[0]
            except IndexError:
                SimpleCacheSignals.objects.create(
                    import_path=model_class.__module__,
                    module_name=model_class.__name__,
                    accessor_path=accessor_path,
                    lookup_type=lookup_type,
                    exclude=negate
                )
                                         
            self.create_signal(model_class, accessor_path, lookup_type, negate)

cache_signals = CacheSignals()


def load_cache_signals(sender, **kwargs):
    """On startup, create signals for registered models"""
    mod = u'.'.join((sender.__module__,sender.__name__))
    if mod in cache_signals.simplecache_signal_imports:
        path_tuple = cache_signals.simplecache_signal_imports[mod]
        cache_signals.create_signal(sender, path_tuple[0], path_tuple[0], path_tuple[2])
class_prepared.connect(load_cache_signals)


post_update = django.dispatch.Signal(providing_args=["sender", "instance"])

### INVALIDATION FUNCTIONS ###

def post_update_simplecache(sender, instance, **kwargs):
    ## TODO auto add select reverse and related ##
    lookup_key = _make_id(sender)
    accessor_set = cache_signals.simplecache_signals.get(lookup_key, set())
    invalidate_cache(sender, instance)


def post_save_simplecache(sender, instance, created, **kwargs):
    invalidate_cache(sender, (instance,))


def pre_delete_simplecache(sender, instance, **kwargs):
    invalidate_cache(sender, (instance,))


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
    lookup_key = _make_id(model_class)
    accessor_set = cache_signals.simplecache_signals.get(lookup_key, set())
    for obj in objects:
        for (accessor_path, lookup_type, negate) in accessor_set:
            for value in get_values(obj, accessor_path):
                invalidation_key = get_invalidation_key(
                    model_class._meta.db_table, 
                    accessor_path = accessor_path, 
                    negate = negate,
                    value = value, save=False)
                invalidation_dict[invalidation_key] = None
            
    invalidation_dict.update(cache.get_many(invalidation_dict.keys()))

    cache_keys = set()
    for obj_key, cache_key_list in invalidation_dict.iteritems():
        if cache_key_list:
            cache_keys.update(cache_key_list)
            
    keys_to_invalidate = dict([(key, None) for key in chain(cache_keys, invalidation_dict.keys())])
    keys_to_invalidate.update(extra_keys)
    cache.set_many(keys_to_invalidate, 5)


def invalidate_template_cache(fragment_name, *variables):
    args = md5_constructor(u':'.join(map(urlquote, variables)).encode('utf-8')).hexdigest()
    cache_key = 'template.cache.%s.%s' % (fragment_name, args)
    cache.delete(cache_key)


