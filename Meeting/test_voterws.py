import json
import pytest
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
    pytestmark = pytest.mark.django_db

    def setup(self):
        self.m = Meeting()
        self.m.save()
        self.old_ts = TokenSet(meeting=self.m)
        self.old_ts.save()
        self.ts = TokenSet(meeting=self.m)
        self.ts.save()

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
