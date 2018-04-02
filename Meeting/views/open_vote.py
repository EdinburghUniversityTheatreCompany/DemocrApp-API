from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ..models import Meeting, Vote


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def open_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != vote.READY:
        return JsonResponse({'result': 'failure'}, status=401)
    if vote.option_set.count() < 2:
        return JsonResponse({'result': 'failure',
                             'reason:': 'insufficient_options',
                             'verbose_reason': 'an stv vote needs at least 2 options'})

    vote.state = vote.LIVE
    vote.token_set = meeting.tokenset_set.latest()
    vote.save()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(meeting.channel_group_name(), {"type": "vote.opening",
                                                                           "vote_id": vote_id})

    message = {
        "type": "success"
    }

    return HttpResponseRedirect(reverse('meeting/manage', args=[meeting.id]))
