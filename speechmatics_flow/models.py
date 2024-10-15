# (c) 2024, Cantab Research Ltd.
"""
Data models and message types used by the library.
"""

import io
import ssl
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Callable, Dict, Optional, Literal


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

    template_id: Literal[
        "default", "flow-service-assistant-amelia", "flow-service-assistant-humphrey"
    ] = "default"
    """Name of a predefined template."""

    template_variables: Optional[Dict[str, str]] = None
    """Optional parameter to allow overriding the default values of variables defined in the template."""

    def asdict(self):
        return asdict(
            self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )


class ClientMessageType(str, Enum):
    # pylint: disable=invalid-name
    """Defines various messages sent from client to server."""

    StartConversation = "StartConversation"
    """Initiates a conversation job based on configuration set previously."""

    AddAudio = "AddAudio"
    """Adds more audio data to the recognition job. The server confirms
    receipt by sending an :py:attr:`ServerMessageType.AudioAdded` message."""

    AudioEnded = "AudioEnded"
    """Indicates audio input has finished."""


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

    audio = "audio"
    """Message contains binary data"""

    prompt = "prompt"
    """Message contains text data"""

    ConversationEnded = "ConversationEnded"
    """Message indicates the session ended."""

    EndOfTranscript = "EndOfTranscript"
    """Server response to :py:attr:`ClientMessageType.EndOfStream`,
    after the server has finished sending all :py:attr:`AddTranscript`
    messages."""

    Info = "Info"
    """Indicates a generic info message."""

    Warning = "Warning"
    """Indicates a generic warning message."""

    Error = "Error"
    """Indicates n generic error message."""


@dataclass
class Interaction:
    """Defines various interactions between client and server."""

    stream: io.BufferedReader
    callback: Optional[Callable] = None
