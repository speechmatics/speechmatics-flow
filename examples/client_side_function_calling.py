"""This example implements a WebSocket client for interacting with Speechmatics' Flow API,
emphasising client-side function calling using a Local Knowledge Source (`Store`)
to manage a customer order.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

import pyaudio

from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.models import (
    ConnectionSettings,
    Interaction,
    AudioSettings,
    ConversationConfig,
    ServerMessageType,
    ClientMessageType,
)

# Create a websocket client
client = WebsocketClient(
    ConnectionSettings(
        url="wss://flow.api.speechmatics.com/v1/flow",
        auth_token=os.getenv("SPEECHMATICS_API_KEY"),
    )
)


class Store:
    """A class to manage a customer's order with an inventory."""

    def __init__(self) -> None:
        """Initializes the store with default inventory and an empty order."""
        self.inventory: Dict[str, int] = {
            "apple": 5,
            "banana": 5,
            "peach": 5,
            "orange": 5,
        }
        self.order: Dict[str, int] = {}

    def items_list(self) -> str:
        """Returns the current inventory."""
        return str(self.inventory)

    def create_order(self, item: str, quantity: str) -> str:
        """Creates an order with a specific item and quantity."""
        if item not in self.inventory:
            raise ValueError(f"Item '{item}' is not available in the inventory.")

        quantity = int(quantity)
        if quantity > self.inventory[item]:
            raise ValueError(
                f"Insufficient stock for '{item}'. Available: {self.inventory[item]}."
            )

        self.order[item] = quantity
        self.inventory[item] -= quantity

        return f"Created an order with {quantity} {item}(s)."

    def add_item_to_order(self, item: str, quantity: str) -> str:
        """Adds an item to the existing order."""
        if item not in self.inventory:
            raise ValueError(f"Item '{item}' is not available in the inventory.")

        quantity = int(quantity)
        if quantity > self.inventory[item]:
            raise ValueError(
                f"Insufficient stock for '{item}'. Available: {self.inventory[item]}."
            )

        self.order[item] = self.order.get(item, 0) + quantity
        self.inventory[item] -= quantity

        return f"Added {quantity} {item}(s) to the order."

    def cancel_order(self) -> str:
        """Cancels the current order and restores inventory."""
        for item, quantity in self.order.items():
            self.inventory[item] += quantity

        self.order.clear()
        return "Your order has been canceled."

    def submit_order(self) -> str:
        """Submits the current order."""
        order = self.order.copy()
        self.order.clear()
        return str(order)


# Create an asyncio queue to store audio data
audio_queue = asyncio.Queue()
# Create a store instance
store = Store()


async def binary_msg_callback(msg: bytes):
    """Handler for binary audio messages."""
    await audio_queue.put(msg)


async def order_callback(msg: Dict[str, Any]) -> None:
    """Handler for ToolInvoke messages related to orders."""
    print(f"Received message: {msg}")

    # Initialize a response template
    response: Dict[str, Any] = {
        "message": ClientMessageType.ToolResult,
        "status": "ok",
    }

    # Extract function name, tool ID, and arguments from the message
    func_name = msg.get("function", {}).get("name")
    tool_id = msg.get("id")
    args = msg.get("function", {}).get("arguments", {})

    if not func_name or not tool_id:
        response.update(
            {
                "status": "failed",
                "content": "Function name and id are required.",
            }
        )
        await send_response(response)
        return

    # Add the tool ID to the response
    response["id"] = tool_id

    try:
        if func_name == "items_list":
            response["content"] = store.items_list()
        elif func_name == "order_create":
            response["content"] = store.create_order(**args)
        elif func_name == "order_add_item":
            response["content"] = store.add_item_to_order(**args)
        elif func_name == "order_cancel":
            response["content"] = store.cancel_order()
        elif func_name == "order_submit":
            response["content"] = store.submit_order()
        else:
            response.update(
                {
                    "status": "rejected",
                    "content": f"Unknown function '{func_name}'.",
                }
            )
    except TypeError as e:
        response.update(
            {
                "status": "rejected",
                "content": f"Invalid arguments: {str(e)}",
            }
        )
    except ValueError as e:
        response.update(
            {
                "status": "failed",
                "content": str(e),
            }
        )
    except Exception as e:
        response.update(
            {
                "status": "failed",
                "content": f"Unexpected error: {str(e)}",
            }
        )

    await send_response(response)


async def send_response(response: Dict[str, Any]) -> None:
    """Send a response to the server."""
    print(f"Sending response: {response}")
    try:
        await client.websocket.send(json.dumps(response))
    except Exception as e:
        print(f"Failed to send response: {e}")


client.add_event_handler(ServerMessageType.AddAudio, binary_msg_callback)
client.add_event_handler(ServerMessageType.ToolInvoke, order_callback)


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
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "items_list",
                            "description": "Use this function when the user ask what's in the inventory or "
                            "if a certain item is available.",
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "order_create",
                            "description": "Use this function when the user asks to place an order. "
                            "NEVER add an item that is not available.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "item": {
                                        "type": "string",
                                        "description": "Item name.",
                                    },
                                    "quantity": {
                                        "type": "string",
                                        "description": "Quantity.",
                                    },
                                },
                                "required": ["item", "quantity"],
                            },
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "order_add_item",
                            "description": "Use this function when the user asks to update or add an item to the order. "
                            "NEVER add an item that is not available.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "item": {
                                        "type": "string",
                                        "description": "Item name.",
                                    },
                                    "quantity": {
                                        "type": "string",
                                        "description": "Quantity.",
                                    },
                                },
                                "required": ["item", "quantity"],
                            },
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "order_cancel",
                            "description": "Use this function when the user asks to cancel the order. "
                            "Double-check first with the user before triggering the function.",
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "order_submit",
                            "description": "Use this function when the user asks to submit the order. "
                            "Double-check first with the user before triggering the function and let them know "
                            "that once submitted, the user can no longer add or delete from the order.",
                        },
                    },
                ],
            )
        ),
        # Start the audio playback handler
        asyncio.create_task(audio_playback()),
    ]

    (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for task in done:
        exc = task.exception()
        if exc:
            raise task.exception()


# Run the main event loop
asyncio.run(main())
