# (c) 2024, Cantab Research Ltd.
"""
Wrapper library to interface with Flow Service API.
"""

import asyncio
import copy
import inspect
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import httpx
import pyaudio
import websockets

from speechmatics_flow.exceptions import (
    ConversationEndedException,
    ForceEndSession,
    ConversationError,
)
from speechmatics_flow.models import (
    ClientMessageType,
    ServerMessageType,
    AudioSettings,
    ConversationConfig,
    Interaction,
    ConnectionSettings,
)
from speechmatics_flow.tool_function_param import ToolFunctionParam
from speechmatics_flow.utils import read_in_chunks, json_utf8

LOGGER = logging.getLogger(__name__)

# If the logging level is set to DEBUG websockets logs very verbosely,
# including a hex dump of every message being sent. Setting the websockets
# logger at INFO level specifically prevents this spam.
logging.getLogger("websockets.protocol").setLevel(logging.INFO)


class WebsocketClient:
    """
    Manage a conversation session with the agent.

    The best way to interact with this library is to instantiate this client
    and then add a set of handlers to it. Handlers respond to particular types
    of messages received from the server.

    :param connection_settings: Settings for the WebSocket connection,
        including the URL of the server.
    :type connection_settings: models.ConnectionSettings
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        connection_settings: ConnectionSettings = None,
    ):
        self.connection_settings = connection_settings
        self.websocket = None
        self.conversation_config = None
        self.audio_settings = None
        self.tools = None

        self.event_handlers = {x: [] for x in ServerMessageType}
        self.middlewares = {x: [] for x in ClientMessageType}

        self.client_seq_no = 0
        self.server_seq_no = 0
        self.session_running = False
        self.conversation_ended_wait_timeout = 5
        self._session_needs_closing = False
        self._audio_buffer = None
        self._executor = ThreadPoolExecutor()

        # The following asyncio fields are fully instantiated in
        # _init_synchronization_primitives
        self._conversation_started = asyncio.Event
        self._conversation_ended = asyncio.Event
        # Semaphore used to ensure that we don't send too much audio data to
        # the server too quickly and burst any buffers downstream.
        self._buffer_semaphore = asyncio.BoundedSemaphore

    async def _init_synchronization_primitives(self):
        """
        Used to initialise synchronization primitives that require
        an event loop
        """
        self._conversation_started = asyncio.Event()
        self._conversation_ended = asyncio.Event()
        self._buffer_semaphore = asyncio.BoundedSemaphore(
            self.connection_settings.message_buffer_size
        )

    def _flag_conversation_started(self):
        """
        Handle a
        :py:attr:`models.ClientMessageType.ConversationStarted`
        message from the server.
        This updates an internal flag to mark the session started
        as started meaning, AddAudio is now allowed.
        """
        self._conversation_started.set()

    def _flag_conversation_ended(self):
        """
        Handle a
        :py:attr:`models.ClientMessageType.ConversationEnded`
        message from the server.
        This updates an internal flag to mark the session ended
        and server connection is closed
        """
        self._conversation_ended.set()

    @json_utf8
    def _start_conversation(self):
        """
        Constructs a
        :py:attr:`models.ClientMessageType.StartConversation`
        message.
        This initiates the conversation session.
        """
        assert self.conversation_config is not None
        msg = {
            "message": ClientMessageType.StartConversation,
            "audio_format": self.audio_settings.asdict(),
            "conversation_config": self.conversation_config.asdict(),
        }
        if self.tools is not None:
            msg["tools"] = self.tools
        self.session_running = True
        self._call_middleware(ClientMessageType.StartConversation, msg, False)
        LOGGER.debug(msg)
        return msg

    @json_utf8
    def _end_of_audio(self):
        """
        Constructs an
        :py:attr:`models.ClientMessageType.AudioEnded`
        message.
        """
        msg = {
            "message": ClientMessageType.AudioEnded,
            "last_seq_no": self.client_seq_no,
        }
        self._call_middleware(ClientMessageType.AudioEnded, msg, False)
        LOGGER.debug(msg)
        return msg

    @json_utf8
    def _audio_received(self):
        """Constructs an :py:attr:`models.ClientMessageType.AudioReceived` message."""
        self.server_seq_no += 1
        msg = {
            "message": ClientMessageType.AudioReceived,
            "seq_no": self.server_seq_no,
            "buffering": 0.01,  # 10ms
        }
        self._call_middleware(ClientMessageType.AudioReceived, msg, False)
        LOGGER.debug(msg)
        return msg

    async def _wait_for_conversation_ended(self):
        """
        Waits for :py:attr:`models.ClientMessageType.ConversationEnded`
        message from the server.
        """
        await asyncio.wait_for(
            self._conversation_ended.wait(), self.conversation_ended_wait_timeout
        )

    async def _consumer(self, message, from_cli=False):
        """
        Consumes messages and acts on them.

        :param message: Message received from the server.
        :type message: str

        :raises ConversationError on an error message received from the
            server after the Session started.
        :raises ConversationEndedException: on models.ServerMessageType.ConversationEnded message
            received from the server.
        :raises ForceEndSession: If this was raised by the user's event
            handler.
        """
        if isinstance(message, (bytes, bytearray)):
            # Send ack as soon as we receive audio
            await self.websocket.send(self._audio_received())
            # add an audio message to local buffer only when running from cli
            if from_cli:
                await self._audio_buffer.put(message)
            # Implicit name for all inbound binary messages.
            # We must manually set it for event handler subscribed
            # to `ServerMessageType.AddAudio` messages to work.
            message_type = ServerMessageType.AddAudio
        else:
            LOGGER.debug(message)
            message = json.loads(message)
            message_type = message.get("message")

        if message_type is None:
            return

        if message_type not in self.event_handlers:
            LOGGER.warning(f"Unknown message type {message_type!r}")
            return

        for handler in self.event_handlers[message_type]:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(copy.deepcopy(message))
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        self._executor, handler, copy.deepcopy(message)
                    )
            except ForceEndSession:
                LOGGER.warning("Session was ended forcefully by an event handler")
                raise
            except Exception as e:
                LOGGER.error(f"Unhandled exception in {handler=}: {e=}")

        if message_type == ServerMessageType.ConversationStarted:
            self._flag_conversation_started()
        elif message_type == ServerMessageType.AudioAdded:
            self._buffer_semaphore.release()
        elif message_type == ServerMessageType.ConversationEnded:
            self._flag_conversation_ended()
            raise ConversationEndedException()
        elif message_type == ServerMessageType.Warning:
            LOGGER.warning(message["reason"])
        elif message_type == ServerMessageType.Error:
            raise ConversationError(message["reason"])

    async def _read_from_microphone(self):
        _pyaudio = pyaudio.PyAudio()
        print(
            f"Default input device: {_pyaudio.get_default_input_device_info()['name']}"
        )
        print(
            f"Default output device: {_pyaudio.get_default_output_device_info()['name']}"
        )
        print("Start speaking...")
        stream = _pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.audio_settings.sample_rate,
            input=True,
        )
        try:
            while True:
                if self._session_needs_closing or self._conversation_ended.is_set():
                    break

                await asyncio.wait_for(
                    self._buffer_semaphore.acquire(),
                    timeout=self.connection_settings.semaphore_timeout_seconds,
                )

                # audio_chunk size is 128 * 2 = 256 bytes which is about 8ms
                audio_chunk = stream.read(num_frames=128, exception_on_overflow=False)

                self.client_seq_no += 1
                self._call_middleware(ClientMessageType.AddAudio, audio_chunk, True)
                await self.websocket.send(audio_chunk)
                # send audio at a constant rate
                await asyncio.sleep(0.01)
        except KeyboardInterrupt:
            await self.websocket.send(self._end_of_audio())
        finally:
            await self._wait_for_conversation_ended()
            stream.stop_stream()
            stream.close()
            _pyaudio.terminate()

    async def _consumer_handler(self, from_cli=False):
        """
        Controls the consumer loop for handling messages from the server.

        raises: ConnectionClosedError when the upstream closes unexpectedly
        """
        while self.session_running:
            try:
                message = await self.websocket.recv()
            except websockets.exceptions.ConnectionClosedOK:
                # Can occur if a timeout has closed the connection.
                LOGGER.info("Cannot receive from closed websocket.")
                return
            except websockets.exceptions.ConnectionClosedError as ex:
                LOGGER.info("Disconnected while waiting for recv().")
                raise ex
            await self._consumer(message, from_cli)

    async def _stream_producer(self, stream, audio_chunk_size):
        async for audio_chunk in read_in_chunks(stream, audio_chunk_size):
            if self._session_needs_closing or self._conversation_ended.is_set():
                break
            await asyncio.wait_for(
                self._buffer_semaphore.acquire(),
                timeout=self.connection_settings.semaphore_timeout_seconds,
            )

            self.client_seq_no += 1
            self._call_middleware(ClientMessageType.AddAudio, audio_chunk, True)
            yield audio_chunk

    async def _producer_handler(self, interactions: List[Interaction]):
        """
        Controls the producer loop for sending messages to the server.
        """
        await self._conversation_started.wait()
        if interactions[0].stream.name == "<stdin>":
            return await self._read_from_microphone()

        for interaction in interactions:
            async for message in self._stream_producer(
                interaction.stream, self.audio_settings.chunk_size
            ):
                try:
                    await self.websocket.send(message)
                except Exception as e:
                    LOGGER.error(f"error sending message: {e}")
                    return
            if interaction.callback:
                interaction.callback(self)

        await self.websocket.send(self._end_of_audio())
        await self._wait_for_conversation_ended()

    async def _playback_handler(self):
        """
        Reads audio binary messages from the playback buffer and plays them to the user.
        """
        _pyaudio = pyaudio.PyAudio()
        stream = _pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.audio_settings.sample_rate,
            frames_per_buffer=128,
            output=True,
        )
        try:
            while True:
                if self._session_needs_closing or self._conversation_ended.is_set():
                    break
                try:
                    audio_message = await self._audio_buffer.get()
                    stream.write(audio_message)
                    self._audio_buffer.task_done()
                    # read from buffer at a constant rate
                    await asyncio.sleep(0.005)
                except Exception as e:
                    LOGGER.error(f"Error during audio playback: {e}")
                    raise e
        finally:
            stream.close()
            stream.stop_stream()
            _pyaudio.terminate()

    def _call_middleware(self, event_name, *args):
        """
        Call the middlewares attached to the client for the given event name.

        :raises ForceEndSession: If this was raised by the user's middleware.
        """
        for middleware in self.middlewares[event_name]:
            try:
                middleware(*args)
            except ForceEndSession:
                LOGGER.warning("Session was ended forcefully by a middleware")
                raise

    def add_event_handler(self, event_name, event_handler):
        """
        Add an event handler (callback function) to handle an incoming
        message from the server. Event handlers are passed a copy of the
        incoming message from the server. If `event_name` is set to 'all' then
        the handler will be added for every event.

        For example, a simple handler that just LOGGER.debugs out the
        :py:attr:`models.ServerMessageType.ConversationStarted`
        messages received:

        >>> client = WebsocketClient(
                ConnectionSettings(url="wss://localhost:9000"))
        >>> handler = lambda msg: LOGGER.debug(msg)
        >>> client.add_event_handler(ServerMessageType.ConversationStarted, handler)

        :param event_name: The name of the message for which a handler is
                being added. Refer to
                :py:class:`models.ServerMessageType` for a list
                of the possible message types.
        :type event_name: str

        :param event_handler: A function to be called when a message of the
            given type is received.
        :type event_handler: Callable[[dict], None]

        :raises ValueError: If the given event name is not valid.
        """
        # TODO: Remove when no longer supported
        if event_name in [ServerMessageType.audio, ServerMessageType.prompt]:
            LOGGER.warning(
                f"DeprecationWarning: '{event_name}' is deprecated and will be removed in future versions."
            )

        if event_name == "all":
            # Iterate through event handlers, excluding deprecated ServerMessageType.audio.
            for name in self.event_handlers.keys():
                if (
                    name == ServerMessageType.audio
                ):  # TODO: Remove when no longer supported
                    continue
                self.event_handlers[name].append(event_handler)
        elif event_name not in self.event_handlers:
            raise ValueError(
                f"Unknown event name: '{event_name}'. Expected 'all' or one of {list(self.event_handlers.keys())}."
            )
        else:
            # Map deprecated ServerMessageType.audio to ServerMessageType.AddAudio for compatibility.
            if (
                event_name == ServerMessageType.audio
            ):  # TODO: Remove when no longer supported
                event_name = ServerMessageType.AddAudio
            self.event_handlers[event_name].append(event_handler)

    def add_middleware(self, event_name, middleware):
        """
        Add middleware to handle outgoing messages sent to the server.
        Middlewares are passed a reference to the outgoing message, which
        they may alter.
        If `event_name` is set to 'all' then the handler will be added for
        every event.

        :param event_name: The name of the message for which middleware is
            being added. Refer to the V2 API docs for a list of the possible
            message types.
        :type event_name: str

        :param middleware: A function to be called to process an outgoing
            message of the given type. The function receives the message as
            the first argument and a second, boolean argument indicating
            whether the message is binary data (which implies it is an
            AddAudio message).
        :type middleware: Callable[[dict, bool], None]

        :raises ValueError: If the given event name is not valid.
        """
        if event_name == "all":
            for name in self.middlewares.keys():
                self.middlewares[name].append(middleware)
        elif event_name not in self.middlewares:
            raise ValueError(
                (
                    f"Unknown event name: {event_name}, expected to be 'all'"
                    f"or one of {list(self.middlewares.keys())}."
                )
            )
        else:
            self.middlewares[event_name].append(middleware)

    async def _communicate(self, interactions: List[Interaction], from_cli=False):
        """
        Create a producer/consumer for transcription messages and
        communicate with the server.
        Internal method called from _run.
        """
        try:
            start_conversation_msg = self._start_conversation()
        except ForceEndSession:
            return
        await self.websocket.send(start_conversation_msg)

        tasks = [
            asyncio.create_task(self._consumer_handler(from_cli)),
            asyncio.create_task(self._producer_handler(interactions)),
        ]

        # Run the playback task that plays audio messages to the user when started from cli
        if from_cli:
            self._audio_buffer = asyncio.Queue()
            tasks.append(asyncio.create_task(self._playback_handler()))

        (done, pending) = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_EXCEPTION,
        )

        # If a task is pending, the other one threw an exception, so tidy up
        for task in pending:
            task.cancel()

        for task in done:
            exc = task.exception()
            if exc and not isinstance(
                exc,
                (ForceEndSession, ConversationEndedException),
            ):
                raise exc

    async def run(
        self,
        interactions: List[Interaction],
        audio_settings: AudioSettings = AudioSettings(),
        conversation_config: ConversationConfig = None,
        from_cli: bool = False,
        tools: Optional[List[ToolFunctionParam]] = None,
    ):
        """
        Begin a new recognition session.
        This will run asynchronously. Most callers may prefer to use
        :py:meth:`run_synchronously` which will block until the session is
        finished.

        :param interactions: A list of interactions with FlowService API.
        :type interactions: List[Interaction]

        :param audio_settings: Configuration for the audio stream.
        :type audio_settings: models.AudioSettings

        :param conversation_config: Configuration for the conversation.
        :type conversation_config: models.ConversationConfig

        :param tools: Optional list of tool functions.
        :type tools: List[ToolFunctionParam]

        :raises Exception: Can raise any exception returned by the
            consumer/producer tasks.
        """
        self.client_seq_no = 0
        self.server_seq_no = 0
        self.conversation_config = conversation_config
        self.audio_settings = audio_settings
        self.tools = tools

        await self._init_synchronization_primitives()

        extra_headers = {}
        auth_token = self.connection_settings.auth_token
        if auth_token and self.connection_settings.generate_temp_token:
            auth_token = await get_temp_token(auth_token)
        extra_headers["Authorization"] = f"Bearer {auth_token}"
        try:
            async with websockets.connect(  # pylint: disable=no-member
                self.connection_settings.url,
                ssl=self.connection_settings.ssl_context,
                ping_timeout=self.connection_settings.ping_timeout_seconds,
                # Don't limit the max. size of incoming messages
                max_size=None,
                extra_headers=extra_headers,
            ) as self.websocket:
                await self._communicate(interactions, from_cli)
        finally:
            self.session_running = False
            self._session_needs_closing = False
            self.websocket = None

    def stop(self):
        """
        Indicates that the recognition session should be forcefully stopped.
        Only used in conjunction with `run`.
        You probably don't need to call this if you're running the client via
        :py:meth:`run_synchronously`.
        """
        self._session_needs_closing = True

    def run_synchronously(self, *args, timeout=None, **kwargs):
        """
        Run the transcription synchronously.
        :raises asyncio.TimeoutError: If the given timeout is exceeded.
        """
        # pylint: disable=no-value-for-parameter
        asyncio.run(asyncio.wait_for(self.run(*args, **kwargs), timeout=timeout))


async def get_temp_token(api_key):
    """
    Used to get a temporary token from management platform api
    """
    mp_api_url = os.getenv("SM_MANAGEMENT_PLATFORM_URL", "https://mp.speechmatics.com")
    endpoint = f"{mp_api_url}/v1/api_keys?type=flow"
    body = {"ttl": 300, "client_ref": "speechmatics-flow-python-client"}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = httpx.post(endpoint, json=body, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["key_value"]
