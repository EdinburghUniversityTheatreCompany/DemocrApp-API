from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting, Vote
from threading import Thread


@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def close_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting == meeting and vote.state == vote.READY:
        return JsonResponse({'error': 'meeting vote mismatch'}, status=401)
    count_method = {
        Vote.YES_NO_ABS: yes_no_abs(vote),
        Vote.STV: stv(vote, request.POST['num_seats']),
    }
    count_method[vote.method]
    num_seats = request.POST['num_seats']
    vote.state = vote.COUNTING
    vote.save()
    message = {'type': 'success'}
    return JsonResponse(message)


def yes_no_abs(vote):
    from ..tallying import *


def stv(vote, seats):
    from ..tallying import run_open_stv
    count_thread = Thread(target=run_open_stv(vote.id, seats))
    count_thread.start()
