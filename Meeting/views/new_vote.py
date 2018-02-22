from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting, Vote


@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def new_vote(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    token_sets = meeting.tokenset_set.order_by('created_at').all()
    name = request.POST['name']
    description = request.POST['description']
    method = request.POST['method_code']
    if method in Vote.methods:
        return JsonResponse({"error": "bad method code"})
    vote = Vote(name=name, description=description, method=method, token_set=token_sets.latest())
    vote.save()
    return JsonResponse({"type": "success", "vote_id": vote.id})
