import os

from django.conf import settings

CACHE_SECONDS = getattr(settings, 'CACHE_SECONDS', 0)
CACHEBOT_CACHE_GET = getattr(settings, 'CACHEBOT_CACHE_GET', True)
CACHEBOT_CACHE_ALL = getattr(settings, 'CACHEBOT_CACHE_ALL', False)
CACHEBOT_TABLE_BLACKLIST = getattr(settings, 'CACHEBOT_TABLE_BLACKLIST', ('django_session', 'django_content_type', 'south_migrationhistory'))
CACHEBOT_ENABLE_LOG = getattr(settings, 'CACHEBOT_ENABLE_LOG', False)
CACHEBOT_LOG = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cachebot.log')
CACHEBOT_DEBUG_RESULTS = getattr(settings, 'CACHEBOT_DEBUG_RESULTS', False)
CACHE_INVALIDATION_TIMEOUT = getattr(settings, 'CACHE_INVALIDATION_TIMEOUT', 5)
RUNNING_TESTS = getattr(settings, 'RUNNING_TESTS', False)
if RUNNING_TESTS:
    CACHEBOT_DEBUG_RESULTS = True
    CACHE_INVALIDATION_TIMEOUT = 1
