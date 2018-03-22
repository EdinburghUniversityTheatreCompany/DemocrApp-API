from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from ..models import Meeting, Vote, Option

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def add_option(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != Vote.READY or vote.method == Vote.YES_NO_ABS:
        return JsonResponse({"result": "failure"})
    o = Option(name=request.POST['name'], vote=vote)
    o.save()
    return JsonResponse({"result": "success",
                         "id": o.id, })

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def remove_option(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != Vote.READY or vote.method == Vote.YES_NO_ABS:
        return JsonResponse({"result": "failure"})
    Option.objects.filter(pk=request.POST['id'], vote=vote).delete()
    return JsonResponse({"result": "success"})
