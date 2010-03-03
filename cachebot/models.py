from django.db import models

class SimpleCacheSignals(models.Model):
    import_path = models.CharField(max_length=100)
    module_name = models.CharField(max_length=50)
    accessor_path = models.CharField(max_length=100)
    lookup_type = models.CharField(max_length=20)
    exclude = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('import_path','module_name','accessor_path')
    
    def __unicode__(self):
        return u".".join((self.import_path,self.module_name,self.accessor_path))
    
class SimpleCacheException(Exception):
    pass
    