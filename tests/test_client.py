import json
from typing import List, Dict, Optional

import pytest
from pytest import param

from speechmatics_flow import DebugMode
from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.models import (
    ServerMessageType,
    ConnectionSettings,
    ClientMessageType,
    AudioSettings,
    ConversationConfig,
)
from speechmatics_flow.tool_function_param import ToolFunctionParam

TOOL_FUNCTION = dict(
    ToolFunctionParam(
        type="function",
        function={
            "name": "test_function",
            "description": "test function to be called.",
        },
    )
)


@pytest.fixture
def ws_client():
    return WebsocketClient(
        connection_settings=ConnectionSettings(url="ws://test"),
    )


@pytest.mark.parametrize(
    "audio_format, conversation_config, tools, debug_mode, expected_start_message",
    [
        param(
            AudioSettings(),
            ConversationConfig(),
            None,
            DebugMode(),
            {
                "message": ClientMessageType.StartConversation.value,
                "audio_format": AudioSettings().asdict(),
                "conversation_config": ConversationConfig().asdict(),
                "debug": DebugMode().asdict(),
            },
            id="with default values",
        ),
        param(
            AudioSettings(),
            ConversationConfig(),
            [TOOL_FUNCTION],
            None,
            {
                "message": ClientMessageType.StartConversation.value,
                "audio_format": AudioSettings().asdict(),
                "conversation_config": ConversationConfig().asdict(),
                "tools": [TOOL_FUNCTION],
            },
            id="with default values and tools",
        ),
        param(
            AudioSettings(),
            ConversationConfig(),
            None,
            DebugMode(llm=True),
            {
                "message": ClientMessageType.StartConversation.value,
                "audio_format": AudioSettings().asdict(),
                "conversation_config": ConversationConfig().asdict(),
                "debug": DebugMode(llm=True).asdict(),
            },
            id="with default values and llm debug mode enabled",
        ),
    ],
)
def test_start_conversation(
    ws_client: WebsocketClient,
    audio_format: AudioSettings,
    conversation_config: ConversationConfig,
    tools: Optional[List[ToolFunctionParam]],
    debug_mode: Optional[DebugMode],
    expected_start_message: Dict,
):
    handler_called = False

    def handler(*_):
        nonlocal handler_called
        handler_called = True

    ws_client.middlewares = {ClientMessageType.StartConversation: [handler]}
    ws_client.audio_settings = audio_format
    ws_client.conversation_config = conversation_config
    ws_client.tools = tools
    ws_client.debug_mode = debug_mode
    start_conversation_msg = ws_client._start_conversation()
    assert start_conversation_msg == json.dumps(
        expected_start_message
    ), f"expected={start_conversation_msg}, got={expected_start_message}"
    assert handler_called, "handler was not called"


@pytest.mark.asyncio
async def test_consumer_supports_sync_and_async_handlers(ws_client):
    await ws_client._init_synchronization_primitives()

    async_handler_called = False
    sync_handler_called = False

    async def async_handler(_):
        nonlocal async_handler_called
        async_handler_called = True

    def sync_handler(_):
        nonlocal sync_handler_called
        sync_handler_called = True

    # Add event handlers for a message type
    ws_client.event_handlers = {
        ServerMessageType.ConversationStarted: [async_handler, sync_handler],
    }

    message = json.dumps({"message": ServerMessageType.ConversationStarted})
    await ws_client._consumer(message, from_cli=False)

    # Check if both handlers were called
    assert async_handler_called, "async handler was not called"
    assert sync_handler_called, "sync handler was not called"
