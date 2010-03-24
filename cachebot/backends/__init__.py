from django.conf import settings

from cachebot.logger import logged_func


def version_key_decorator(func):
    def inner(instance, keys, *args, **kwargs):
        if hasattr(keys, '__iter__'):
            if isinstance(keys, dict):
                keys = dict([(version_key(k),v) for k,v in keys.iteritems()])
            else:
                keys = map(version_key, keys)
        else:
            keys = version_key(keys)
                
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
     
