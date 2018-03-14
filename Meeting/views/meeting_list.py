from django.http import JsonResponse
from ..models import Meeting


def meeting_list(request):
    meeting_list = []
    for meeting in Meeting.objects.filter(close_time__isnull=True).all():
        meeting_list.append({'id': meeting.id,
                             'name': meeting.name})
    message = {'meetings': meeting_list}
    return JsonResponse(message)
