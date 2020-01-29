import _thread

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.db import models
from django.urls import reverse
import uuid
import random

from Meeting.voting_methods import YNA, STV as STVMethod, VoteMethod


class Meeting(models.Model):
    time = models.DateTimeField(default=timezone.now)
    name = models.TextField(default='')
    close_time = models.DateTimeField(default=None, null=True, blank=True)

    def open(self):
        return self.close_time is None

    def save(self, *args, **kwargs):
        if self._state.adding:
            super(Meeting, self).save(args, kwargs)
            ts = TokenSet(meeting_id=self.pk)
            ts.save()
        else:
            super(Meeting, self).save(args, kwargs)

    def __str__(self):
        return "{} \t-\t {}".format(self.time.date(), self.name)

    def get_absolute_url(self):
        return reverse('meeting/manage', args=[self.pk])

    def channel_group_name(self):
        return "meeting_{}".format(self.pk)


class TokenSet(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def valid(self):
        return self == self.meeting.tokenset_set.latest('created_at') and self.meeting.open()

    class Meta:
        get_latest_by = 'created_at'


def get_new_token_id():
    x = -1
    while x == -1 or AuthToken.objects.filter(pk=x).exists():
        x = random.randrange(10000000, 99999999)
    return x


class AuthToken(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    has_proxy = models.BooleanField(default=False)
    id = models.PositiveIntegerField(primary_key=True, default=get_new_token_id)
    active = models.BooleanField(default=True)

    def valid_for(self, vote):
        return (vote.token_set == self.token_set) and self.active

    def save(self, *args, **kwargs):
        if self._state.adding:
            super(AuthToken, self).save(args, kwargs)
            vt = VoterToken(auth_token_id=self.pk)
            vt.save()
            if self.has_proxy:
                vt = VoterToken(auth_token_id=self.pk, proxy=True)
                vt.save()
        else:
            super(AuthToken, self).save(args, kwargs)


class Session(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4)
    auth_token = models.ForeignKey(AuthToken, on_delete=models.CASCADE)
    channel = models.TextField(null=True)


class VoterToken(models.Model):
    auth_token = models.ForeignKey(AuthToken, on_delete=models.CASCADE)
    proxy = models.BooleanField(default=False)


class Vote(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    name = models.TextField(default='')
    description = models.TextField(default='')
    results = models.TextField(default='')
    YES_NO_ABS = "YNA"
    STV = "STV"
    methods = (
        (YES_NO_ABS, "Yes No Abs"),
        (STV, "Single Transferable Vote"),
    )
    method_classes = {
        YES_NO_ABS: YNA,
        STV: STVMethod
    }
    method = models.CharField(max_length=3, default=STV, choices=methods)
    READY = 'RE'
    LIVE = 'LI'
    COUNTING = "CO"
    NEEDS_TIE_BREAKER = "TI"
    CLOSED = "CL"
    states = (
        (READY, "Ready"),
        (LIVE, "Live"),
        (COUNTING, "Counting"),
        (NEEDS_TIE_BREAKER, "Needs Tie Breaker"),
        (CLOSED, "Closed"),
    )
    state = models.CharField(max_length=2, default=READY, choices=states)

    def responses(self, exclude_proxies=False):
        if exclude_proxies:
            return BallotEntry.objects.filter(option__vote=self, token__proxy=False).values('token').distinct().count()
        else:
            return BallotEntry.objects.filter(option__vote=self).values('token').distinct().count()

    def save(self, *args, **kwargs):
        if self._state.adding and self.method == self.YES_NO_ABS:
            super(Vote, self).save(*args, **kwargs)
            Option(vote=self, name="yes").save()
            Option(vote=self, name="no").save()
            Option(vote=self, name="abs").save()
        else:
            super(Vote, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def close(self, num_seats):
        self.state = self.COUNTING
        self.save()
        self.method_classes.get(self.method).count(self.id, num_seats=num_seats)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(self.token_set.meeting.channel_group_name(), {"type": "vote.closing",
                                                                                              "vote_id": self.pk})

    def get_method_class(self) -> VoteMethod:
        return self.method_classes[self.method]


class Option(models.Model):
    class Meta:
        unique_together = (('vote', 'name'),)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')
    link = models.URLField(null=True)

    def __str__(self):
        return "vote {}: {}".format(self.vote.name, self.name)


class BallotEntry(models.Model):
    class Meta:
        unique_together = (('token', 'option'),
                           #('option__vote', 'value')
                           )

    token = models.ForeignKey(VoterToken, on_delete=models.DO_NOTHING)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    value = models.SmallIntegerField(default=1)


class Tie(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
