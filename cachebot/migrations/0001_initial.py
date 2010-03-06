
from south.db import db
from django.db import models
from cachebot.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'CacheBotSignals'
        db.create_table('cachebot_cachebotsignals', (
            ('id', orm['cachebot.CacheBotSignals:id']),
            ('import_path', orm['cachebot.CacheBotSignals:import_path']),
            ('module_name', orm['cachebot.CacheBotSignals:module_name']),
            ('accessor_path', orm['cachebot.CacheBotSignals:accessor_path']),
            ('lookup_type', orm['cachebot.CacheBotSignals:lookup_type']),
            ('exclude', orm['cachebot.CacheBotSignals:exclude']),
        ))
        db.send_create_signal('cachebot', ['CacheBotSignals'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'CacheBotSignals'
        db.delete_table('cachebot_cachebotsignals')
        
    
    
    models = {
        'cachebot.cachebotsignals': {
            'accessor_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'exclude': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_path': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'lookup_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }
    
    complete_apps = ['cachebot']
