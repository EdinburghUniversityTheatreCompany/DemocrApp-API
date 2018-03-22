from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from ..models import Meeting, Vote


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def manage_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting:
        return HttpResponse("this vote is not part of the selected meeting")
    if request.method == "POST" and request.POST['_method'] == "DELETE" and vote.state == Vote.READY:
        vote.delete()
        return HttpResponseRedirect(reverse('meeting/manage', args=[meeting.id]))
    context = {'meeting': meeting,
               'vote': vote}
    return render(request, 'meeting/vote.html', context)

