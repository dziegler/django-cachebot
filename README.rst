Django-cachebot
=================

Django-cachebot provides automated caching and invalidation for the Django ORM. 


Installation
************

1. Download django-cachebot and run::
    
    python setup.py install
    
2. Add ``cachebot`` to your ``INSTALLED_APPS``
3. Set a cache backend to one of the backends in ``cachebots.backends``, for instance:: 

    CACHE_BACKEND = 'cachebot.backends.memcached://127.0.0.1:11211/?timeout=2591000'

4. Run::
    
    python manage.py patch_django_manager

This will make CacheBotManager the default manager used by your Django app. Although this last step is optional, it's highly recommended because it adds a post_update signal. Queryset.update doesn't trigger save and delete signals, which are needed for invalidation. Also, if you turn caching off, your queryset behavior should be the same anyways.


Usage
******

Supposed you had a query that looked like this and you wanted to cache it::

    Photo.objects.filter(user=user, status=2)

Just add ``.cache()`` to the queryset chain like so::

    Photo.objects.cache().filter(user=user, status=2)

This query will get invalidated if any of the following conditions are met::

    1. One of the objects returned by the query is altered.
    2. user is altered.
    3. A Photo is modified and has status = 2.
    4. A Photo is modified and has user = user.

This invalidation criteria is probably too cautious, because we don't want to invalidate this cache every time a Photo with ``status = 2`` is saved. To fine tune the invalidation criteria, we can specify to only invalidate on certain fields. For example::
    
    Photo.objects.cache('user').filter(user=user, status=2)

This query will get invalidated if any of the following conditions are met::

    1. One of the objects returned by the query is altered.
    2. user is altered.
    3. A Photo is modified and has user = user.


django-cachebot can also handle select_related, forward relations, and reverse relations, ie::

    Photo.objects.select_related().cache('user').filter(user__username="david", status=2)
    
    Photo.objects.cache('user').filter(user__username="david", status=2)
    
    Photo.objects.cache('message__sender').filter(message__sender=user, status=2)


Settings
********

``CACHEBOT_CACHE_GET``  default: False

if ``CACHEBOT_CACHE_GET = True``, all objects.get queries will automatically be cached. This can be overridden at the manager level like so::
    
    class Photos(models.Model):
        ...
        objects = models.Manager(cache_get=True)


``CACHEBOT_CACHE_ALL``  default: False

if ``CACHEBOT_CACHE_ALL = True``, all queries will automatically be cached. This can be overridden at the manager level like so::
    
    class Photos(models.Model):
        ...
        objects = models.Manager(cache_all=True)


``CACHE_PREFIX``  default: ''

Suppose you have a development and production server sharing the same memcached server. Normally this is a bad idea because each server might be overwriting the other server's cache keys. If you add ``CACHE_PREFIX`` to your settings, all cache keys will have that prefix appended to them so you can avoid this problem.


Caveats (Important!)
********************

1. django-cachebot only works with Django 1.1.1. It's possible that it could work on other versions with some minor tweaking, but I haven't tested it.


2. Symmetric ManyToMany fields will break. Sorry, I'm working on it. If you have a model that uses one of these and you're using CacheBotManager as the default manager, you should fall back to the regular Django manager like so::

    from django.db.models.managers import DjangoManager
    class SomeModel(models.Model):
        ...
        objects = DjangoManager()


3. Adding/Removing objects with a ManyRelatedManager will not automatically invalidate. This is because signals for these types of operations are not in Django until 1.2. Until then, you'll need to manually invalidate these queries like so::

    from cachebot.signals import invalidate_object
    
    user.friends.add(friend)
    invalidate_object(user)
    invalidate_object(friend)


4. ``count()`` queries will not get cached. Still working on this, sorry.


5. If you're invalidating on a field that is in a range or exclude query, these queries will get invalidated when anything in the table changes. For example the following would get invalidated when anything on the User table changed::

    Photo.objects.cache('user').filter(user__in=users, status=2)

    Photo.objects.cache('user').exclude(user=user, status=2)
    

6. You should probably use a tool like django-memcache-status_ to check on the status of your cache. If memcache overfills and starts dropping keys, it's possible that your queries might not get invalidated.


7. It's possible that there are edge cases I've missed. django-cachebot is still in it's infancy, so you should still double check that your queries are getting cached and invalidated. Please let me know if you notice any weird discrepancies.


.. _django-memcache-status: http://github.com/bartTC/django-memcache-status

Dependecies
*************

* Django 1.1.1


Acknowledgements
****************

Thanks to the good folks at Mingle LLC and SocialHour for letting me open source this
