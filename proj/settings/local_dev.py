'''
Settings that overwrite settings in __init__.py in development mode.
'''

import sys
globals().update(vars(sys.modules["settings"]))

CACHE_MIDDLEWARE_SECONDS = 0 # Really just prevents us form caching in dev environment.

ALLOWED_HOSTS += ['localhost', 'iniav2-qa.herokuapp.com']

# SQLite, uncomment to use this instead of mysql.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

