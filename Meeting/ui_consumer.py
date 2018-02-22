from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from .models import *


class UIConsumer(JsonWebsocketConsumer):
    auth_token = None

    def websocket_connect(self, message):
        self.accept()
        async_to_sync(self.channel_layer.group_add)("broadcast", self.channel_name)

    def websocket_disconnect(self, message):
        async_to_sync(self.channel_layer.group_discard)("broadcast", self.channel_name)
        self.close()

    def receive_json(self, message, **kwargs):
        options = {
            'auth_request': self.authenticate,
            'votes': self.process_votes
        }
        options.get(message['type'], self.bad_message)(message)

    def authenticate(self, message):
        key = message['session_token']
        self.session = Session.objects.filter(pk=key).first()
        if self.session is not None:
            self.boot_others()
            self.session.channel = self.channel_name
            self.session.save()
            auth_token = self.session.auth_token
            if auth_token.token_set.valid():
                self.vote_token = auth_token.votertoken_set.filter(proxy=False).first()
                voters = [{"token": self.vote_token.id, "type": "primary"}]
                if auth_token.has_proxy:
                    self.proxy_token = auth_token.votertoken_set.filter(proxy=True).first()
                    voters.append({"token": self.proxy_token.id, "type": "proxy"})
                reply = {"type": "auth_response",
                        "result": "success",
                        "voters": voters,
                        "meeting_name": auth_token.token_set.meeting.name,
                        }
                self.send_json(reply)
                for vote in Vote.objects.filter(token_set=auth_token.token_set).all():
                    self.send_vote(vote)
            else:
                self.send_json({"ERROR": "Old Auth Token"})
        else:
            self.send_json({"ERROR": "Bad Auth Token"})

    def process_votes(self, message):
        vote_num = message['ballot_id']
        vote = Vote.objects.filter(pk=vote_num).first()
        if self.auth_token.valid_for(vote) and vote.live:
            for voter in message['votes'].items():
                if voter[0] in [self.proxy_token.id, self.vote_token.id]:
                    BallotEntry.objects.filter(token_id=voter, option__vote=vote).delete()
                    for ballot_entry in voter[1].items():
                        option = vote.option_set.filter(pk=ballot_entry[0]).first()
                        if option is not None and ballot_entry[1] >= 1:
                            be = BallotEntry(option=option, token_id=voter[0], value=ballot_entry[1])
                            be.save()

    def boot_others(self):
        others = Session.objects.filter(auth_token=self.session.auth_token)
        others = others.exclude(pk=self.session.id)
        others = others.exclude(channel=None)
        for other_session in others.all():
            async_to_sync(self.channel_layer.send)(other_session.channel, {"type": "boot"})

    def vote_opening(self, event):
        vote = Vote.objects.get(pk=event['vote_id'])
        self.send_vote(vote)

    def send_vote(self, vote):
        options = []
        for option in vote.option_set.all():
            options.append({
                "id": option.id,
                "name": option.name,
            })
        message = {
            "type": "ballot",
            "ballot_id": vote.id,
            "title": vote.name,
            "desc": vote.description,
            "method": vote.method,
            "options": options,
            "proxies": True,
        }
        self.send_json(message)

    def vote_closing(self, event):
        message = {
            "ballot_id": "vote.id",
            "reason": "[optional reason string]"
        }
        self.send_json(message)

    def boot(self, event):
        message = {
            "type": "terminate_session",
            "reason": "New Client Connected"
        }
        self.send_json(message)
        self.websocket_disconnect(None)


    def bad_message(self, content):
        pass