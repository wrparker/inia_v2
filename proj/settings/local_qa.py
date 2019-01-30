import sys
globals().update(vars(sys.modules["settings"]))

ALLOWED_HOSTS += ['iniav2-qa.herokuapp.com']

DEBUG = True
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
