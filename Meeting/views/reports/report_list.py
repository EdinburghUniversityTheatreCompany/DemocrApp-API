from django.shortcuts import render
from ...models import Meeting


def report_list(request):
    context = {'meetings': Meeting.objects.filter(close_time__isnull=False)}
    return render(request, 'meeting/reports/list.html', context)
