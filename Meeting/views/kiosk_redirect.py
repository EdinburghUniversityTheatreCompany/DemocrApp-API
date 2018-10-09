from django.http import HttpResponse
from django.shortcuts import redirect

from Meeting.models import Meeting


def kiosk_redirect(request):
    meeting_query = Meeting.objects.filter(close_time__isnull=True).order_by('-time')
    if meeting_query.exists():
        meeting = meeting_query.first()
        return redirect('/?k=true&m={}'.format(meeting.id))
    else:
        return HttpResponse("No meeting currently running")
