from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from Meeting.form import VoteForm
from ..models import Meeting, Vote, AuthToken


@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def manage_meeting(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if request.method == "POST":
        if request.POST['type'] == "create_token":
            proxy = "proxy" in request.POST.keys()
            at = AuthToken(token_set=meeting.tokenset_set.latest(), has_proxy=proxy)
            at.save()
            return redirect('print_token', token_id=at.id, has_proxy=str(proxy))
        else:
            return JsonResponse({"result": "failure", "reason": "unexpected type"})
    else:
        form = VoteForm()
        context['meeting'] = meeting
        context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
        context['form'] = form
        return render(request, 'meeting/meeting.html', context)
