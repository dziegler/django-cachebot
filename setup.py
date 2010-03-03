from setuptools import setup, find_packages
import cachebot

setup(
    name = "django-cachebot",
    version = cachebot.__version__,
    description = 'Automated caching and invalidation for the Django ORM',
    author = 'David Ziegler',
    author_email = 'david.ziegler@gmail.com',
    license = 'BSD',
    zip_safe = False,
    packages = find_packages(),
    requires = [
        'django==1.1',
    ],
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)