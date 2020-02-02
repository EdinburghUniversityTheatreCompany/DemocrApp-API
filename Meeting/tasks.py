from __future__ import absolute_import, unicode_literals

from celery import shared_task


@shared_task
def run_count(vote_id, num_seats):
    from Meeting.models import Vote
    vote = Vote.objects.get(id=vote_id)
    vote.method_classes.get(vote.method).count(vote, num_seats=num_seats)
    vote.refresh_from_db()
    vote.state = Vote.CLOSED
    vote.save()
