"""ASGI config for Profile Manager project."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_manager.settings")
application = get_asgi_application()
