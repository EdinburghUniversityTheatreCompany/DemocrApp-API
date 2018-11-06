from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

import urllib.parse

from Meeting.form import VoteForm
from ..models import Meeting, Vote, AuthToken


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def manage_meeting(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if request.method == "POST":
        return JsonResponse({"result": "failure", "reason": "depreciated method. use /api/meeting/<id>/create_token"})
    else:
        form = VoteForm()
        context['meeting'] = meeting
        context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
        context['form'] = form
        return render(request, 'meeting/meeting.html', context)


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def close_meeting(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        for t_set in meeting.tokenset_set.all():
            for vote in t_set.vote_set.filter(state=Vote.LIVE):
                vote.close(1)
            for vote in t_set.vote_set.filter(state=Vote.READY):
                vote.delete()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(meeting.channel_group_name(),
                                                {"type": "announcement",
                                                 "message": "This meeting has now closed"})
        meeting.close_time = timezone.now()
        meeting.save()
        return redirect("meeting/report/meeting", meeting_id=meeting_id)
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def create_token(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        proxy = (request.POST['proxy'] == 'true')
        at = AuthToken(token_set=meeting.tokenset_set.latest(), has_proxy=proxy)
        at.save()
        return JsonResponse({"result": "success", "meeting_id": meeting_id, "meeting_name": meeting.name, "token": at.id, "proxy": proxy, "print_url": "/print.html?" + urllib.parse.urlencode({'t': at.id, 'h': meeting.name, 'p': proxy, 'm': meeting_id}, quote_via=urllib.parse.quote)})
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def deactivate_token(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        at = AuthToken.objects.filter(id=request.POST['key'])
        if not at.exists():
            return JsonResponse({'result': 'failure',
                                 'reason': 'token doesnt exist'})
        elif at.filter(token_set__meeting=meeting).exists():
            at.filter(token_set__meeting=meeting).update(active=False)
            #TODO(close any open websockets (probably through any related sessions))
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'failure',
                                 'reason': 'token is for a different meeting'})
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})
