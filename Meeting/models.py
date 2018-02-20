from django.db import models
import random


class Meeting(models.Model):
    time = models.DateTimeField
    name = models.CharField
    close_time = models.DateTimeField(null=True)

    def open(self):
        return self.close_time is None


class TokenSet(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def valid(self):
        return self == self.meeting.tokenset_set.latest('created_at') and self.meeting.open()


class Device(models.Model):
    expires = models.DateTimeField
    fingerprint = models.IntegerField


def get_new_token_id():
    x = -1
    while x == -1 or AuthToken.objects.filter(pk=x).exists():
        x = random.randrange(10000000, 99999999)
    return x


class AuthToken(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING, null=True)
    creator = models.CharField
    has_proxy = models.BooleanField(default=False)
    id = models.PositiveIntegerField(primary_key=True, default=get_new_token_id)

    def valid_for(self, vote):
        return vote.token_set == self.token_set

    def save(self, *args, **kwargs):
        if self._state.adding:
            super(AuthToken, self).save(args, kwargs)
            vt = VoterToken(auth_token_id=self.pk)
            vt.save()
            if self.proxy:
                vt = VoterToken(auth_token_id=self.pk, proxy=True)
                vt.save()
        else:
            super(AuthToken, self).save(args, kwargs)


class VoterToken(models.Model):
    auth_token = models.ForeignKey(AuthToken, on_delete=models.CASCADE)
    proxy = models.BooleanField(default=False)


class Vote(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    name = models.CharField
    description = models.TextField
    method = models.CharField
    live = models.BooleanField(default=False)


class Option(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    name = models.CharField
    link = models.URLField


class BallotEntry(models.Model):
    token = models.ForeignKey(VoterToken, on_delete=models.DO_NOTHING)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    value = models.SmallIntegerField
