from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from ..models import Meeting, Session

@csrf_exempt
def check_token(request, meeting_id):
    token = request.POST['token']
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    current_set = meeting.tokenset_set.latest('created_at')
    if current_set.authtoken_set.filter(pk=token).exists():
        s = Session(auth_token_id=token)
        s.save()
        sessions = Session.objects.filter(auth_token_id=token)
        response = {
            "success": True,
            "session_token": s.id,
            "num_sessions": sessions.count(),
            "active_sessions": sessions.exclude(channel=None).count(),
        }
        response = JsonResponse(response)
    else:
        response = JsonResponse({"success": False, "reason": "BadToken"})
    response["Access-Control-Allow-Origin"] = "*"
    return response