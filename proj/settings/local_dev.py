'''
Settings that overwrite settings in __init__.py in development mode.
'''

import sys
globals().update(vars(sys.modules["settings"]))

CACHE_MIDDLEWARE_SECONDS = 0 # Really just prevents us form caching in dev environment.

ALLOWED_HOSTS += ['*']

if RUNNING_IN_DOCKER:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'NAME': 'postgres',
            'HOST': 'postgres',
            'PORT': 5432,
        }
    }
elif not DEV_IN_POSTGRES:
    # SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    # Use psql specified in .env
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'USER': os.getenv('DB_USER', False),
            'PASSWORD': os.getenv('DB_PASSWORD', False),
            'NAME': os.getenv('DB_NAME', False),
            'HOST': os.getenv('DB_HOST', False),
            'PORT': os.getenv('DB_PORT', False),
        }
    }
