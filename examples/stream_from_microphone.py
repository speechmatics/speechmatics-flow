import asyncio
import io
import ssl
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

AUTH_TOKEN = "YOUR TOKEN HERE"

# Create a websocket client
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
client = WebsocketClient(
    ConnectionSettings(
        url="wss://flow.api.speechmatics.com/v1/flow",
        auth_token=AUTH_TOKEN,
        ssl_context=ssl_context,
    )
)


# Create an asyncio queue to store audio data
audio_queue = asyncio.Queue()


# Create a callback function to add binary messages to the audio queue
def binary_msg_handler(msg: bytes):
    if isinstance(msg, (bytes, bytearray)):
        audio_queue.put_nowait(msg)


# Register the callback to be called when the client receives an audio message
client.add_event_handler(ServerMessageType.audio, binary_msg_handler)


async def audio_playback():
    """Continuously read from the audio queue and play audio back to the user."""
    p = pyaudio.PyAudio()
    chunk_size = 1024
    player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)

    try:
        while True:
            # Create a new playback buffer for each iteration
            playback_buffer = io.BytesIO()

            # Fill the buffer until it has enough data
            while playback_buffer.tell() < chunk_size:
                playback_buffer.write(await audio_queue.get())

            # Write the full buffer contents to the player stream
            player_stream.write(playback_buffer.getvalue())
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

    await asyncio.gather(*tasks)


# Run the main event loop
asyncio.run(main())
