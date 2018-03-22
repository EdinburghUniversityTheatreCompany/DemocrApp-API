from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

import urllib.parse

from Meeting.form import VoteForm
from ..models import Meeting, Vote, AuthToken


@login_required(login_url='/api/admin/login')
@permission_required('meeting.can_create')
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
@permission_required('meeting.can_create')
def create_token(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        proxy = ("proxy" in request.POST.keys())
        at = AuthToken(token_set=meeting.tokenset_set.latest(), has_proxy=proxy)
        at.save()
        return JsonResponse({"result": "success", "meeting_id": meeting_id, "meeting_name": meeting.name, "token": at.id, "proxy": proxy, "print_url": "/print.html?" + urllib.parse.urlencode({'t': at.id, 'h': meeting.name, 'p': proxy}, quote_via=urllib.parse.quote)})
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})