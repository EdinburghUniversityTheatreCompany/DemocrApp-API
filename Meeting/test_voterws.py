import json
import pytest
from Meeting.models import *
from channels.testing import WebsocketCommunicator
from .ui_consumer import UIConsumer

@pytest.mark.asyncio
async def test_my_consumer():
    communicator = WebsocketCommunicator(UIConsumer, "")
    connected, subprotocol = await communicator.connect()
    assert connected
    # Test sending text
    await communicator.send_to(text_data="hello")
    response = await communicator.receive_from()
    assert response == "hello"
    # Close
    await communicator.disconnect()
