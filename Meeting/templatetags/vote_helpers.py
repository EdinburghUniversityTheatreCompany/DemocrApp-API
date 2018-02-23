from django import template
from django.urls import reverse
from django.utils.html import format_html

from ..models import Vote

register = template.Library()

@register.simple_tag(name="vote_action_button")
def vote_action_button(vote):
    args = [vote.token_set.meeting_id, vote.id]
    cases = {
        Vote.READY: "<a class='btn' href='{}'>{}</a>".format(
            reverse('meeting/open_vote', args=args),
            "Open Vote"),
        Vote.LIVE: "<a class='btn' href='{}'>{}</a>".format(
            reverse('meeting/close_vote', args=args),
            "Close Vote"),
        Vote.COUNTING: "Counting",
        Vote.NEEDS_TIE_BREAKER: "<a class='btn' href='{}'>{}</a>".format(
            reverse('meeting/break_tie', args=args),
            "Needs Tie Breaker"),
        Vote.CLOSED: "Closed",
    }
    return format_html(cases[vote.state])
