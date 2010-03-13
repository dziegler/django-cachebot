from itertools import chain

from django.core.cache import cache
from django.conf import settings
from django.utils.hashcompat import md5_constructor
from django.db.models.sql.constants import LOOKUP_SEP
from django.db.models.base import ModelBase
from django.db.models.query_utils import QueryWrapper

from cachebot.models import CacheBotException
from cachebot.backends import version_key

def get_invalidation_key(table_alias, accessor_path='', lookup_type='exact', negate=False, value='', save=True):
    """An invalidation key is associated with a set of cached queries. A blank accessor_path
    will create an invalidation key for this entire table instead of a specific row"""
    
    
    # punt on this problem for now
    if isinstance(value, QueryWrapper) or lookup_type != 'exact' or negate:
        value = ''
    if hasattr(value, '__iter__'):
        if len(value) == 1:
            value = value[0]
        else:
            value = ''
    #print save, table_alias,accessor_path,str(value)
    base_args = ('cachebot:invalidation',table_alias,accessor_path,str(value))
    return version_key(md5_constructor(u'.'.join(base_args).encode('utf-8')).hexdigest())

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
            raise CacheBotException(u"%s is not a valid attribute of %s" % (accessor, instance))

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
                yield value
        else:
            yield value
    raise StopIteration

