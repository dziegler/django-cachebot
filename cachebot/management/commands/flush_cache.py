#!/usr/bin/env python
# encoding: utf-8

from django.core.management.base import BaseCommand
from cachebot.utils import flush_cache

class Command(BaseCommand):
    """
    Empty the cache
    """
    help = 'Empty the cache'
    
    def handle(self, *args, **options):
        
        flush_cache(hard=True)