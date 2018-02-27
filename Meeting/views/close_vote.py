import _thread

from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ..models import Meeting, Vote
from threading import Thread
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def close_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != vote.LIVE:
        return JsonResponse({'result': 'failure'}, status=401)
    vote.state = vote.COUNTING
    vote.save()
    num_seats = request.POST['num_seats'] if 'num_seats' in request.POST else 1
    count_method_action = {
        Vote.YES_NO_ABS: yes_no_abs,
        Vote.STV: stv,
    }
    count_method_args = {
        Vote.YES_NO_ABS: [vote],
        Vote.STV: [vote, num_seats]
    }
    default_args = "hi"
    func = count_method_action.get(vote.method, stv)
    func(*count_method_args.get(vote.method, [vote, 1]))
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("broadcast", {"type": "vote.closing",
                                                          "vote_id": vote_id})
    message = {'type': 'success'}
    return HttpResponseRedirect(reverse('meeting/manage', args=[meeting.id]))


def yes_no_abs(vote):
    from ..tallying import yes_no_abs_count
    y, n, a = yes_no_abs_count(vote.id)
    vote.description = "Y:{},N:{},A{}".format(y, n, a)
    vote.state = Vote.CLOSED
    vote.save()


def stv(vote, seats):
    from ..tallying import run_open_stv
    _thread.start_new_thread(run_open_stv, (vote.id, seats))

