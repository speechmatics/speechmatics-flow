#!/usr/bin/env python3
# (c) 2024, Cantab Research Ltd.
"""
Command-line interface
"""

import json
import logging
import ssl
import sys
from dataclasses import dataclass
from socket import gaierror

import httpx
from websockets.exceptions import WebSocketException

from speechmatics_flow.cli_parser import parse_args
from speechmatics_flow.client import WebsocketClient
from speechmatics_flow.exceptions import ConversationError
from speechmatics_flow.models import (
    AudioSettings,
    ConversationConfig,
    ServerMessageType,
    Interaction,
    ConnectionSettings,
    PlaybackSettings,
    DebugMode,
)
from speechmatics_flow.templates import TEMPLATE_NAME_TO_ID

LOGGER = logging.getLogger(__name__)


@dataclass
class Transcripts:
    user_transcript: str = ""
    agent_transcript: str = ""


def get_log_level(verbosity):
    """
    Returns the appropriate log level given a verbosity level.

    :param verbosity: Verbosity level.
    :type verbosity: int

    :return: The logging level (eg. logging.INFO).
    :rtype: int

    :raises SystemExit: If the given verbosity level is invalid.
    """
    try:
        log_level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}[verbosity]

        return log_level
    except KeyError as error:
        key = int(str(error))
        raise SystemExit(
            f"Only supports 2 log levels eg. -vv, you are asking for " f"-{'v' * key}"
        ) from error


def get_connection_settings(args):
    """
    Helper function which returns a ConnectionSettings object based on the
    command line options given to the program.

    :param args: Keyword arguments, typically from the command line.
    :type args: dict

    :return: Settings for the WebSocket connection.
    :rtype: models.ConnectionSettings
    """
    auth_token = args.get("auth_token")
    url = args.get("url")
    settings = ConnectionSettings(
        url=url,
        auth_token=auth_token,
        generate_temp_token=args.get("generate_temp_token") == "true",
    )

    if args.get("buffer_size") is not None:
        settings.message_buffer_size = args["buffer_size"]

    if args.get("ssl_mode") == "insecure":
        settings.ssl_context.check_hostname = False
        settings.ssl_context.verify_mode = ssl.CERT_NONE
    elif args.get("ssl_mode") == "none":
        settings.ssl_context = None

    return settings


def get_conversation_config(
    args,
):
    """
    Helper function which returns a ConversationConfig object based on the
    command line options given to the program.

    :param args: Keyword arguments probably from the command line.
    :type args: Dict

    :return: Settings for the Flow engine.
    :rtype: models.ConversationConfig
    """

    config = {}
    # First, get configuration from the config file if provided.
    if args.get("config_file"):
        with open(args["config_file"], encoding="utf-8") as config_file:
            config = json.load(config_file)

    if config.get("conversation_config"):
        config = config["conversation_config"]

    # Command line arguments override values from config file
    if assistant := args.get("assistant"):
        config["template_id"] = TEMPLATE_NAME_TO_ID.get(assistant.lower(), assistant)

    return ConversationConfig(**config)


def get_audio_settings(args):
    """
    Helper function which returns an AudioSettings object based on the command
    line options given to the program.

    Args:
        args (dict): Keyword arguments, typically from the command line.

    Returns:
        models.AudioSettings: Settings for the audio stream
            in the connection.
    """
    settings = AudioSettings(
        sample_rate=args.get("sample_rate"),
        chunk_size=args.get("chunk_size"),
        encoding=args.get("raw"),
    )
    return settings


def get_playback_settings(args):
    """
    Helper function which returns a PlaybackSettings object based on the command
    line options given to the program.

    Args:
        args (dict): Keyword arguments, typically from the command line.

    Returns:
        models.PlaybackSettings: Settings for the audio playback stream
            in the connection.
    """
    return PlaybackSettings(
        buffering=args.get("playback_buffering"),
        sample_rate=args.get("playback_sample_rate"),
        chunk_size=args.get("playback_chunk_size"),
    )


def get_debug_mode_settings(args):
    return DebugMode(llm=args.get("llm_debug_enabled"))


