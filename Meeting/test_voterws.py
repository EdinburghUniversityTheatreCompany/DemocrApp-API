import pytest
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.test import Client

from Meeting.models import *
from channels.testing import WebsocketCommunicator
from .ui_consumer import UIConsumer


@pytest.mark.asyncio
async def test_bad_message():
    communicator = WebsocketCommunicator(UIConsumer, "")
    connected, subprotocol = await communicator.connect()
    assert connected
    # Test sending text
    await communicator.send_json_to({"hello": "hi"})
    response = await communicator.receive_json_from()
    assert response['type'] == "Bad Message"
    await communicator.send_json_to({"type": "random string with no defined response"})
    response = await communicator.receive_json_from()
    assert response['type'] == "Bad Message"


@pytest.mark.django_db(transaction=True)
class TestUiDatabaseTransactions:

    def setup(self):
        self.m = Meeting()
        self.m.save()
        self.old_ts = TokenSet(meeting=self.m)
        self.old_ts.save()
        self.ts = TokenSet(meeting=self.m)
        self.ts.save()
        self.admin = User()
        self.admin.is_superuser = True
        self.admin.save()
        self.client = Client()
        self.client.force_login(self.admin)

    async def authenticate(self, proxy):
        at = AuthToken(token_set=self.ts, has_proxy=proxy)
        at.save()
        session = Session(auth_token=at)
        session.save()
        communicator = WebsocketCommunicator(UIConsumer, "")
        connected, subprotocol = await communicator.connect()
        assert connected
        return session, communicator

    def test_setup(self):
        assert self.m in Meeting.objects.all()
        assert self.ts in self.m.tokenset_set.all()
        assert self.old_ts in self.m.tokenset_set.all()

    async def check_votes(self, expected_votes, communicator):
        v_set = expected_votes
        vote_count = 0
        vote_ids = []
        for v in v_set.all():
            response = await communicator.receive_json_from()
            while response['type'] == 'auth_response':
                response = await communicator.receive_json_from(timeout=10)
            assert 'ballot' == response['type']
            assert response['ballot_id']
            vote = v_set.filter(id=response['ballot_id']).first()
            assert vote
            assert vote in v_set.all()
            assert vote.id not in vote_ids
            vote_ids.append(vote.id)
            assert vote.name == response['title']
            assert vote.description == response['desc']
            assert vote.method == response['method']
            options = response['options']
            assert vote.option_set.count() == len(options)
            for o in vote.option_set.all():
                op = [op for op in options if op['id'] == o.id]
                assert op
                assert o.name == op[0]['name']
            assert response['proxies']
            assert not response['existing_ballots']
            vote_count += 1
        assert v_set.count() == vote_count

    @pytest.mark.asyncio
    async def test_authenticate_single(self):
        session, communicator = await self.authenticate(False)
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': str(session.id)})
        response = await communicator.receive_json_from()
        assert "success" == response['result']
        assert 1 == len(response['voters'])
        primary = session.auth_token.votertoken_set.filter(proxy=False).first().id
        primary_dict_list = [voter for voter in response['voters'] if voter['token'] == primary]
        assert primary_dict_list  # checks the list has an entry
        assert "primary" == primary_dict_list[0]['type']

    @pytest.mark.asyncio
    async def test_authenticate_proxy(self):
        session, communicator = await self.authenticate(True)
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': str(session.id)})
        response = await communicator.receive_json_from()
        assert "success" == response['result']
        assert 2 == len(response['voters'])
        primary = session.auth_token.votertoken_set.filter(proxy=False).first().id
        primary_dict_list = [voter for voter in response['voters'] if voter['token'] == primary]
        assert primary_dict_list  # checks the list has an entry
        assert "primary" == primary_dict_list[0]['type']
        proxy = session.auth_token.votertoken_set.filter(proxy=True).first().id
        poxy_dict_list = [voter for voter in response['voters'] if voter['token'] == proxy]
        assert poxy_dict_list  # checks the list has an entry
        assert "proxy" == poxy_dict_list[0]['type']

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason='stuff refuses to be awaited for unknown reasons')
    async def test_votes_are_dispatched_as_they_are_opened(self):
        # TODO(Figure out why this only passes if run on its own)
        v1 = Vote(name='y n a test', token_set=self.ts, method=Vote.YES_NO_ABS, state=Vote.READY)
        v1.save()
        v2 = Vote(token_set=self.ts, name='stv test', method=Vote.STV, state=Vote.READY)
        v2.save()
        for x in range(0, 5):
            Option(name=x, vote=v2).save()
        session, communicator = await self.authenticate(False)
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': str(session.id)})
        response = await communicator.receive_json_from()
        assert "success" == response['result']
        channel_layer = get_channel_layer()
        await channel_layer.group_send(self.m.channel_group_name(), {"type": "vote.opening",
                                                                     "vote_id": v1.id})
        await self.check_votes(Vote.objects.filter(pk=v1.id), communicator)
        await channel_layer.group_send(self.m.channel_group_name(), {"type": "vote.opening",
                                                                     "vote_id": v2.id})
        await self.check_votes(Vote.objects.filter(pk=v2.id), communicator)

    @pytest.mark.asyncio
    async def test_authenticate_with_open_votes(self):
        v = Vote(name='y n a test', token_set=self.ts, method=Vote.YES_NO_ABS, state=Vote.LIVE)
        v.save()
        v = Vote(token_set=self.ts, method=Vote.STV, state=Vote.LIVE)
        v.save()
        for x in range(0, 5):
            Option(name=x, vote=v).save()
        session, communicator = await self.authenticate(False)
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': str(session.id)})
        await self.check_votes(Vote.objects.filter(state=Vote.LIVE, token_set=self.ts), communicator)

    @pytest.mark.asycio
    async def test_authenticate_invalid_session(self):
        assert False
        communicator = WebsocketCommunicator(UIConsumer, "")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': 'garbage'})
        response = await communicator.receive_json_from()
        assert response['result'] == "failure"

    @pytest.mark.asycio
    async def test_authenticate_old_token(self):
        _, communicator = await self.authenticate(False)
        outdated_token = AuthToken(TokenSet=self.old_ts, has_proxy=False)
        session = Session(auth_token=outdated_token)
        session.save()
        await communicator.send_json_to({'type': 'auth_request',
                                         'session_token': str(session.id)})
        response = await communicator.receive_json_from()
        assert "failure" == response['result']

    #TODO("Test announcent view sends an announcement")
