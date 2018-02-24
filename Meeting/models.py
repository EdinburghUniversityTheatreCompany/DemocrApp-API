from django.db import models
import uuid
import random


class Meeting(models.Model):
    time = models.DateTimeField
    name = models.TextField(default='')
    close_time = models.DateTimeField(null=True)

    def open(self):
        return self.close_time is None


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
    creator = models.TextField
    has_proxy = models.BooleanField(default=False)
    id = models.PositiveIntegerField(primary_key=True, default=get_new_token_id)

    def valid_for(self, vote):
        return vote.token_set == self.token_set

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
    YES_NO_ABS = "YNA"
    STV = "STV"
    methods = (
        (YES_NO_ABS, "Yes No Abs"),
        (STV, "Single Transferable Vote"),
    )
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


    def responses(self):
        return BallotEntry.objects.filter(option__vote=self).values('token').distinct().count()

    def save(self, *args, **kwargs):
        if self._state.adding and self.method == self.YES_NO_ABS:
            super(Vote, self).save(args, kwargs)
            Option(vote=self, name="yes").save()
            Option(vote=self, name="no").save()
            Option(vote=self, name="abs").save()
        else:
            super(Vote, self).save(args, kwargs)

    def __str__(self):
        return self.name



class Option(models.Model):
    class Meta:
        unique_together = (('vote', 'name'),)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    name = models.TextField(default='')
    link = models.URLField

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
