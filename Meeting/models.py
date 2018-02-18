from django.db import models
from jsonfield import JSONField


class Meeting(models.Model):
    time = models.DateTimeField
    name = models.CharField


class TokenSet(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)


class Device(models.Model):
    expires = models.DateTimeField
    fingerprint = models.IntegerField


class AuthToken(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    creator = models.CharField
    proxy = models.BooleanField(default=False)


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
    candidate = models.ForeignKey(Option, on_delete=models.CASCADE)
    value = models.SmallIntegerField
