"""WSGI config for Profile Manager project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_manager.settings")
application = get_wsgi_application()
