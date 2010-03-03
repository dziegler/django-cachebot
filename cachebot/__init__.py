from django.conf import settings

CACHE_SECONDS = getattr(settings,'CACHE_SECONDS',2591000)
CACHE_PREFIX = getattr(settings,'CACHE_PREFIX','')
