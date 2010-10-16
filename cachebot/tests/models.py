from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class UniqueModel(models.Model):
    text = models.CharField(max_length=50, unique=True)

class NoCacheModel(models.Model):
    text = models.CharField(max_length=50)
    objects = models.Manager(cache_get=False)

class FirstModel(models.Model):
    text = models.CharField(max_length=50)

class SecondModel(models.Model):
    text = models.CharField(max_length=50)
    obj = models.ForeignKey(FirstModel)

class ThirdModel(models.Model):
    text = models.CharField(max_length=50)
    obj = models.ForeignKey(SecondModel)

class ManyModel(models.Model):
    text = models.CharField(max_length=50)
    firstmodel = models.ManyToManyField(FirstModel)
    thirdmodel = models.ManyToManyField(ThirdModel)

class GenericModel(models.Model):
    text = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    obj = generic.GenericForeignKey('content_type', 'object_id')

