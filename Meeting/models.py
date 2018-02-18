from django.db import models
from jsonfield import JSONField


class Meeting(models.Model):
    time = models.DateTimeField
    name = models.CharField


class TokenSet(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)


class Device(models.Model):
    expires = models.DateTimeField
    fingerprint = models.CharField


class Token(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    creator = models.CharField
    proxy = models.BooleanField(default=False)


class Vote(models.Model):
    token_set = models.ForeignKey(TokenSet, on_delete=models.CASCADE)
    name = models.CharField
    method = models.CharField


class Candidate(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    name = models.CharField
    link = models.URLField


class BallotEntry(models.Model):
    token = models.ForeignKey(Token, on_delete=models.DO_NOTHING)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    data = JSONField()
