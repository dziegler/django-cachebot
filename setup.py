from setuptools import setup, find_packages
import cachebot
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = read('README.rst')


setup(
    name = "django-cachebot",
    version = cachebot.__version__,
    description = 'Automated caching and invalidation for the Django ORM',
    long_description = README,
    url = 'http://github.com/dziegler/django-cachebot',
    author = 'David Ziegler',
    author_email = 'david.ziegler@gmail.com',
    license = 'BSD',
    zip_safe = False,
    packages = find_packages(),
    package_data = {'cachebot':['patches/1-1-1-final-0/*.py']},
    install_requires = [
        'django==1.1.1',
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