from django import template
from django.template import context
from django.urls import reverse
from django.utils.html import format_html
from ..models import Vote

register = template.Library()


@register.simple_tag(name="vote_action_button")
def vote_action_button(vote):
    args = [vote.token_set.meeting_id, vote.id]
    if vote.method == Vote.STV and vote.state == Vote.LIVE:
        return format_html("<a class='btn btn-sm btn-warning' href='{}'>{}</a>".format(
            reverse('meeting/close_vote/stv', args=args),
            "Close Vote"))
    cases = {
        Vote.READY: "<a class='btn btn-sm btn-success' href='{}'>{}</a>".format(
            reverse('meeting/open_vote', args=args),
            "Open Vote"),
        Vote.LIVE: "<a class='btn btn-sm btn-warning' href='{}'>{}</a>".format(
            reverse('meeting/close_vote', args=args),
            "Close Vote"),
        Vote.COUNTING: "Counting",
        Vote.NEEDS_TIE_BREAKER: "<a class='btn btn-sm btn-secondary' href='{}'>{}</a>".format(
            reverse('meeting/break_tie', args=args),
            "Needs Tie Breaker"),
        Vote.CLOSED: "-",
    }
    return format_html(cases[vote.state])


@register.simple_tag(name="vote_responses_or_remove")
def vote_responses_or_remove(vote, token):
    if vote.state == Vote.READY:
        return format_html("""<form action='{}' method='POST'>
        <input type='hidden' name='csrfmiddlewaretoken' value='{}' />
        <input type='hidden' name='_method' value='DELETE'>
        <input class='btn btn-sm btn-danger' type='submit' value='Delete'>
        </form>""",
            reverse('meeting/manage_vote', args=[vote.token_set.meeting_id, vote.id]),
            token)
    else:
        return vote.responses()


@register.simple_tag(name="option_remove_button")
def option_remove_button(option):
    out = ""
    if option.vote.method != Vote.YES_NO_ABS and option.vote.state == Vote.READY:
        out = "<button class='btn btn-sm btn-danger m-1' type='button' onclick='remove_option({})'>remove</button>".format(option.id)
    return format_html(out)
