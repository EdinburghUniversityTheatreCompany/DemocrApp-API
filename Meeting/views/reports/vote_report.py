from django.shortcuts import render, get_object_or_404
from ...models import Meeting, Vote, VoterToken


def vote_report(request, meeting_id, vote_id):
    context = {}
    vote = get_object_or_404(Vote, pk=vote_id)
    context['vote'] = vote
    voters = VoterToken.objects.filter(ballotentry__option__vote=vote).distinct()
    present_voters = voters.filter(proxy=False).all()
    proxies = voters.filter(proxy=True).all()
    votes = []
    for v in present_voters:
        votes.append(v.ballotentry_set.filter(option__vote=vote).order_by('value'))
    proxy_votes = []
    for v in proxies:
        proxy_votes.append(v.ballotentry_set.filter(option__vote=vote).order_by('value'))
    context['votes'] = votes
    context['proxy_votes'] = proxy_votes
    context['options'] = vote.option_set.all()
    return render(request, 'meeting/reports/vote.html', context)
