# (c) 2024, Cantab Research Ltd.
"""
Data models and message types used by the library.
"""

import io
import ssl
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Dict, Optional, BinaryIO, IO, Union

from speechmatics_flow.templates import TemplateID


@dataclass
class AudioSettings:
    """Defines audio parameters."""

    encoding: str = "pcm_s16le"
    """Encoding format when raw audio is used. Allowed values are
    `pcm_f32le` and `pcm_s16le`"""

    sample_rate: int = 16000
    """Sampling rate in hertz."""

    chunk_size: int = 256
    """Chunk size in bytes."""

    def asdict(self):
        return {
            "type": "raw",
            "encoding": self.encoding,
            "sample_rate": self.sample_rate,
        }


@dataclass
class PlaybackSettings:
    """Defines audio playback parameters."""

    buffering: int = 10
    """Buffer (in milliseconds) for audio received from the server before playback.
    Increasing the buffer size can improve resilience to poor network conditions, at the cost of increased latency."""

    sample_rate: int = 16000
    """Sampling rate in hertz."""

    chunk_size: int = 256
    """Chunk size in bytes."""


@dataclass
class ConnectionSettings:
    """Defines connection parameters."""

    url: str
    """Websocket server endpoint."""

    message_buffer_size: int = 512
    """Message buffer size in bytes."""

    ssl_context: ssl.SSLContext = field(default_factory=ssl.create_default_context)
    """SSL context."""

    semaphore_timeout_seconds: float = 120
    """Semaphore timeout in seconds."""

    ping_timeout_seconds: float = 60
    """Ping-pong timeout in seconds."""

    auth_token: Optional[str] = None
    """auth token to authenticate a customer."""

    generate_temp_token: Optional[bool] = True
    """Automatically generate a temporary token for authentication."""


@dataclass
class ConversationConfig:
    """Defines configuration parameters for conversation requests."""

    template_id: Union[TemplateID, str] = "default"
    """Name of a predefined template."""

    template_variables: Optional[Dict[str, str]] = None
    """Optional parameter to allow overriding the default values of variables defined in the template."""

    def asdict(self):
        return asdict(
            self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )


@dataclass
class DebugMode:
    """Defines debug flags for monitoring and troubleshooting Flow"""

    llm: bool = False
    """Optional Flag indicating whether to receive conversations between the LLM and the Flow backend as
    debug messages."""

    def asdict(self):
        return asdict(self)


class ClientMessageType(str, Enum):
    # pylint: disable=invalid-name
    """Defines various messages sent from client to server."""

    StartConversation = "StartConversation"
    """Initiates a conversation job based on configuration set previously."""

    AddAudio = "AddAudio"
    """Implicit name for all outbound binary messages. The server confirms
    receipt by sending an :py:attr:`ServerMessageType.AudioAdded` message."""

    AudioReceived = "AudioReceived"
    """Client response to :py:attr:`ServerMessageType.AddAudio`, indicating
    that audio has been added successfully."""

    AudioEnded = "AudioEnded"
    """Indicates audio input has finished."""

    ToolResult = "ToolResult"
    """Client response to :py:attr:`ServerMessageType.ToolInvoke`, containing
    the result of the function call."""


class ServerMessageType(str, Enum):
    # pylint: disable=invalid-name
    """Defines various message types sent from server to client."""

    ConversationStarted = "ConversationStarted"
    """Server response to :py:attr:`ClientMessageType.StartConversation`,
    acknowledging that a conversation session has started."""

    AddPartialTranscript = "AddPartialTranscript"
    """Indicates a partial transcript, which is an incomplete transcript that
    is immediately produced and may change as more context becomes available.
    """

    AudioAdded = "AudioAdded"
    """Server response to :py:attr:`ClientMessageType.AddAudio`, indicating
    that audio has been added successfully."""

    AddTranscript = "AddTranscript"
    """Indicates the final transcript of a part of the audio."""

    ResponseStarted = "ResponseStarted"
    """
    Indicates the start of TTS audio streaming from the server.
    The message contains the textual content of the utterance to be spoken.
    """

    ResponseCompleted = "ResponseCompleted"
    """Indicates the completion of TTS audio transmission from the server.
    The message includes the textual content of the utterance just spoken.
    """

    ResponseInterrupted = "ResponseInterrupted"
    """Indicates an interruption in the TTS audio stream from the server.
    The message contains the textual content up to the point where the utterance was stopped.
    """

    AddAudio = "AddAudio"
    """Implicit name for all outbound binary messages. The client confirms
    receipt by sending an :py:attr:`ClientMessageType.AudioReceived` message."""

    audio = "audio"
    """Message contains binary data"""

    prompt = "prompt"
    """Message contains text data"""

    ConversationEnding = "ConversationEnding"
    """Indicates the session will continue in one-sided mode
    during TTS playback of the final words."""

    ConversationEnded = "ConversationEnded"
    """Message indicates the session ended."""

    ToolInvoke = "ToolInvoke"
    """Indicates invocation of a function call. The client responds by sending
    an :py:attr:`ClientMessageType.ToolResult` message.
    """

    Info = "Info"
    """Indicates a generic info message."""

    Warning = "Warning"
    """Indicates a generic warning message."""

    Error = "Error"
    """Indicates a generic error message."""

    Debug = "Debug"
    """Indicates a debug message"""


@dataclass
class Interaction:
    """
    Defines a single interaction between a client and a server, typically
    used to handle non-continuous streams such as an audio file. This class
    enables the server to respond after the stream has finished or based
    on the specified callback function, allowing flexibility in connection
    handling after streaming.

    Attributes:
        stream (io.IOBase | BinaryIO | IO[bytes]): A file-like object for reading audio data.
            This object should support binary read operations, such as `read()` and `readinto()`.
            Suitable for audio streams that can be processed incrementally.
        callback (Optional[Callable]): An optional function to be executed when
            the audio stream ends. This can be used to delay connection closure
            or perform additional actions upon stream completion.

    Examples:
        Keep the connection open for an additional 2 seconds after streaming
        an audio file, allowing time for the server to respond.

        ```python
        Interaction(audio_stream, callback=lambda x: time.sleep(2))
        ```
    """

    stream: Union[io.IOBase, BinaryIO, IO[bytes]]

    callback: Optional[Callable] = None
