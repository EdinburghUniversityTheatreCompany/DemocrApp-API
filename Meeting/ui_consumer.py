from uuid import UUID
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from .models import *


class UIConsumer(JsonWebsocketConsumer):
    session = None
    voter_tokens = []

    def websocket_connect(self, message):
        self.accept()
        async_to_sync(self.channel_layer.group_add)("broadcast", self.channel_name)

    def websocket_disconnect(self, message):
        async_to_sync(self.channel_layer.group_discard)("broadcast", self.channel_name)
        if self.session is not None:
            async_to_sync(self.channel_layer.group_discard)(
                self.session.auth_token.token_set.meeting.channel_group_name(),
                self.channel_name)
        self.close()

    def receive_json(self, message, **kwargs):
        if 'type' in message.keys():
            options = {
                'auth_request': self.authenticate,
                'ballot_form': self.process_votes
            }
            options.get(message['type'], self.bad_message)(message)
        else:
            self.bad_message(message)

    def authenticate(self, message):
        key = message['session_token']
        try:
            self.session = Session.objects.filter(pk=UUID(key)).first()
            if self.session is not None:
                self.boot_others()
                self.session.channel = self.channel_name
                self.session.save()
                auth_token = self.session.auth_token
                if auth_token.token_set.valid():
                    self.voter_tokens = []
                    self.voter_tokens.append(auth_token.votertoken_set.filter(proxy=False).first().id)
                    voters = [{"token": self.voter_tokens[0], "type": "primary"}]
                    if auth_token.has_proxy:
                        self.voter_tokens.append(auth_token.votertoken_set.filter(proxy=True).first().id)
                        voters.append({"token": self.voter_tokens[1], "type": "proxy"})
                    async_to_sync(self.channel_layer.group_add)(auth_token.token_set.meeting.channel_group_name(),
                                                                self.channel_name)
                    reply = {"type": "auth_response",
                            "result": "success",
                            "voters": voters,
                            "meeting_name": auth_token.token_set.meeting.name,
                            }
                    self.send_json(reply)
                    for vote in Vote.objects.filter(token_set=auth_token.token_set, state=Vote.LIVE).all():
                        self.send_vote(vote)
                else:
                    self.send_json({"type": "auth_response",
                                    "result": "failure",
                                    "reason": "Old Auth Token"})
            else:
                raise RuntimeError
        except Exception as e:
            response = {
                "type": "auth_response",
                "result": "failure",
                "reason": "Bad Auth Token"
            }

            if settings.DEBUG:
                response['exception'] = str(e)

            self.send_json(response)

    def process_votes(self, message):
        vote_num = message['ballot_id']
        vote = Vote.objects.filter(pk=vote_num).first()
        tokens = []
        self.session.refresh_from_db()
        if self.session.auth_token.valid_for(vote) and vote.state == Vote.LIVE:
            for voter in message['votes'].items():
                voter_id = int(voter[0])
                ballot_entries = voter[1]
                if voter_id in self.voter_tokens:
                    vote.get_method_class().receive_ballot(vote, voter_id, ballot_entries)
                    tokens.append(voter_id)

            message = {
                "type": "ballot_receipt",
                "ballot_id": vote_num,
                "voter_token": tokens,
            }
            self.send_json(message)
        else:
            message = {"type": "ballot_receipt",
                       "ballot_id": vote_num,
                       "result": "failure"}
            if not self.session.auth_token.valid_for(vote):
                message['reason'] = 'Your token is not valid for this vote.'
            else:
                message['reason'] = 'Vote is not open'
            self.send_json(message)

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
        if vote.method == vote.STV:
            option_list = vote.option_set.order_by('?').all()
        else:
            option_list = vote.option_set.all()
        for option in option_list:
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
            "existing_ballots": list(BallotEntry.objects.filter(option__vote=vote, token_id__in=self.voter_tokens).values("option__vote", "token_id")),
        }
        self.send_json(message)

    def vote_closing(self, event):
        message = {
            "type": "ballot_closed",
            "ballot_id": event['vote_id'],
            "reason": "",
        }
        self.send_json(message)

    def announcement(self, event):
        message = {
            "type": "announcement",
            "message": event['message'],
        }
        self.send_json(message)

    def boot(self, event):
        message = {
            "type": "terminate_session",
            "reason": "New Client Connected"
        }
        self.send_json(message)
        self.websocket_disconnect(None)
        self.session.delete()

    def bad_message(self, content):
        self.send_json({"type": "Bad Message"})
