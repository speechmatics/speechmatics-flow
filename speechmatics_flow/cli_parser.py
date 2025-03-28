# (c) 2024, Cantab Research Ltd.
"""
Parsers used by the CLI to handle CLI arguments
"""
import argparse
import logging

LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def get_arg_parser():
    """
    Creates a command-line argument parser objct

    :return: The argparser object with all commands and subcommands.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="CLI for Speechmatics Flow API.")
    parser.add_argument(
        "-v",
        dest="verbose",
        action="count",
        default=0,
        help=(
            "Set the log level for verbose logs. "
            "The number of flags indicate the level, eg. "
            "-v is INFO and -vv is DEBUG."
        ),
    )
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help=(
            "Prints useful symbols to represent the messages on the wire. "
            "Symbols are printed to STDERR, use only when STDOUT is "
            "redirected to a file."
        ),
    )
    parser.add_argument(
        "--url",
        default="wss://flow.api.speechmatics.com/v1/flow",
        type=str,
        help="Websocket url for Flow API",
    )
    parser.add_argument(
        "--auth-token",
        type=str,
        help="Authentication token to authorize the client.",
    )
    parser.add_argument(
        "--generate-temp-token",
        default="true",
        choices=["true", "false"],
        help="Automatically generate a temporary token for authentication.",
    )
    parser.add_argument(
        "--ssl-mode",
        default="regular",
        choices=["regular", "insecure", "none"],
        help=(
            "Use a preset configuration for the SSL context. With `regular` "
            "mode a valid certificate is expected. With `insecure` mode"
            " a self signed certificate is allowed."
            " With `none` then SSL is not used."
        ),
    )
    parser.add_argument(
        "--raw",
        metavar="ENCODING",
        type=str,
        default="pcm_s16le",
        help=(
            "Indicate that the input audio is raw, provide the encoding"
            "of this raw audio, eg. pcm_f32le."
        ),
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16_000,
        help="The sample rate in Hz of the input audio, if in raw format.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=256,
        help=(
            "How much audio data, in bytes, to send to the server in each "
            "websocket message. Larger values can increase latency, but "
            "values which are too small create unnecessary overhead."
        ),
    )
    parser.add_argument(
        "--buffer-size",
        default=512,
        type=int,
        help=(
            "Maximum number of messages to send before waiting for"
            "acknowledgements from the server."
        ),
    )
    parser.add_argument(
        "--playback-buffering",
        type=int,
        default=10,
        help=(
            "Buffer (in milliseconds) for audio received from the server before playback. "
            "Increasing the buffer size can improve resilience to poor network conditions, "
            "at the cost of increased latency."
        ),
    ),
    parser.add_argument(
        "--playback-sample-rate",
        type=int,
        default=16_000,
        help="The sample rate in Hz of the output audio.",
    )
    parser.add_argument(
        "--playback-chunk-size",
        type=int,
        default=256,
        help=(
            "The size of each audio chunk, in bytes, to read from the audio buffer. "
            "Increasing the chunk size may improve playback smoothness."
        ),
    )
    parser.add_argument(
        "--print-json",
        default=False,
        action="store_true",
        help=(
            "Print the JSON partial & final transcripts received rather than "
            "plaintext messages."
        ),
    )
    parser.add_argument(
        "--config-file",
        dest="config_file",
        type=str,
        default=None,
        help="Read the conversation config from a file."
        " If you provide this, all other config options work as overrides.",
    )
    parser.add_argument(
        "--assistant",
        default=None,
        type=str,
        help="Choose your assistant.",
    )
    parser.add_argument(
        "--llm-debug-enabled",
        default=False,
        action="store_true",
        help="Flag indicating whether to receive conversations between the LLM and the Flow backend in debug messages.",
    )

    return parser


def parse_args(args=None):
    """
    Parses command-line arguments.

    :param args: List of arguments to parse.
    :type args: (List[str], optional)

    :return: The set of arguments provided along with their values.
    :rtype: Namespace
    """
    parser = get_arg_parser()
    parsed_args = parser.parse_args(args=args)
    return parsed_args
