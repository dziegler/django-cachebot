VERSION = (0, 2, 2)
__version__ = '.'.join(map(str, VERSION))

try:
    from cachebot.managers import patch_manager
    patch_manager()
except ImportError:
    print "ImportError, Django Manager was not patched"
