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


@register.simple_tag(name="option_remove_button")
def option_remove_button(option):
    out = ""
    if option.vote.method != Vote.YES_NO_ABS and option.vote.state == Vote.READY:
        out = "<button type='button' onclick='remove_option({})'>remove</button>".format(option.id)
    return format_html(out)
