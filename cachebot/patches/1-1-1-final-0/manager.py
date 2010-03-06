import copy

from django.db.models.query import QuerySet, EmptyQuerySet, insert_query
from django.db.models import signals
from django.db.models.fields import FieldDoesNotExist

def ensure_default_manager(sender, **kwargs):
    """
    Ensures that a Model subclass contains a default manager  and sets the
    _default_manager attribute on the class. Also sets up the _base_manager
    points to a plain Manager instance (which could be the same as
    _default_manager if it's not a subclass of Manager).
    """
    cls = sender
    if cls._meta.abstract:
        return
    if not getattr(cls, '_default_manager', None):
        # Create the default manager, if needed.
        try:
            cls._meta.get_field('objects')
            raise ValueError, "Model %s must specify a custom Manager, because it has a field named 'objects'" % cls.__name__
        except FieldDoesNotExist:
            pass
        cls.add_to_class('objects', Manager())
        cls._base_manager = cls.objects
    elif not getattr(cls, '_base_manager', None):
        default_mgr = cls._default_manager.__class__
        if (default_mgr is Manager or
                getattr(default_mgr, "use_for_related_fields", False)):
            cls._base_manager = cls._default_manager
        else:
            # Default manager isn't a plain Manager class, or a suitable
            # replacement, so we walk up the base class hierarchy until we hit
            # something appropriate.
            for base_class in default_mgr.mro()[1:]:
                if (base_class is Manager or
                        getattr(base_class, "use_for_related_fields", False)):
                    cls.add_to_class('_base_manager', base_class())
                    return
            raise AssertionError("Should never get here. Please report a bug, including your model and model manager setup.")

signals.class_prepared.connect(ensure_default_manager)

