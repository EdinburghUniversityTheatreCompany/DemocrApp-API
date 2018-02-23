from django.urls import path
from . import views

urlpatterns = [
    path('<int:meeting_id>/checktoken', views.check_token, name='meeting/token_check'),
    path('<int:meeting_id>', views.meeting, name='meeting/detail'),
    path('<int:meeting_id>/new_vote', views.new_vote, name='meeting/new_vote'),
    path('<int:meeting_id>/<int:vote_id>/open_vote', views.open_vote, name='meeting/open_vote'),
    path('<int:meeting_id>/<int:vote_id>/close_vote', views.close_vote, name='meeting/close_vote'),
    path('<int:meeting_id>/<int:vote_id>/break_tie', views.break_tie, name='meeting/break_tie'),
    path('manage/<int:meeting_id>', views.manage_meeting, name='meeting/manage'),
    path('<int:meeting_id>/announcement', views.announcement, name='meeting/announcement')
]
