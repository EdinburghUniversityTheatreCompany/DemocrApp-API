from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Meeting


@login_required(login_url='/admin/login')
@permission_required('meeting.can_create')
def announcement(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if not meeting.open():
        return JsonResponse({"result": "failure",
                             "error": "meeting closed"})
    if "message" not in request.POST:
        return JsonResponse({"result": "failure",
                             "error": "no message"})
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("broadcast", {"type": "announcement",
                                                          "message": request["message"]})
    return JsonResponse({"result": "success"})
