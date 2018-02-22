from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting, Vote

@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def open_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set in meeting.tokenset_set:
        return JsonResponse(status=401)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("broadcast", {"type": "vote.opening",
                                                          "vote_id": 1})
    return HttpResponse("notified")