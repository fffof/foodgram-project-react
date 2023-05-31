from os import environ

from split_settings.tools import include, optional

ENV = environ.get('DJANGO_ENV') or 'development'

base_settings = [
    'components/common.py',  # standard django settings
    'components/database.py',
    optional('environments/local.py'),
]
include(*base_settings)
