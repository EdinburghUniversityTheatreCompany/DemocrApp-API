from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    token_sets = meeting.tokenset_set.order_by('created_at').all()
    votes = []
    for t_set in token_sets:
        votes += t_set.vote_set.all()
    context = {
        'meeting': meeting,
        'token_sets': token_sets,
        'vote_list': votes}
    token_set_dict = {}
    for token_set in token_sets:
        token_set_dict[token_set.id] = token_set.authtoken_set.count()
    vote_dict = {}
    for vote in votes:
        vote_data = {"name": vote.name,
                     "description": vote.description,
                     "method": vote.method,
                     "state": vote.state,
                     }
        vote_dict[vote.id] = vote_data
    message = {
        'name': meeting.name,
        'token_sets': token_set_dict,
        'votes': vote_dict,
    }
    return JsonResponse(message)
