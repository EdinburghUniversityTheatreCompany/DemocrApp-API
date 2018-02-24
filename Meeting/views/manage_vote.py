from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from ..models import Meeting, Vote


@csrf_exempt
@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def manage_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting:
        return HttpResponse("this vote is not part of the selected meeting")
    context = {'meeting': meeting,
               'vote': vote}
    return render(request, 'meeting/vote.html', context)

