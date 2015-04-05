# Django settings for dierentheater project.

import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
PROJECT = os.path.split(PROJECT_PATH)[1]

import logging
from os.path import exists

if not exists(PROJECT_PATH + "/log/"):
    os.mkdir(PROJECT_PATH + "/log/")

if not exists(PROJECT_PATH + "/dump/"):
    os.mkdir(PROJECT_PATH + "/dump/")

logger = logging.getLogger('')
# only set loggers once
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(PROJECT_PATH + "/log/debug")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

CACHE_SCRAPING = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'dierentheater_pouet',
    }
}

TIME_ZONE = 'Europe/Brussels'
LANGUAGE_CODE = 'en-us'

# SITE_ID = 1

USE_I18N = True
USE_L10N = True

MEDIA_ROOT = ''
MEDIA_URL = ''

STATIC_ROOT = ''
STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = (
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'q8j8az4jeden%c5hb64vb)unwfq^h$3j+f8&g_+40jd0=l@#qs'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = PROJECT + '.urls'

TEMPLATE_DIRS = (
    PROJECT_PATH + '/templates',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    #'django.contrib.sites',
    'django.contrib.staticfiles',
    'lachambre',
    'scraper',
    'tastypie',
    'tastypie_nonrel',
    'scheduler',
    'django_crontab',
    'djcelery',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

CRONTAB_PYTHON_EXECUTABLE = PROJECT_PATH + "/ve/bin/python"

CRONJOBS = [
    ('1 10,17 * * *', 'scheduler.cron.check_for_new_documents'),
    ('3 3 * * 3', 'scheduler.cron.reparse_all_documents'),
]

try:
    from settings_local import *
except ImportError:
    pass
