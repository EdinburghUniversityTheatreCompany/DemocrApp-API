from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting, Vote, Tie


@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def break_tie(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting == meeting and vote.state == vote.READY:
        return JsonResponse({'error': 'meeting vote mismatch'}, status=401)

    winner = request.POST['winner_id']
    if not Tie.objects.filter(vote=vote, option_id=winner).exists():
        return JsonResponse({'error': 'winner_id was not an option'}, status=401)

    for tie in Tie.objects.filter(vote=vote).exclude(option_id=winner).all():
        tie.delete()
    vote.state = vote.COUNTING
    vote.save()
    message = {'type': 'success'}
    return JsonResponse(message)
