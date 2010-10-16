from cachebot import conf
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
                
        return logged_func(func)(instance, keys, *args, **kwargs)
    return inner


def version_key(k):
    if k and k.startswith(conf.CACHE_PREFIX):
        return k
    else:
        return "%s.%s" % (conf.CACHE_PREFIX,k)
        
