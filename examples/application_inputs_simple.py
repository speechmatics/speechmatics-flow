"""
Example of using Application Inputs feature with Flow Api

This example is running a WebSocket client that connects to the Flow engine and sends audio data from the microphone.
AddInput messages are sent from cli input, the experience is not great because the input is collected form the command
line and the flow responses are printed to the command line.
"""

import asyncio
import os
import queue
import sys
import json
import threading

from dotenv import load_dotenv

from speechmatics_flow.cli import Transcripts, add_printing_handlers
from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.models import (
    AudioSettings,
    ConnectionSettings,
    ConversationConfig,
    Interaction,
    ServerMessageType,
    AddInput
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
# Regular Python queue for thread-safe communication
input_queue = queue.Queue()
# Flag to signal when to stop the input thread
stop_input_thread = threading.Event()


# Create a callback function to add binary messages to the audio queue
async def binary_msg_callback(msg: bytes):
    await audio_queue.put(msg)


# Function to read input in a separate thread
def input_reader():
    print("Type your message and press Enter to send. (Press Ctrl+C to exit)")
    while not stop_input_thread.is_set():
        try:
            user_input = input(">>>> ")
            # Add the input to the queue for the asyncio task to process
            input_queue.put(user_input)
        except EOFError:
            # Handle EOF (Ctrl+D on Unix, Ctrl+Z on Windows)
            break
        except Exception as e:
            print(f"Error reading input: {e}")
            break


# Function to process the input queue and send messages via WebSocket
async def handle_keyboard_input():
    while True:
        # Check the regular queue in a non-blocking way
        try:
            # Use asyncio.sleep(0) to yield control back to the event loop regularly
            await asyncio.sleep(0.1)

            # Check if there's input to process (non-blocking)
            if not input_queue.empty():
                user_input = input_queue.get_nowait()
                if user_input:
                    # Create the message in the required format
                    message = AddInput(input=user_input, immediate=True, interrupt_response=True).asdict()
                    # Send the message through the WebSocket
                    await client.websocket.send(json.dumps(message))
                    print(f"Message sent: {json.dumps(message)}")
                # Mark the task as done
                input_queue.task_done()
        except queue.Empty:
            # Queue is empty, just continue
            pass
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error sending message: {e}")


async def main():
    """Main function to run both the WebSocket client and audio playback."""
    transcripts = Transcripts()
    # Register callbacks
    client.add_event_handler(ServerMessageType.AddAudio, binary_msg_callback)
    add_printing_handlers(client, transcripts, False)

    # Start the input reader thread
    input_thread = threading.Thread(target=input_reader, daemon=True)
    input_thread.start()

    tasks = [
        # Start the WebSocket client and conversation
        asyncio.create_task(
            client.run(
                interactions=[Interaction(sys.stdin.buffer)],
                audio_settings=AudioSettings(),
                conversation_config=ConversationConfig(
                    template_id=os.environ.get("CONVERSATION_TEMPLATE_ID", "default"),
                ),
            )
        ),
        # Start the audio playback handler
        asyncio.create_task(audio_playback(audio_queue)),
        # Start the keyboard input handler (polls the queue)
        asyncio.create_task(handle_keyboard_input()),
    ]

    try:
        (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in done:
            exc = task.exception()
            if exc:
                raise task.exception()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Signal the input thread to stop
        stop_input_thread.set()

        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
