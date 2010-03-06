#!/usr/bin/env python
# encoding: utf-8

from django.core.management.base import BaseCommand
from django.core.cache import cache
from cachebot.models import CacheBotSignals
from cachebot.signals import cache_signals

class Command(BaseCommand):
    """
    Empty the cache
    """
    help = 'Empty the cache'
    
    def handle(self, *args, **options):
        
        CacheBotSignals.objects.all().delete()
        cache.clear()
        