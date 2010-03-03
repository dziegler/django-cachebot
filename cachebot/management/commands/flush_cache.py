#!/usr/bin/env python
# encoding: utf-8

from django.core.management.base import BaseCommand
from django.core.cache import cache
from cache_utils.models import SimpleCacheSignals
from cache_utils.signals import cache_signals
class Command(BaseCommand):
    """
    Empty the cache
    """
    help = 'Empty the cache'
    
    def handle(self, *args, **options):
        
        SimpleCacheSignals.objects.all().delete()
        cache_signals.simplecache_signals = {}
        cache_signals.simplecache_signal_imports = {}
        cache.clear()
        