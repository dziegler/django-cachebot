import inspect
from itertools import chain
from cachebot import CACHE_PREFIX

class CachebotBackendMeta(type):
    
    def __init__(cls, name, bases, ns):
        for key, value in chain(ns.iteritems(),parent_ns_gen(bases)):
            
            if key in ('__init__', 'set_many', 'clear'):
                continue

            if not inspect.ismethod(value): 
                continue

            setattr(cls, key, backend_decorator(value))
 

def backend_decorator(func):
    def inner(instance, keys, *args, **kwargs):
        if hasattr(keys, '__iter__'):
            keys = map(version_key, keys)
        else:
            keys = version_key(keys)
            
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
     
            
