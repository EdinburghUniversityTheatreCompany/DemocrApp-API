from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ..models import Meeting, Vote, Tie


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def break_tie(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting == meeting and vote.state == vote.READY:
        return JsonResponse({'error': 'meeting vote mismatch'}, status=401)

    if vote.state == Vote.NEEDS_TIE_BREAKER:
        if request.method == "GET":
            options = {}
            for tied_candidate in vote.tie_set.all():
                options[tied_candidate.option.id] = {
                    "name": tied_candidate.option.name
                }
            message = {"type": "tied_options",
                       "options": options,
                       }
            context = {"options": vote.tie_set.all()}
            return render(request, 'meeting/tie_breaking.html', context)
        elif request.method == "POST":
            winner = request.POST['winner_id']
            if not Tie.objects.filter(vote=vote, option_id=winner).exists():
                return JsonResponse({'error': 'winner_id was not an option'}, status=401)

            for tie in Tie.objects.filter(vote=vote).exclude(option_id=winner).all():
                tie.delete()
            vote.state = vote.COUNTING
            vote.save()
            return HttpResponseRedirect(reverse('meeting/manage', args=[meeting_id]))
    else:
        return JsonResponse({"type": "error",
                            "error": "designated stalemate associate un needed"})
