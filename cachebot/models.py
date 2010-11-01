from django.db import models
from django import dispatch

from cachebot import conf

class CacheBotSignals(models.Model):
    table_name = models.CharField(max_length=100)
    accessor_path = models.CharField(max_length=100)
    lookup_type = models.CharField(max_length=20)
    exclude = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('table_name','accessor_path','lookup_type','exclude')
    
    def __unicode__(self):
        return u".".join((self.table_name,self.accessor_path,self.lookup_type,str(self.exclude)))
    
class CacheBotException(Exception):
    pass

post_update = dispatch.Signal(providing_args=["sender", "queryset"])

if conf.CACHEBOT_ENABLE_LOG:
    from django.core.signals import request_finished
    from django.core.cache import cache
    
    request_finished.connect(cache._logger.reset)

if conf.RUNNING_TESTS:
    from cachebot.test_models import *