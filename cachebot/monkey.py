def patch_manager():
    from django.db import models    
    from cachebot.managers import CacheBotManager
    models.Manager = CacheBotManager

def patch_queryset():
    from django.db.models import query
    from cachebot.queryset import CachedQuerySet
    query.QuerySet = CachedQuerySet

def patch_all(manager=True, queryset=True):
    if manager:
        patch_manager()
    if queryset:
        patch_queryset()