class DjangoManager(object):
    # Tracks each time a Manager instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self):
        super(DjangoManager, self).__init__()
        self._set_creation_counter()
        self.model = None
        self._inherited = False

    def contribute_to_class(self, model, name):
        # TODO: Use weakref because of possible memory leak / circular reference.
        self.model = model
        setattr(model, name, ManagerDescriptor(self))
        if not getattr(model, '_default_manager', None) or self.creation_counter < model._default_manager.creation_counter:
            model._default_manager = self
        if model._meta.abstract or (self._inherited and not self.model._meta.proxy):
            model._meta.abstract_managers.append((self.creation_counter, name,
                    self))
        else:
            model._meta.concrete_managers.append((self.creation_counter, name,
                self))

    def _set_creation_counter(self):
        """
        Sets the creation counter value for this instance and increments the
        class-level copy.
        """
        self.creation_counter = DjangoManager.creation_counter
        DjangoManager.creation_counter += 1

    def _copy_to_model(self, model):
        """
        Makes a copy of the manager and assigns it to 'model', which should be
        a child of the existing model (used when inheriting a manager from an
        abstract base class).
        """
        assert issubclass(model, self.model)
        mgr = copy.copy(self)
        mgr._set_creation_counter()
        mgr.model = model
        mgr._inherited = True
        return mgr

    #######################
    # PROXIES TO QUERYSET #
    #######################

    def get_empty_query_set(self):
        return EmptyQuerySet(self.model)

    def get_query_set(self):
        """Returns a new QuerySet object.  Subclasses can override this method
        to easily customize the behavior of the Manager.
        """
        return QuerySet(self.model)

    def none(self):
        return self.get_empty_query_set()

    def all(self):
        return self.get_query_set()

    def count(self):
        return self.get_query_set().count()

    def dates(self, *args, **kwargs):
        return self.get_query_set().dates(*args, **kwargs)

    def distinct(self, *args, **kwargs):
        return self.get_query_set().distinct(*args, **kwargs)

    def extra(self, *args, **kwargs):
        return self.get_query_set().extra(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.get_query_set().get(*args, **kwargs)

    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(**kwargs)

    def create(self, **kwargs):
        return self.get_query_set().create(**kwargs)

    def filter(self, *args, **kwargs):
        return self.get_query_set().filter(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        return self.get_query_set().aggregate(*args, **kwargs)

    def annotate(self, *args, **kwargs):
        return self.get_query_set().annotate(*args, **kwargs)

    def complex_filter(self, *args, **kwargs):
        return self.get_query_set().complex_filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        return self.get_query_set().exclude(*args, **kwargs)

    def in_bulk(self, *args, **kwargs):
        return self.get_query_set().in_bulk(*args, **kwargs)

    def iterator(self, *args, **kwargs):
        return self.get_query_set().iterator(*args, **kwargs)

    def latest(self, *args, **kwargs):
        return self.get_query_set().latest(*args, **kwargs)

    def order_by(self, *args, **kwargs):
        return self.get_query_set().order_by(*args, **kwargs)

    def select_related(self, *args, **kwargs):
        return self.get_query_set().select_related(*args, **kwargs)

    def values(self, *args, **kwargs):
        return self.get_query_set().values(*args, **kwargs)

    def values_list(self, *args, **kwargs):
        return self.get_query_set().values_list(*args, **kwargs)

    def update(self, *args, **kwargs):
        return self.get_query_set().update(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        return self.get_query_set().reverse(*args, **kwargs)

    def defer(self, *args, **kwargs):
        return self.get_query_set().defer(*args, **kwargs)

    def only(self, *args, **kwargs):
        return self.get_query_set().only(*args, **kwargs)

    def _insert(self, values, **kwargs):
        return insert_query(self.model, values, **kwargs)

    def _update(self, values, **kwargs):
        return self.get_query_set()._update(values, **kwargs)

from django.db.models.signals import post_save, pre_delete
from cachebot import CACHEBOT_CACHE_GET, CACHEBOT_CACHE_ALL, post_update


class Manager(DjangoManager):
    """
    Queries made through CacheBotManager will be cached.
    
    @cache_all - If True, all queries made with this manager will automatically be cached
    @cache_get - If True, all get queries will automatically be cached
    
    NOTE: It's recommended that you use the patch_django_manager command which
    will make this the default manager used by Django.
    """
    def __init__(self, cache_all=CACHEBOT_CACHE_ALL, cache_get=CACHEBOT_CACHE_GET, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)
        self.cache_all = cache_all
        self.cache_get = cache_get
    
    def contribute_to_class(self, cls, name):
        post_update.connect(self.post_update, sender=cls)
        post_save.connect(self.post_save, sender=cls)
        pre_delete.connect(self.pre_delete, sender=cls)
        return super(Manager, self).contribute_to_class(cls, name)
    
    def post_update(self, sender, instance, **kwargs):
        from cachebot.signals import post_update_cachebot
        post_update_cachebot(sender, instance)
    
    def post_save(self, sender, instance, **kwargs):
        from cachebot.signals import post_save_cachebot
        post_save_cachebot(sender, instance)
    
    def pre_delete(self, sender, instance, **kwargs):
        from cachebot.signals import pre_delete_cachebot
        pre_delete_cachebot(sender, instance)
    
    def get_query_set(self):
        from cachebot.queryset import CachedQuerySet
        if self.cache_all:
            return CachedQuerySet(self.model).cache()
        else:
            return CachedQuerySet(self.model)
    
    def get_or_create(self, *args, **kwargs):
        if self.cache_get:
            return self.get_query_set().cache().get_or_create(*args, **kwargs)
        else:
            return self.get_query_set().get_or_create(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self.cache_get:
            return self.get_query_set().cache().get(*args, **kwargs)
        else:
            return self.get_query_set().get(*args, **kwargs)

    def cache(self, *args):
        return self.get_query_set().cache(*args)
    
    def select_reverse(self, *args, **kwargs):
        return self.get_query_set().select_reverse(*args, **kwargs)
        

class ManagerDescriptor(object):
    # This class ensures managers aren't accessible via model instances.
    # For example, Poll.objects works, but poll_obj.objects raises AttributeError.
    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, type=None):
        if instance != None:
            raise AttributeError, "Manager isn't accessible via %s instances" % type.__name__
        return self.manager

class EmptyManager(Manager):
    def get_query_set(self):
        return self.get_empty_query_set()
