import asyncio
import os
import sys

import pyaudio

from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.models import (
    ConnectionSettings,
    Interaction,
    AudioSettings,
    ConversationConfig,
    ServerMessageType,
)

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


# Register the callback to be called when the client receives an audio message
client.add_event_handler(ServerMessageType.AddAudio, binary_msg_callback)


async def audio_playback():
    """Continuously read from the audio queue and play audio back to the user."""
    p = pyaudio.PyAudio()
    player_stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        frames_per_buffer=128,
        output=True,
    )
    try:
        while True:
            audio = await audio_queue.get()
            player_stream.write(audio)
            # read from buffer at a constant rate
            await asyncio.sleep(0.005)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()


async def main():
    """Main function to run both the WebSocket client and audio playback."""
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
        asyncio.create_task(audio_playback()),
    ]

    await asyncio.wait(tasks)


# Run the main event loop
asyncio.run(main())
