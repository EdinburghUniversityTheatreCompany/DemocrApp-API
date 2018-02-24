from django.shortcuts import render, get_object_or_404

from Meeting.form import VoteForm
from ..models import Meeting, Vote

def manage_meeting(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    form = VoteForm()
    context['meeting'] = meeting
    context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
    context['form'] = form
    return render(request, 'meeting/meeting.html', context)
