from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ..models import Meeting


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def announcement(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if not meeting.open():
        return JsonResponse({"result": "failure",
                             "error": "meeting closed"})
    if "message" not in request.POST:
        return JsonResponse({"result": "failure",
                             "error": "no message"})
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(meeting.channel_group_name(),
                                            {"type": "announcement",
                                             "message": request.POST["message"]})
    return JsonResponse({"result": "success"})
