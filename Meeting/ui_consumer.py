from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from .models import *


class UIConsumer(JsonWebsocketConsumer):
    auth_token = None

    def websocket_connect(self, message):
        self.accept()
        async_to_sync(self.channel_layer.group_add)("broadcast", self.channel_name)

    def receive_json(self, message, **kwargs):
        options = {
            'authentication': self.authenticate,
            'votes': self.process_votes
        }
        options.get(message['content'], self.bad_message)(message)

    def authenticate(self, message):
        key = message['key']
        self.auth_token = AuthToken.objects.filter(pk=97305076).first()
        if self.auth_token is not None:
            if self.auth_token.token_set.valid():
                self.vote_token = self.auth_token.votertoken_set.filter(proxy=False).first()
                if self.auth_token.has_proxy:
                    self.proxy_token = self.auth_token.votertoken_set.filter(proxy=True).first()
                    # TODO(notify the ui it has proxies)
                else:
                    pass
                    # TODO(notify the ui it doesnt have proxies)
            else:
                self.send_json({"ERROR": "Old Auth Token"}, close=True)
        else:
            self.send_json({"ERROR": "Bad Auth Token"}, close=True)

    def process_votes(self, message):
        vote_num = message['vote_number']
        vote = Vote.objects.filter(pk=vote_num).first()
        if self.auth_token.valid_for(vote) and vote.live:
            for x in message['votes'].items():
                option = vote.option_set.filter(pk=x[0]).first()
                if option is not None:
                    be = BallotEntry(vote=option, token=self.vote_token)
                    be.value = x[1]
                    be.save()

    def vote_opening(self,event):
        self.send_json({"event": event})

    def bad_message(self, content):
        pass