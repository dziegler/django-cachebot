#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Threadlocal OpenStruct-like cache."""

import re
import fnmatch
import threading
from cachebot.logger import cache_log


class LocalStore(threading.local):
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.storage = {}
        self.set_many = {}
        self.delete_many = set()


class DeferredCache(object):
    
    def __init__(self):
        local.reset()
        
    def commit(self, instance):
        if local.delete_many:
            instance.delete_many(local.delete_many, commit=True)
        for timeout, mapping in local.set_many.iteritems():
            if mapping:
                instance.set_many(mapping, timeout, commit=True)
        local.reset()
    
    
    # deferred cache methods
    def add(self, func, instance, key, value, timeout=None):
        cache_val = local.storage.get(key)
        if cache_val is None and key not in local.delete_many:
            local.storage[key] = value
            return func(instance, key, value, timeout=None)
        else:
            return False

    def get(self, func, instance, key, default=None):
        value = local.storage.get(key)
        if value is None and key not in local.delete_many:
            value = func(instance, key, default)
            local.storage[key] = value
        return value

    def set(self, func, instance, key, value, timeout=None, commit=False):
        if commit:
            func(instance, key, value, timeout)
        else:
            local.storage[key] = value
            local.set_many.setdefault(timeout, {})
            local.set_many[timeout][key] = value

    def delete(self, func, instance, key, commit=False):
        if commit:
            func(instance, key)
        else:
            if key in local.storage:
                del local.storage[key]
            local.delete_many.add(key)
    
    def get_many(self, func, instance, keys):
        value_dict = {}
        new_keys = []
        for key in keys:
            value = local.storage.get(key)
            value_dict[key] = value
            if value is None and key not in local.delete_many:
                new_keys.append(key)
    
        if new_keys:
            from_cache = func(instance, new_keys)
            local.storage.update(from_cache)
            value_dict.update(from_cache)
        return value_dict

    def set_many(self, func, instance, mapping, timeout=None, commit=False):
        if commit:
            func(instance, mapping, timeout)
        else:
            local.storage.update(mapping)
            local.set_many.setdefault(timeout, {})
            local.set_many[timeout].update(mapping)

    def close(self, func, instance, **kwargs):
        self.commit(instance)
        func(instance, **kwargs)
 
    def delete_many(self, func, instance, keys, commit=False):
        if commit:
            func(instance, keys)
        else:
            for key in keys:
                if key in local.storage:
                    del local.storage[key]
            local.delete_many.update(keys)

    def clear(self, func, instance):
        local.reset()
        func(instance)
    
    # pass through methods
    
    def incr(self, func, instance, *args, **kwargs):
        return func(instance, *args, **kwargs)

    def decr(self, func, instance, *args, **kwargs):
        return func(instance, *args, **kwargs)
    
    def append(self, func, instance, *args, **kwargs):
        return func(instance, *args, **kwargs)
    
    def prepend(self, func, instance, *args, **kwargs):
        return func(instance, *args, **kwargs)

local = LocalStore()
deferred_cache = DeferredCache()