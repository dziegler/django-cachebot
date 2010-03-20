from itertools import chain, ifilter

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.conf import settings
from django.db import connection
from django.db.models import get_models
from django.db.models.query import QuerySet, ValuesQuerySet, ITER_CHUNK_SIZE
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, ReverseManyRelatedObjectsDescriptor, ManyRelatedObjectsDescriptor, ReverseSingleRelatedObjectDescriptor
from django.db.models.sql.constants import LOOKUP_SEP
from django.db.models.sql.where import WhereNode
from django.utils.hashcompat import md5_constructor


from cachebot.signals import cache_signals
from cachebot.utils import get_invalidation_key, get_values
from cachebot import CACHE_SECONDS, CACHEBOT_TABLE_BLACKLIST, post_update
from cachebot.models import CacheBotException
from cachebot.backends import version_key

RUNNING_TESTS = getattr(settings, 'RUNNING_TESTS', False)

class CacheBot(object):
    
    def __init__(self, queryset, extra_args='', invalidation_only=False):
        # have to call clone for some reason
        self.queryset = queryset._clone()
        self.iterator = super(self.queryset.__class__, self.queryset).iterator
        self.result_key = queryset.get_cache_key(extra_args)
        
        # set this to True when we don't want to cache the entire queryset, but we do want to be able to invalidate this result_key
        # (when performing count for example)
        self.invalidation_only = invalidation_only
        
    def __iter__(self):
        results = cache.get(self.result_key)
        if results is not None:
            for obj in results:
                if RUNNING_TESTS:
                    obj = self._set_field(obj,'from_cache', True)
                yield obj
            raise StopIteration
        
        results = []
        cache_query = getattr(self.queryset, '_cache_query', False)
        pk_name = self.queryset.model._meta.pk.name   
        self.queryset._fill_select_reverse_cache()
        
        reversemapping_keys = self.queryset._reversemapping.keys()
        reversemapping_keys.sort()
        
        for obj in self.iterator():    
            for related_name in reversemapping_keys:
                reversemap = self.queryset._target_maps[related_name]
                related_split = related_name.split(LOOKUP_SEP)
                for related_obj, related_field in self._nested_select_reverse(obj, related_split):
                    val = reversemap.get(get_values(related_obj, pk_name),[])
                    related_obj = self._set_field(related_obj, related_field, val)
                        
            if cache_query:
                results.append(obj)
            if RUNNING_TESTS:
                obj = self._set_field(obj,'from_cache', False)
            yield obj
            
        if cache_query:
            self.cache_results(results)
    
    def _nested_select_reverse(self, obj, related_split):
        related_field = related_split.pop(0)
        try:
            related_obj = getattr(obj, related_field)
            if hasattr(related_obj, '__iter__'):
                for related_obj_ in related_obj:                    
                    for nested_obj, related_field in self._nested_select_reverse(related_obj_, related_split):
                        yield nested_obj, related_field
            else:
                for nested_obj, related_field in self._nested_select_reverse(related_obj, related_split):
                    yield nested_obj, related_field
        except AttributeError:
            yield obj, related_field
    
    def _is_valid_flush_path(self, accessor_path):
        return not self.queryset._flush_fields or accessor_path in self.queryset._flush_fields or accessor_path+'_id' in self.queryset._flush_fields
    
    def cache_results(self, results):
        """
        Create invalidation signals for these results in the form of CacheBotSignals.
        A CacheBotSignal stores a model and it's accessor path to self.queryset.model.
        """
        # cache the results     
        if results and not self.invalidation_only:
            cache.set(self.result_key, results, CACHE_SECONDS)
        
        invalidation_dict = {}
        
        for child, negate in self.queryset._get_where_clause(self.queryset.query.where):     
            (table_alias, field_name, db_type), lookup_type, value_annotation, params = child
            for model_class, accessor_path in self._get_join_paths(table_alias, field_name):
                if model_class is None:
                    continue
                if self._is_valid_flush_path(accessor_path):  
                    cache_signals.register(model_class, accessor_path, lookup_type, negate=negate)
                    invalidation_key = get_invalidation_key(
                        model_class._meta.db_table, 
                        accessor_path = accessor_path, 
                        lookup_type = lookup_type, 
                        negate = negate, 
                        value = params, save=True)
                    invalidation_dict[invalidation_key] = None
                
                join_to_tables = ifilter(lambda x: x[0] == model_class._meta.db_table, self.queryset.query.join_map.keys())
                for join_tuple in join_to_tables:
                    if self._is_valid_flush_path(accessor_path): 
                        model_class = self.queryset._get_model_class_from_table(join_tuple[1])
                        cache_signals.register(model_class, join_tuple[3], lookup_type, negate=negate)
                        invalidation_key = get_invalidation_key(
                            model_class._meta.db_table, 
                            accessor_path = join_tuple[3], 
                            lookup_type = lookup_type, 
                            negate = negate, 
                            value = params, save=True)
                        invalidation_dict[invalidation_key] = None
        invalidation_dict.update(dict([(key,None) for key in self.get_invalidation_keys(results)]))
        invalidation_dict.update(cache.get_many(invalidation_dict.keys()))

        for flush_key, flush_list in invalidation_dict.iteritems():
            if flush_list is None:
                invalidation_dict[flush_key] = set([self.result_key])
            else:
                invalidation_dict[flush_key].add(self.result_key)
        cache.set_many(invalidation_dict, CACHE_SECONDS)
    
    def _get_join_paths(self, table_alias, accessor_path):
        try:
            model_class = self.queryset._get_model_class_from_table(table_alias)
        except CacheBotException:
            
            try:
                # this is a many to many field
                model_class = [f.rel.to for m in get_models() for f in m._meta.local_many_to_many if f.m2m_db_table() == table_alias][0]
                accessor_path = model_class._meta.pk.attname
            except IndexError:
                # this is an inner join
                model_class = None
                accessor_path = None
            
        yield model_class, accessor_path

        join_from_tables = ifilter(lambda x: x[1] == table_alias, self.queryset.query.join_map.keys())
        for join_tuple in join_from_tables:
            if join_tuple[0]:
                for model_class, join_accessor_path in self._get_join_paths(join_tuple[0], join_tuple[2]):
                    if model_class is None:
                        continue
                    if join_accessor_path == model_class._meta.pk.attname:
                        for attname, related in self.queryset._get_reverse_relations(model_class):
                            join_accessor_path = attname
                            yield model_class, LOOKUP_SEP.join((join_accessor_path, accessor_path))
                    elif join_accessor_path.split(LOOKUP_SEP)[-1] == 'id':
                        accessor_path_split = join_accessor_path.split(LOOKUP_SEP) 
                        join_accessor_path = LOOKUP_SEP.join(accessor_path_split[:-1])
                        yield model_class, LOOKUP_SEP.join((join_accessor_path, accessor_path))
                    elif join_accessor_path.endswith('_id'):
                        join_accessor_path = join_accessor_path[:-3]
                        yield model_class, LOOKUP_SEP.join((join_accessor_path, accessor_path))
                    else:
                        yield model_class, LOOKUP_SEP.join((join_accessor_path, accessor_path))


    def get_invalidation_keys(self, results):
        """
        Iterates through a list of results, and returns an invalidation key for each result. If the
        query spans multiple tables, also return invalidation keys of any related rows.
        """
        related_fields = self.queryset._related_fields
        select_reverse_keys = self.queryset._target_maps.keys()
        for obj in results:
            for field, model_class in related_fields.iteritems():
                pk_name = model_class._meta.pk.attname
                cache_signals.register(model_class, pk_name, 'exact')
                for value in get_values(obj, field):
                    invalidation_key = get_invalidation_key(
                        model_class._meta.db_table, 
                        accessor_path = pk_name, 
                        value = value, save=True)
                    yield invalidation_key
        
    def _set_field(self, obj, field, value):
        """Helper method to handle setting values in a CachedQuerySet or ValuesQuerySet object"""
        try:
            obj[field] = value
        except TypeError:
            setattr(obj, field, value)
        return obj

        
