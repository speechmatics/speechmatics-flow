import asyncio
import os
import sys

from dotenv import load_dotenv

from speechmatics_flow.cli import Transcripts, add_printing_handlers
from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.models import (
    AudioSettings,
    ConnectionSettings,
    ConversationConfig,
    Interaction,
    ServerMessageType,
)
from speechmatics_flow.playback import audio_playback

load_dotenv()

# Create a websocket client
client = WebsocketClient(
    ConnectionSettings(
        url="wss://flow.api.speechmatics.com/v1/flow",
        auth_token=os.getenv("SPEECHMATICS_API_KEY"),
    )
)


# Create an asyncio queue to store audio data
audio_queue = asyncio.Queue()


# Create a callback function to add binary messages to the audio queue
async def binary_msg_callback(msg: bytes):
    await audio_queue.put(msg)


async def main():
    """Main function to run both the WebSocket client and audio playback."""
    transcripts = Transcripts()
    # Register callbacks
    client.add_event_handler(ServerMessageType.AddAudio, binary_msg_callback)
    add_printing_handlers(client, transcripts, False)

    tasks = [
        # Start the WebSocket client and conversation
        asyncio.create_task(
            client.run(
                interactions=[Interaction(sys.stdin.buffer)],
                audio_settings=AudioSettings(),
                conversation_config=ConversationConfig(),
            )
        ),
        # Start the audio playback handler
        asyncio.create_task(audio_playback(audio_queue)),
    ]

    (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for task in done:
        exc = task.exception()
        if exc:
            raise task.exception()


# Run the main event loop
asyncio.run(main())
