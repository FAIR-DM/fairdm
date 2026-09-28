"""WSGI application for the demo portal."""

import os

from django.core.wsgi import get_wsgi_application

# A DJANGO_SETTINGS_MODULE already in the environment wins.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
