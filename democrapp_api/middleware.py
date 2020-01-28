from urllib import request as ulib_request

from django.http import HttpResponse
from django.urls import resolve, Resolver404
from django.utils.deprecation import MiddlewareMixin

from democrapp_api import settings


class DevProxyMiddleware(MiddlewareMixin):
    """
    Middleware that proxies requests to another server if unsatisfied
    """

    def process_request(self, request):
        try:
            current_route_name = resolve(request.path_info).url_name
        except Resolver404:
            response = ulib_request.urlopen(f"{settings.UPSTREAM}{request.path}")
            info = response.info()
            return HttpResponse(response.read(), content_type=info.get_content_type())
