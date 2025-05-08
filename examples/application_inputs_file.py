"""
Example of using Application Inputs feature with Flow Api

This example is running a WebSocket client that connects to the Flow engine and sends audio data from the microphone.

AddInput messages are read from input.txt file, one message per line, this approach is slightly better than
the command line driven example.
"""

import asyncio
import os
import queue
import sys
import json
import time
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

# Configuration
INPUT_FILE = "input.txt"
CLEAR_FILE_AFTER_READING = True

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
# Queue for input messages from the file
input_queue = queue.Queue()
# Flag to control the file watcher
stop_watching = threading.Event()


# Create a callback function to add binary messages to the audio queue
async def binary_msg_callback(msg: bytes):
    await audio_queue.put(msg)


class InputFileHandler:
    def __init__(self, input_file=INPUT_FILE, clear_file=CLEAR_FILE_AFTER_READING):
        self.last_position = 0
        self.input_file = input_file
        self.clear_file = clear_file
        self.setup_file()

    def setup_file(self):
        """Create the input file if it doesn't exist"""
        if not os.path.exists(self.input_file):
            with open(self.input_file, 'w') as f:
                pass  # Create empty file
            print(f"Created input file: {self.input_file}")
        else:
            # If file exists, get its current size
            self.last_position = os.path.getsize(self.input_file)
            print(f"Using existing input file: {self.input_file}")

    def process_file(self):
        while not stop_watching.is_set():
            try:
                file_size = os.path.getsize(self.input_file)

                # Check if file has grown
                if file_size > self.last_position:
                    with open(self.input_file, 'r') as f:
                        # Seek to the last position we read
                        f.seek(self.last_position)
                        # Read new lines
                        # Process each new line
                        for line in [line.strip() for line in f.readlines() if line.strip()]:
                            input_queue.put(line)

                    # Update position
                    if self.clear_file:
                        open(self.input_file, 'w').close()
                        self.last_position = 0
                    else:
                        self.last_position = file_size
                time.sleep(0.5)

            except Exception as e:
                print(f"Error reading input file: {e}")
                break


def start_file_watcher():
    print(f"Listening for input in file: {os.path.abspath(INPUT_FILE)}")
    print(f"Add your messages to {INPUT_FILE}, one message per line.")
    print("Messages will be sent when the file is saved.")
    if CLEAR_FILE_AFTER_READING:
        print("Note: The file will be cleared after reading.")

    input_file = InputFileHandler(INPUT_FILE, CLEAR_FILE_AFTER_READING)
    input_file.process_file()


async def handle_input_queue():
    while True:
        try:
            await asyncio.sleep(0.1)

            if not input_queue.empty():
                user_input = input_queue.get_nowait()
                if user_input:
                    # Create the message in the required format
                    message = AddInput(input=user_input, immediate=True, interrupt_response=True).asdict()
                    # Send the message through the WebSocket
                    await client.websocket.send(json.dumps(message))

                input_queue.task_done()

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error sending message: {e}")


async def main():
    """Main function to run the WebSocket client, audio playback, and file watcher."""
    transcripts = Transcripts()

    # Register callbacks
    client.add_event_handler(ServerMessageType.AddAudio, binary_msg_callback)
    add_printing_handlers(client, transcripts, False)

    input_thread = threading.Thread(target=start_file_watcher, daemon=True)
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
        # Start the file input handler
        asyncio.create_task(handle_input_queue()),
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
        # Signal the watcher thread to stop
        stop_watching.set()
        input_thread.join()

        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)


# Run the main event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")