import inspect
import threading
from itertools import chain

from django.conf import settings

CONCURRENCY_LEVEL = 3

class ConcurrentTestMetaClass(type):
    
    def __init__(cls, name, bases, ns):
        if settings.DATABASE_ENGINE == 'sqlite3':
            from warnings import warn
            warn("Concurrency tests will not run with DATABASE_ENGINE == 'sqlite3'")
        else:
            for key, value in chain(ns.iteritems(),parent_ns_gen(bases)):
                if key.startswith('test_') and inspect.isfunction(value): 
                    setattr(cls, key, test_concurrently(CONCURRENCY_LEVEL)(value))
            

def parent_ns_gen(classes):
    for cls in classes:
        ns = dir(cls)
        for attr in ns:
            value = getattr(cls, attr)
            if inspect.ismethod(value):
                yield attr, value


def test_concurrently(times):
    """ 
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.
    """
    def test_concurrently_decorator(test_func):
        if settings.DATABASE_ENGINE != 'sqlite3':
            def wrapper(*args, **kwargs):
                exceptions = []
                def call_test_func():
                    try:
                        test_func(*args, **kwargs)
                    except Exception, e:
                        exceptions.append(e)
                        raise
                threads = []
                for i in range(times):
                    threads.append(threading.Thread(target=call_test_func))
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                if exceptions:
                    raise Exception('test_concurrently intercepted %s exceptions: %s' % (len(exceptions), exceptions))
            return wrapper
        else:
            return test_func
    return test_concurrently_decorator   
