from time import time

from django.core.cache import cache
from django.utils.hashcompat import md5_constructor
from django.db.models.sql.constants import LOOKUP_SEP
from django.db.models.base import ModelBase
from django.db.models.query_utils import QueryWrapper
from django.core.exceptions import ObjectDoesNotExist

def set_value(obj, key, value):
    """Helper method to handle setting values in a CachedQuerySet or ValuesQuerySet object"""
    try:
        obj[key] = value
    except TypeError:
        setattr(obj, key, value)

def get_invalidation_key(table_alias, accessor_path='', lookup_type='exact', negate=False, value='', version=None):
    """
    An invalidation key is associated with a set of cached queries. A blank accessor_path
    will create an invalidation key for this entire table instead of a specific row
    """
    
    # punt on this problem for now
    if isinstance(value, QueryWrapper) or lookup_type != 'exact' or negate:
        value = ''
        
    if hasattr(value, '__iter__'):
        if len(value) == 1:
            value = value[0]
        else:
            value = ''

    base_key = md5_constructor('.'.join((accessor_path, unicode(value))).encode('utf-8')).hexdigest()
    return cache.make_key('.'.join((table_alias, 'cachebot.invalidation', base_key)), version=version)

def get_values(instance, accessor_path):
    accessor_split = accessor_path.split(LOOKUP_SEP)
    if isinstance(instance, dict):
        try:
            yield instance[accessor_path]
            raise StopIteration
        except KeyError:
            # maybe this is a nested reverse relation
            accessor = accessor_split.pop(0)
            try:
                instance = instance[accessor]
            except KeyError:
                instance = instance[accessor + '_cache']
    
    for value in _get_nested_value(instance, accessor_split):
        if value is None:
            continue
        if isinstance(value.__class__, ModelBase):
            value = getattr(value, 'pk')
        yield value
    raise StopIteration

def _get_nested_value(instance, accessor_split):
    accessor = accessor_split.pop(0)
    try:
        value = getattr(instance, accessor)
    except AttributeError:
        if not instance:
            yield None
            raise StopIteration
        
        raise_error = True
        for modifier in ('_cache', '_id'):  
            if accessor.endswith(modifier):
                accessor = accessor[:-len(modifier)]
                try:
                    value = getattr(instance, accessor)
                    raise_error = False
                    break
                except AttributeError:
                    pass
                    
        if raise_error:
            yield None
            raise StopIteration

    if hasattr(value, 'select_reverse'):
        # check if a cached version of this reverse relation exists
        if hasattr(value, accessor + '_cache'):
            value = getattr(instance, accessor + '_cache')
        else:
            value = value.all()
    
    if hasattr(value, '__iter__'):
        if accessor_split:
            for obj in value:
                for nested_val in _get_nested_value(obj, accessor_split):
                    yield nested_val
        else:
            for nested_val in value:
                yield nested_val
    else:    
        if accessor_split:
            for nested_val in _get_nested_value(value, accessor_split):
                yield nested_val
        else:
            yield value
    raise StopIteration

def get_many_by_key(cache_key_f, item_keys, version=None):
    """
    For a series of item keys and a function that maps these keys to cache keys,
    get all the items from the cache if they are available there.
    
    Return a dictionary mapping the item keys to the objects retrieved from the
    cache.  Any items not found in the cache are not returned.
    """
    cache_key_to_item_key = {}
    for item_key in item_keys:
        cache_key = cache.make_key(cache_key_f(item_key), version=version)
        cache_key_to_item_key[cache_key] = item_key

    # request from cache
    from_cache = cache.get_many(cache_key_to_item_key.keys())

    results = {}
    for cache_key, value in from_cache.iteritems():
        item_key = cache_key_to_item_key[cache_key]
        results[item_key] = value
    return results

def fetch_objects(cache_key_f, get_database_f, item_keys):
    """
    For a series of item keys and two functions, get these items from the cache
    or from the database (individually so that the queries are cached).
    
    cache_key_f: function to convert an item_key to a cache key
    get_database_f: function to get an item from the database
    
    Returns a dictionary mapping item_keys to objects.  If the object
    does not exist in the database, ignore it.
    """
    item_key_to_item = get_many_by_key(cache_key_f, item_keys)
    
    for item_key in item_keys:
        if item_key not in item_key_to_item:
            # failed to get the item from the cache
            try:
                # have to get each item individually to cache the query
                item = get_database_f(item_key)
                item_key_to_item[item_key] = item
            except ObjectDoesNotExist:
                pass
    
    return item_key_to_item

def fetch_instances(model, field, values):
    """
    For a series of item keys, attempt to get the model from the cache,
    if that doesn't work, query the database.
    
    The point of all this is to do a single memcache query and then individual database queries
    for the remaining items. It would be nice to do a single database query for the remaining
    items, but it does not appear that cachebot supports this.
    """
    cache_key_f = lambda value: model.objects.filter((field, value)).get_cache_key()
    # since the filter query returns a list, it seems we need a list here to keep the types the same
    get_database_f = lambda value: [model.objects.get((field, value))]
    
    item_key_to_object = fetch_objects(cache_key_f, get_database_f, values)
    
    # remove the list surrounding each value by grabbing the first entry
    for k, v in item_key_to_object.items():
        if len(v) > 0:
            item_key_to_object[k] = v[0]
        else:
            del item_key_to_object[k] # this happens when cachebot has cached a result of [] for the query
        
    return item_key_to_object

def flush_cache(hard=True):
    from cachebot.models import CacheBotSignals
    from cachebot.signals import cache_signals

    CacheBotSignals.objects.all().delete()
    cache_signals.local_signals = {}
    if hard:
        cache.clear()
    else:
        cache.version = int(time()*10000)
