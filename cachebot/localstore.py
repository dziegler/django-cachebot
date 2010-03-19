#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Threadlocal OpenStruct-like cache."""

import re
import fnmatch
import threading
from cachebot.logger import cache_log

class LocalStore(threading.local):
    """A thread-local OpenStruct that can be used as a local cache.  Stole this from johnny-cache :)"""
    
    def __init__(self, **d):
        threading.local.__init__(self)
        for k,v in d.iteritems():
            threading.local.__setattr__(self, k, v)
    # dictionary API
    def __getitem__(self, key):
        return self.__dict__[key]
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    def __delitem__(self, key):
        if key in self.__dict__:
            del self.__dict__[key]
    def __iter__(self):
        return iter(self.__dict__)
    def __len__(self): return len(self.__dict__)
    def keys(self): return self.__dict__.keys()
    def values(self): return self.__dict__.values()
    def items(self): return self.__dict__.items()
    def iterkeys(self): return self.__dict__.iterkeys()
    def itervalues(self): return self.__dict__.itervalues()
    def iteritems(self): return self.__dict__.iteritems()
    def get(self, *args): return self.__dict__.get(*args)
    def update(self, d): self.__dict__.update(d)
    def setdefault(self, name, value): return self.__dict__.setdefault(name, value)
    def mget(self, pat=None):
        """Get a dictionary mapping of all k:v pairs with key matching
        glob style expression `pat`."""
        if pat is None: return {}
        expr = re.compile(fnmatch.translate(pat))
        m = {}
        for key in self.keys():
            #make sure the key is a str first
            if type(key) in (str, unicode):
                if expr.match(key):
                    m[key] = self[key]
        return m

    def clear(self, pat=None):
        """Minor diversion with built-in dict here;  clear can take a glob
        style expression and remove keys based on that expression."""
        if pat is None:
            return self.__dict__.clear()
        expr = re.compile(fnmatch.translate(pat))
        for key in self.keys():
            #make sure the key is a str first
            if type(key) in (str, unicode):
                if expr.match(key):
                    del self.__dict__[key]

    def __repr__(self): return repr(self.__dict__)
    def __str__(self): return str(self.__dict__)

local = LocalStore()


def add(func, instance, key, value, timeout=None):
    local[key] = value
    return func(instance, key, value, timeout)

def get(func, instance, key, default=None):
    value = local.get(key)
    if value is None:
        value = func(instance, key, default)
        local[key] = value
    return value

def set(func, instance, key, value, timeout=None):
    local[key] = value
    func(instance, key, value, timeout)

def delete(func, instance, key):
    if key in local:
        del local[key]
    func(instance, key)

def get_many(func, instance, keys):
    value_dict = {}
    new_keys = []
    for key in keys:
        value = local.get(key)
        value_dict[key] = value
        if value is None:
            new_keys.append(key)
    
    if new_keys:
        from_cache = func(instance, new_keys)
        local.update(from_cache)
        value_dict.update(from_cache)
    return value_dict

def set_many(func, instance, mapping, timeout=None):
    local.update(mapping)
    func(instance, mapping, timeout)

def close(func, instance, **kwargs):
    local.clear()
    func(instance, **kwargs)

def incr(func, instance, key, delta=1):
    return func(instance, key, delta)

def decr(func, instance, key, delta=1):
    return func(instance, key, delta)
 
def delete_many(func, instance, keys):
    for key in keys:
        if key in local:
            del local[key]
    func(instance, keys)

def clear(func, instance):
    local.clear()
    func(instance)
