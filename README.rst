Django-cachebot
=================

Django-cachebot provides automated caching and invalidation for the Django ORM. More documentation and installation instructions coming soon!

Usage
*****

Articles.objects.filter(author=author).cache('author')

or

Articles.objects.filter(author=author).cache()


Dependecies
***********

* Django 1.1.1
