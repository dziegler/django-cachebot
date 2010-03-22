import os

VERSION = (0,1)
__version__ = '.'.join(map(str, VERSION))

try:
    from django.conf import settings
    import django.dispatch

    CACHE_SECONDS = getattr(settings,'CACHE_SECONDS',2591000)
    CACHE_PREFIX = getattr(settings,'CACHE_PREFIX','').encode('utf-8')
    CACHEBOT_CACHE_GET = getattr(settings,'CACHEBOT_CACHE_GET',False)
    CACHEBOT_CACHE_ALL = getattr(settings,'CACHEBOT_CACHE_ALL',False)
    CACHEBOT_TABLE_BLACKLIST = getattr(settings,'CACHEBOT_TABLE_BLACKLIST',('django_session',))
    CACHEBOT_LOCAL_CACHE = getattr(settings,'CACHEBOT_LOCAL_CACHE',True)
    CACHEBOT_LOG = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cachebot.log')
    post_update = django.dispatch.Signal(providing_args=["sender", "instance"])

except ImportError:
    pass