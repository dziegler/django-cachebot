import inspect
from itertools import chain
from django.conf import settings
from cachebot import CACHEBOT_LOCAL_CACHE
from cachebot.localstore import deferred_cache
from cachebot.logger import logged_func

class CachebotBackendMeta(type):
    
    def __init__(cls, name, bases, ns):
        for key, value in chain(ns.iteritems(),parent_ns_gen(bases)):

            if key.startswith('_') or not inspect.isfunction(value): 
                continue
            
            if key in ('clear', 'close'):
                setattr(cls, key, backend_decorator(value))
            else:
                setattr(cls, key, version_key_decorator(value))
            
            setattr(cls, '_deferred', deferred_cache)
            
            if settings.DEBUG:
                from cachebot.logger import cache_log
                setattr(cls, "_logger", cache_log)
 

def backend_decorator(func):
    def inner(instance, *args, **kwargs):
        name = func.func_name
            
        if CACHEBOT_LOCAL_CACHE:
            return getattr(instance._deferred, name)(func, instance, *args, **kwargs)
        else:
            return func(instance, *args, **kwargs)
    return inner


def version_key_decorator(func):
    def inner(instance, keys, *args, **kwargs):
        if hasattr(keys, '__iter__'):
            if isinstance(keys, dict):
                keys = dict([(version_key(k),v) for k,v in keys.iteritems()])
            else:
                keys = map(version_key, keys)
        else:
            keys = version_key(keys)
        
        name = func.func_name
        
        # this is ugly, but can't redefine func
        if CACHEBOT_LOCAL_CACHE:
            if settings.DEBUG:
                return getattr(instance._deferred, name)(logged_func(func), instance, keys, *args, **kwargs)
            else:
                return getattr(instance._deferred, name)(func, instance, keys, *args, **kwargs)
        else:
            if settings.DEBUG:
                return logged_func(func)(instance, keys, *args, **kwargs)
            else:
                return func(instance, keys, *args, **kwargs)
    return inner


def version_key(k):
    if k and k.startswith(settings.CACHE_PREFIX):
        return k
    else:
        return "%s.%s" % (settings.CACHE_PREFIX,k)
        
        
def parent_ns_gen(classes):
    for cls in classes:
        ns = dir(cls)
        for attr in ns:
            value = getattr(cls, attr)
            if inspect.ismethod(value):
                yield attr, value
     
