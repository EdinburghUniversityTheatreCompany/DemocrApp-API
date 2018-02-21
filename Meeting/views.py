from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Meeting, TokenSet, AuthToken
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@csrf_exempt  # TODO(Decide if this is a good idea)
def check_token(request, meeting_id):
    token = request.POST['token']
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    current_set = meeting.tokenset_set.latest('created_at')
    if current_set.authtoken_set.filter(pk=token).exists():
        return HttpResponse(":D")
    else:
        return HttpResponse("Bad Token")

def new_vote(request, meeting_id):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)("broadcast", {"type": "vote.opening",
                                                          "vote_id": 1})
    return HttpResponse("notified")

def meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    token_sets = meeting.tokenset_set.all()
    votes = []
    for t_set in token_sets:
        votes += t_set.vote_set.all()
    context = {
        'meeting': meeting,
        'token_sets': token_sets,
        'vote_list': votes}
    render(request, '', context)

