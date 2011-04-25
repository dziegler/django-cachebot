Django-cachebot
=================

Django-cachebot provides automated caching and invalidation for the Django ORM. 

Installation
************

1. ``easy_install django-cachebot`` or ``pip install django-cachebot``
    
2. Add ``cachebot`` to your ``INSTALLED_APPS``

3. Set a cache backend to one of the backends in ``cachebots.backends``, for instance:: 

    CACHES = {
        'default': {
            'BACKEND': 'cachebot.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

Current supported backends are:: 

    cachebot.backends.dummy.DummyCache
    cachebot.backends.memcached.MemcachedCache
    cachebot.backends.memcached.PyLibMCCache


4. If you want to add caching to a model, the model's manager needs to be ``CacheBotManager`` or a subclass of it, e.g::
    
    from django.db import models
    from cachebot.managers import CacheBotManager
    
    class Author(models.Model):
        name = models.CharField(max_length=50)
        objects = CacheBotManager()
    
    class BookManager(CacheBotManager):
        
        def for_author(self, name):
            return self.filter(author__name=name)
    
    class Book(models.Model):
        title = models.CharField(max_length=50)
        author = models.ForeignKey(Author)
        objects = BookManager()
 
Usage
******

By default, all ``get`` queries for ``CacheBotManager`` will be cached::
    
    photo = Photo.objects.get(user=user)

If you don't want this behavior, call ``CacheBotManager(cache_get=False)`` when defining the manager, or to change this globally set ``CACHEBOT_CACHE_GET=False`` in settings.

------------

For more complex queries, suppose you had a query that looked like this and you wanted to cache it::

    Photo.objects.filter(user=user, status=2)

Just add ``.cache()`` to the queryset chain like so::

    Photo.objects.cache().filter(user=user, status=2)

This query will get invalidated if any of the following conditions are met::

    1. One of the objects returned by the query is altered.
    2. The user is altered.
    3. A Photo is modified and has status = 2.
    4. A Photo is modified and has user = user.

This invalidation criteria is probably too cautious, because we don't want to invalidate this cache every time a Photo with ``status = 2`` is saved. To fine tune the invalidation criteria, we can specify to only invalidate on certain fields. For example::
    
    Photo.objects.cache('user').filter(user=user, status=2)

This query will get invalidated if any of the following conditions are met::

    1. One of the objects returned by the query is altered.
    2. The user is altered.
    3. A Photo is modified and has user = user.


django-cachebot can also handle select_related, forward relations, and reverse relations, ie::

    Photo.objects.select_related().cache('user').filter(user__username="david", status=2)
    
    Photo.objects.cache('user').filter(user__username="david", status=2)
    
    Photo.objects.cache('message__sender').filter(message__sender=user, status=2)


Settings
********

 - ``CACHEBOT_CACHE_GET``
 
   - default: ``True``
   - If set to ``True``, ``CacheBotManager`` will be called with ``cache_get=True`` by default.

 - ``CACHEBOT_TABLE_BLACKLIST``
 
   - default: ('django_session', 'django_content_type', 'south_migrationhistory')
   - A list of tables that cachebot should ignore.
   

Caveats (Important!)
********************

1. Adding/Removing objects with a ManyRelatedManager will not automatically invalidate. You'll need to manually invalidate these queries like so::

    from cachebot.signals import invalidate_object
    
    user.friends.add(friend)
    invalidate_object(user)
    invalidate_object(friend)

2. ``count()`` queries will not get cached.

3. If you're invalidating on a field that is in a range or exclude query, these queries will get invalidated when anything in the table changes. For example the following would get invalidated when anything on the User table changed::

    Photo.objects.cache('user').filter(user__in=users, status=2)

    Photo.objects.cache('user').exclude(user=user, status=2)
    

4. You should probably use a tool like django-memcache-status_ to check on the status of your cache. If memcache overfills and starts dropping keys, it's possible that your queries might not get invalidated.

5. .values_list() doesn't cache yet. You should do something like this instead::

    [photo['id'] for photo in Photo.objects.cache('user').filter(user=user).values('id')]


.. _django-memcache-status: http://github.com/bartTC/django-memcache-status

Dependencies
*************

* Django 1.3

If you use Django 1.2, you can use django-cachebot version 0.3.1

