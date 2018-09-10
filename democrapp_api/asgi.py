"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
from channels.layers import get_channel_layer
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "democrapp_api.settings")
django.setup()
channel_layer = get_channel_layer()
application = get_default_application()
