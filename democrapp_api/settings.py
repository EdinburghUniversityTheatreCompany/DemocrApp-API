from .base_settings import *
DEBUG = True

if DEBUG:
    MIDDLEWARE.append('democrapp_api.middleware.DevProxyMiddleware')
    UPSTREAM = "http://127.0.0.1:3000"