class CachedQuerySetMixin(object):              
    
    def get_cache_key(self, extra_args=''):
        """Cache key used to identify this query"""
        query, params = self.query.as_sql()
        query_string = (query % params).strip()
        base_key = md5_constructor('.'.join(('cachebot:result_key',str(self.__class__),query_string, extra_args))).hexdigest()
        return version_key('.'.join((self.model._meta.db_table,base_key)))
    
    def _get_model_class_from_table(self, table):
        """Helper method that accepts a table name and returns the Django model class it belongs to"""
        try:
            return [m for m in get_models() if connection.introspection.table_name_converter(m._meta.db_table) in map(connection.introspection.table_name_converter,[table])][0]
        except IndexError:
            raise CacheBotException("Could not find model for table %s" % table)
    
    @property
    def _related_fields(self):
        """Returns the primary key accessor name and model class for any table this query spans."""
        related_fields = {
            self.model._meta.pk.attname: self._get_model_class_from_table(self.model._meta.db_table)
        }
        for attname, model_class in self._get_related_models(self.model):
            related_fields[attname] = model_class
        return related_fields
    
    def _get_related_models(self, parent_model):
        """
        A recursive function that looks at what tables this query spans, and
        finds that table's primary key accessor name and model class.
        """
        related_models = set()
        rev_reversemapping = dict([(v,k) for k,v in self._reversemapping.iteritems()])
        if rev_reversemapping:
            for attname, related in self._get_reverse_relations(parent_model):
                related_models.add((rev_reversemapping[attname], related.model))

        for field in parent_model._meta.fields:
            if field.rel and field.rel.to._meta.db_table in self.query.tables:
                related_models.add((field.attname, field.rel.to))
        
        for attname, model_class in related_models:
            yield attname, model_class
            if attname.endswith("_id"):
                attname = attname[:-3]
                for join_attname, model_class in self._get_related_models(model_class):
                    yield LOOKUP_SEP.join((attname,join_attname)), model_class
    
    def _get_reverse_relations(self, model_class):
        for related in chain(model_class._meta.get_all_related_objects(), model_class._meta.get_all_related_many_to_many_objects()):
            if related.opts.db_table in self.query.tables:
                related_name = related.get_accessor_name()
                yield related_name, related
                for attname, join_related in self._get_reverse_relations(related.model):
                    yield LOOKUP_SEP.join((related_name + '_cache', attname)), join_related
                
    def _base_clone(self, queryset, klass=None, setup=False, **kwargs):
        """
        Clones a CachedQuerySet. If caching and this is a ValuesQuerySet, automatically add any
        related foreign relations to the select fields so we can invalidate this query.
        """
        cache_query = kwargs.get('_cache_query', getattr(self, '_cache_query', False))
        kwargs['_cache_query'] = cache_query
        if not hasattr(self, '_reversemapping'):
            self._reversemapping = {}

        if cache_query and isinstance(queryset, ValuesQuerySet):
            fields = kwargs.get('_fields', getattr(self,'_fields', ()))
            if fields:
                fields = list(fields)
            else:
                fields = [f.attname for f in self.model._meta.fields]
            
            for related_field in self._related_fields.keys():
                if related_field not in fields and self._is_valid_field(related_field):
                    fields.append(related_field)
                    setup = True
            kwargs['_fields'] = tuple(fields)
        
        if cache_query:
            reversemapping = {}
            for attname, related in self._get_reverse_relations(self.model):
                reversemapping[attname + '_cache'] = attname
            kwargs['_reversemapping'] = reversemapping

        clone = super(queryset.__class__, queryset)._clone(klass=klass, setup=setup, **kwargs)
        if not hasattr(clone, '_cache_query'):
            clone._cache_query = getattr(self, '_cache_query', False)
        if not hasattr(clone, '_reversemapping'):
            clone._reversemapping = getattr(self, '_reversemapping', {})
        if not hasattr(clone, '_target_maps'):
            clone._target_maps = getattr(self, '_target_maps', {})
        if not hasattr(clone, '_flush_fields'):
            clone._flush_fields = getattr(self, '_flush_fields', ())
            
        return clone
    
    def _is_valid_field(self, field, allow_m2m=True):
        """A hackish way to figure out if this is a field or reverse foreign relation"""
        try:
            self.query.setup_joins(field.split(LOOKUP_SEP), self.query.get_meta(), self.query.get_initial_alias(), False, allow_m2m, True)
            return True
        except FieldError:
            return False
    
    def _get_select_reverse_model(self, model_class, lookup_args):
        model_arg = lookup_args.pop(0)
        try:
            descriptor = getattr(model_class, model_arg)
        except AttributeError:
            # for nested reverse relations
            descriptor = getattr(model_class, self._reversemapping[model_arg])
        if lookup_args:
            if isinstance(descriptor, ForeignRelatedObjectsDescriptor):
                return self._get_select_reverse_model(descriptor.related.model, lookup_args)
            elif isinstance(descriptor, ReverseManyRelatedObjectsDescriptor):
                return self._get_select_reverse_model(descriptor.field.rel.to, lookup_args)
            elif isinstance(descriptor, ManyRelatedObjectsDescriptor):
                return self._get_select_reverse_model(descriptor.related.model, lookup_args)
        else:
            return model_class, model_arg
            
    def _fill_select_reverse_cache(self):
        reversemapping = getattr(self, '_reversemapping', {})
        target_maps = {}
        if reversemapping:
            if isinstance(self, ValuesQuerySet):
                pk_name = self.model._meta.pk.name
                queryset = self._clone().values(pk_name)
            else:
                queryset = self._clone()
            
            # Need to clear any limits on this query because of http://code.djangoproject.com/ticket/10099
            queryset.query.clear_limits()
            
            # we need to iterate through these in a certain order
            reversemapping_keys = self._reversemapping.keys()
            reversemapping_keys.sort()
            
            for key in reversemapping_keys:
                target_map= {}
                val = self._reversemapping[key]

                model_class, model_arg = self._get_select_reverse_model(self.model, val.split(LOOKUP_SEP))
                if hasattr(model_class,  key):
                    raise ImproperlyConfigured,  "Model %s already has an attribute %s" % (model_class,  key)  
                    
                descriptor = getattr(model_class,  model_arg)
                if isinstance(descriptor, ForeignRelatedObjectsDescriptor):
                    rel = descriptor.related
                    related_queryset = rel.model.objects.filter(**{rel.field.name+'__in':queryset}).all()
                    for item in related_queryset.iterator():
                        target_map.setdefault(getattr(item, rel.field.get_attname()), []).append(item)
                elif isinstance(descriptor, ReverseManyRelatedObjectsDescriptor):
                    field = descriptor.field
                    related_queryset = field.rel.to.objects.filter(**{field.rel.related_name +'__in':queryset}).all().extra( \
                                select={'main_id': field.m2m_db_table() + '.' + field.m2m_column_name()})
                    for item in related_queryset.iterator():
                        target_map.setdefault(getattr(item, 'main_id'), []).append(item)
                elif isinstance(descriptor, ManyRelatedObjectsDescriptor):
                    rel = descriptor.related
                    related_queryset = rel.model.objects.filter(**{rel.field.name +'__in':queryset}).all().extra( \
                                select={'main_id': rel.field.m2m_db_table() + '.' + rel.field.m2m_column_name()}) 
                    for item in related_queryset.iterator():
                        target_map.setdefault(getattr(item, 'main_id'), []).append(item)
                else:
                    raise ImproperlyConfigured, "Unsupported mapping %s %s" % (val, descriptor)
                target_maps[key]=target_map
        self._target_maps = target_maps   

    def _get_where_clause(self, node):
        for child in node.children:
            if isinstance(child, WhereNode):
                for child_node, negated in self._get_where_clause(child):
                    yield child_node, negated
            else:
                yield child, node.negated

    def select_reverse(self, *reversemapping, **kwargs):
        """
        Like select_related, but follows reverse and m2m foreign relations. Example usage:
        
        article_list = Article.objects.select_reverse('book_set')

        for article in article_list:
            # these will return the same queryset
            print article.book_set_cache
            print article.book_set.all() 
        
        If there are N Articles belonging to K Books, this will return N + K results. The actual
        reversed book queryset would be cached in article_list._target_maps['book_set_cache']
        
        Nested queries are also supported:
        
        article_list = Article.objects.select_reverse('book_set','book_set__publisher_set')

        for article in article_list:
            
            # these will return the same queryset
            for book in article.book_set_cache:
                print book.publisher_set_cache
                print book.publisher_set.all()
            
            # these will return the same queryset
            for book in article.book_set.all():
                print book.publisher_set_cache
                print book.publisher_set.all()
             
        
        This could probably be better, because it does a SQL query for each reverse or m2m foreign
        relation in select_reverse, i.e. 
        
        Article.objects.select_reverse('book_set','author_set')
        
        will be 3 SQL queries. This is a lot better than the alternative of a separate SQL query
        for each article in article_list, but it'd be nice to be able to do the whole thing in 1.
        
        Based off django-selectreverse: http://code.google.com/p/django-selectreverse/
        """
        _reversemapping = dict([(key +'_cache', key) for key in reversemapping])
        return self._clone(_reversemapping=_reversemapping, **kwargs)
        
    def values(self, *fields):
        return self._clone(klass=CachedValuesQuerySet, setup=True, _fields=fields)
    
    def cache(self, *flush_fields):
        """
        Cache this queryset. If this is a query over reverse foreign relations, those fields will automatically
        be added to select_reverse, because we need them for invalidation. Do not cache queries on
        tables in CACHEBOT_TABLE_BLACKLIST
        """
        _cache_query = self.model._meta.db_table not in CACHEBOT_TABLE_BLACKLIST
            
        return self._clone(setup=True, _cache_query=_cache_query, _flush_fields=flush_fields)
    
    def get(self, *args, **kwargs):
        if self.model.objects.cache_get:
            return super(CachedQuerySetMixin, self.cache()).get(*args, **kwargs)
        else:
            return super(CachedQuerySetMixin, self).get(*args, **kwargs)
    
    def count(self):
        # don't cache counts for now
        return self.query.get_count()
    
        
class CachedQuerySet(CachedQuerySetMixin, QuerySet):
    
    def iterator(self):    
        for obj in CacheBot(self):
            yield obj
        raise StopIteration
    
    def _clone(self, klass=None, setup=False, **kwargs):
        return self._base_clone(self, klass=klass, setup=setup, **kwargs)
        
    def update(self, **kwargs):
        super(CachedQuerySet, self).update(**kwargs)
        post_update.send(sender=self.model, instance=self)
        
        
class CachedValuesQuerySet(CachedQuerySetMixin, ValuesQuerySet):
    
    def iterator(self):      
        for obj in CacheBot(self):
            yield obj
        raise StopIteration
    
    def _clone(self, klass=None, setup=False, **kwargs):
        return self._base_clone(self, klass=klass, setup=setup, **kwargs)
    
    def update(self, **kwargs):
        super(CachedValuesQuerySet, self).update(**kwargs)
        post_update.send(sender=self.model, instance=self)
        
