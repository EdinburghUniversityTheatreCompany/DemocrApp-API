from django.shortcuts import render, get_object_or_404
from ..models import Meeting, Vote

def manage_meeting(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    context['meeting'] = meeting
    context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
    return render(request, 'meeting/meeting.html', context)
