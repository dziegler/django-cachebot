
from south.db import db
from django.db import models
from cachebot.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'CacheBotSignals.table_name'
        db.add_column('cachebot_cachebotsignals', 'table_name', orm['cachebot.cachebotsignals:table_name'])
        
        # Deleting field 'CacheBotSignals.import_path'
        db.delete_column('cachebot_cachebotsignals', 'import_path')
        
        # Deleting field 'CacheBotSignals.module_name'
        db.delete_column('cachebot_cachebotsignals', 'module_name')
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'CacheBotSignals.table_name'
        db.delete_column('cachebot_cachebotsignals', 'table_name')
        
        # Adding field 'CacheBotSignals.import_path'
        db.add_column('cachebot_cachebotsignals', 'import_path', orm['cachebot.cachebotsignals:import_path'])
        
        # Adding field 'CacheBotSignals.module_name'
        db.add_column('cachebot_cachebotsignals', 'module_name', orm['cachebot.cachebotsignals:module_name'])
        
    
    
    models = {
        'cachebot.cachebotsignals': {
            'accessor_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'exclude': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lookup_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'table_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }
    
    complete_apps = ['cachebot']
