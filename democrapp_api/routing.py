from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from Meeting.ui_consumer import UIConsumer

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    "websocket": UIConsumer
})
