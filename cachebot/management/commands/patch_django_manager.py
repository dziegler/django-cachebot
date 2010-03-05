#!/usr/bin/env python
# encoding: utf-8

import os
import cachebot
import shutil

import django
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """
    Patch the default Django manager to use the cachebot manager
    """
    help = 'Empty the cache'
    
    def handle(self, *args, **options):
        
        version = '-'.join(map(str,django.VERSION))
        manager_path = os.path.join(django.__path__[0],'db','models','manager.py')
        cachebot_path = os.path.join(cachebot.__path__[0],'patches',version,'manager.py')

        if not os.path.exists(cachebot_path):
            raise Exception("Django version: %s not supported by django-cachebot" % django.VERSION)

        shutil.copyfile(cachebot_path,manager_path)

        print 'Cachebot successfully patched %s with %s' % (manager_path, cachebot_path)

