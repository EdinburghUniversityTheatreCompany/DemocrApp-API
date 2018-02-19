from django.urls import path
from . import views

urlpatterns = [
    path('<int:meeting_id>/checktoken', views.check_token, name='meeting/token_check')
]