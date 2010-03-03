from cachebot import CACHE_PREFIX

def version_key_decorator(func):
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
        
    