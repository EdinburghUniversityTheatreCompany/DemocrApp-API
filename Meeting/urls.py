from django.urls import path
from . import views

urlpatterns = [
    path('<int:meeting_id>/checktoken', views.check_token, name='meeting/token_check'),
    path('<int:meeting_id>', views.meeting, name='meeting/detail'),
    path('<int:meeting_id>/new_vote', views.new_vote, name='meeting/new_vote'),
    path('<int:meeting_id>/<int:vote_id>/open_vote', views.open_vote, name='meeting/open_vote'),
]