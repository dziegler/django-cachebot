import inspect
from itertools import chain
from django.conf import settings
from cachebot import CACHE_PREFIX, CACHEBOT_LOCAL_CACHE
from cachebot import localstore
from cachebot.logging import logged_func

class CachebotBackendMeta(type):
    
    def __init__(cls, name, bases, ns):
        for key, value in chain(ns.iteritems(),parent_ns_gen(bases)):

            if key.startswith('_') or not inspect.isfunction(value): 
                continue
            
            if key in ('set_many', 'clear', 'close'):
                setattr(cls, key, backend_decorator(value))
            else:
                setattr(cls, key, version_key_decorator(value))
            
            if settings.DEBUG:
                from cachebot.logging import cache_log
                setattr(cls, "_logger", cache_log)
 

def backend_decorator(func):
    def inner(instance, *args, **kwargs):
        if CACHEBOT_LOCAL_CACHE:
            return getattr(localstore, func.func_name)(func, instance, *args, **kwargs)
        else:
            return func(instance, *args, **kwargs)
    return inner


def version_key_decorator(func):
    def inner(instance, keys, *args, **kwargs):
        if hasattr(keys, '__iter__'):
            keys = map(version_key, keys)
        else:
            keys = version_key(keys)
            
        if CACHEBOT_LOCAL_CACHE:
            if settings.DEBUG:
                return getattr(localstore, func.func_name)(logged_func(func), instance, keys, *args, **kwargs)
            else:
                return getattr(localstore, func.func_name)(func, instance, keys, *args, **kwargs)

        else:
            return func(instance, keys, *args, **kwargs)
    return inner


def version_key(k):
    if k and k.startswith(CACHE_PREFIX):
        return k
    else:
        return "%s.%s" % (CACHE_PREFIX,k)
        
        
def parent_ns_gen(classes):
    for cls in classes:
        ns = dir(cls)
        for attr in ns:
            value = getattr(cls, attr)
            if inspect.ismethod(value):
                yield attr, value
     
            
