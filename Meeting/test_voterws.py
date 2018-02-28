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
    # Close
    communicator.disconnect()

@pytest.mark.django_db
class TestUiDatabaseTransactions:
    pytestmark = pytest.mark.django_db

    def setup(self):
        self.m = Meeting()
        self.m.save()
        self.old_ts = TokenSet(meeting=self.m)
        self.old_ts.save()
        self.ts = TokenSet(meeting=self.m)
        self.ts.save()

    async def authenticate(self):
        at = AuthToken(token_set=self.ts)
        at.save()
        session = Session(AuthToken=at)
        session.save()
        communicator = WebsocketCommunicator(UIConsumer, "")
        connected, subprotocol = await self.communicator.connect()
        assert connected
        return session, communicator

    def test_setup(self):
        assert self.m in Meeting.objects.all()

    @pytest.mark.asyncio
    async def test_authenticate(self):
        session, communicator = await self.authenticate()
        await communicator.send_json_to({'type': 'auth_request',
                                              'session_token': session.id})
        response = await communicator.receive_json_from()
        assert response['result'] == "Success"
