"""democrapp_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views import defaults

urlpatterns = [
    path('print.html?t=<int:token_id>&p=<str:has_proxy>', defaults.permission_denied, name='print_token'),
    path('bulk_tokens.html', defaults.permission_denied, name="bulk_tokens"),
    path('api/admin/', admin.site.urls),
    path('api/',  include('Meeting.urls')),
]