# pylint: disable=too-many-arguments,too-many-statements
def add_printing_handlers(
    api,
    transcripts,
    print_json=False,
):
    """
    Adds a set of handlers to the websocket client which print out transcripts
    as they are received. This includes partials if they are enabled.

    Args:
        api (client.WebsocketClient): Client instance.
        transcripts (Transcripts): Allows the transcripts to be concatenated to
            produce a final result.
        print_json (bool, optional): Whether to print json transcript messages.
    """
    escape_seq = "\33[2K" if sys.stdout.isatty() else ""

    def convert_to_txt(message):
        if print_json:
            print(json.dumps(message))
            return
        transcript = message["metadata"]["transcript"]
        return transcript.replace("<sb> ", "").replace("</sb>", "").replace("<sb>", "")

    def transcript_handler(message):
        plaintext = convert_to_txt(message)
        if plaintext:
            sys.stdout.write(f"{escape_seq}{plaintext}\n")
        transcripts.user_transcript += plaintext

    def partial_transcript_handler(message):
        plaintext = convert_to_txt(message)
        if plaintext:
            sys.stderr.write(f"{escape_seq}{plaintext}\r")

    def prompt_handler(message):
        if print_json:
            print(json.dumps(message))
            return
        new_response = message["content"]
        new_plaintext_response = new_response.replace("<sb> ", "").replace("</sb> ", "")
        if new_plaintext_response:
            sys.stdout.write(f"{escape_seq}{new_plaintext_response}\n")
        transcripts.user_transcript += new_plaintext_response

    api.add_event_handler(ServerMessageType.ResponseStarted, prompt_handler)
    api.add_event_handler(ServerMessageType.AddTranscript, transcript_handler)
    api.add_event_handler(
        ServerMessageType.AddPartialTranscript, partial_transcript_handler
    )


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def main(args=None):
    """
    Main entrypoint.

    :param args: command-line arguments; defaults to None in which
            case arguments will be retrieved from `sys.argv` (this is useful
            mainly for unit tests).
    :type args: List[str]
    """
    if not args:
        args = vars(parse_args())

    logging.basicConfig(level=get_log_level(args["verbose"]))
    LOGGER.info("Args: %s", args)

    try:
        flow_main(args)
    except (KeyboardInterrupt, ValueError, ConversationError, KeyError) as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(f"{type(error).__name__}: {error}")
    except FileNotFoundError as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(
            f"FileNotFoundError: {error.strerror}: '{error.filename}'."
            + " Check to make sure the filename is spelled correctly, and that the file exists."
        )
    except httpx.HTTPStatusError as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(error.response.text)
    except httpx.HTTPError as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(f"httpx.HTTPError: An unexpected http error occurred. {error}")
    except ConnectionResetError as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(
            f"ConnectionResetError: {error}.\n\nThe most likely reason for this is that the client "
            + "has been configured to use SSL but the server does not support SSL. "
            + "If this is the case then try using --ssl-mode=none"
        )
    except (WebSocketException, gaierror) as error:
        LOGGER.info(error, exc_info=True)
        sys.exit(
            f"WebSocketError: An unexpected error occurred in the websocket: {error}.\n\n"
            + "Check that the url and config provided is valid, "
            + "and that the language in the url matches the config.\n"
        )


def flow_main(args):
    """Main dispatch for "flow" mode commands.

    :param args: arguments from parse_args()
    :type args: argparse.Namespace
    """
    settings = get_connection_settings(args)
    api = WebsocketClient(settings)
    transcripts = Transcripts()
    add_printing_handlers(
        api,
        transcripts,
        print_json=args["print_json"],
    )

    def run(stream):
        try:
            api.run_synchronously(
                interactions=[Interaction(stream)],
                audio_settings=get_audio_settings(args),
                conversation_config=get_conversation_config(args),
                playback_settings=get_playback_settings(args),
                debug_mode=get_debug_mode_settings(args),
                from_cli=True,
            )
        except KeyboardInterrupt:
            # Gracefully handle Ctrl-C, else we get a huge stack-trace.
            LOGGER.warning("Keyboard interrupt received.")

    run(sys.stdin.buffer)


if __name__ == "__main__":
    main()
