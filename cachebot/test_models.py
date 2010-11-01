from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from cachebot.managers import CacheBotManager

class UniqueModel(models.Model):
    text = models.CharField(max_length=50, unique=True)
    objects = CacheBotManager(cache_get=True)
    
class NoCacheModel(models.Model):
    text = models.CharField(max_length=50)
    objects = CacheBotManager(cache_get=False)

class FirstModel(models.Model):
    text = models.CharField(max_length=50)
    objects = CacheBotManager(cache_get=True)

class SecondModel(models.Model):
    text = models.CharField(max_length=50)
    obj = models.ForeignKey(FirstModel)
    objects = CacheBotManager(cache_get=True)

class ThirdModel(models.Model):
    text = models.CharField(max_length=50)
    obj = models.ForeignKey(SecondModel)
    objects = CacheBotManager(cache_get=True)

class ManyModel(models.Model):
    text = models.CharField(max_length=50)
    firstmodel = models.ManyToManyField(FirstModel)
    thirdmodel = models.ManyToManyField(ThirdModel)
    objects = CacheBotManager(cache_get=True)

class GenericModel(models.Model):
    text = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    obj = generic.GenericForeignKey('content_type', 'object_id')
    objects = CacheBotManager(cache_get=True)
