
"""
WSGI config for inia project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""
import sys
import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler


sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)),'.virutalenv/lib/python3.6/site-packages'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

if settings.DEBUG:
    application = StaticFilesHandler(get_wsgi_application())
else:
    application = get_wsgi_application()
