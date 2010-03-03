from cache_utils import CACHE_SECONDS

def cache_globals(request):
    
    return { 'CACHE_SECONDS': CACHE_SECONDS }