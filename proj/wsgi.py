"""
WSGI config for inia project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""
import sys
import os

from django.core.wsgi import get_wsgi_application

sys.path.append("/var/www/inia_v2/proj")
sys.path.append('/var/www/inia_v2/.virutalenv/lib/python3.6/site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()