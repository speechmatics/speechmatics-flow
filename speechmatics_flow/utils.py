# (c) 2024, Cantab Research Ltd.
"""
Helper functions used by the library.
"""

import asyncio
import concurrent.futures
import importlib.metadata
import inspect
import json
from pathlib import Path


def json_utf8(func):
    """A decorator to turn a function's return value into JSON"""

    def wrapper(*args, **kwargs):
        """wrapper"""
        return json.dumps(func(*args, **kwargs))

    return wrapper


async def read_in_chunks(stream, chunk_size):
    """
    Utility method for reading in and yielding chunks

    :param stream: file-like object to read audio from
    :type stream: io.IOBase

    :param chunk_size: maximum chunk size in bytes
    :type chunk_size: int

    :raises ValueError: if no data was read from the stream

    :return: a sequence of chunks of data where the length in bytes of each
        chunk is <= max_sample_size and a multiple of max_sample_size
    :rtype: collections.AsyncIterable

    """
    while True:
        # Work with both async and synchronous file readers.
        if inspect.iscoroutinefunction(stream.read):
            audio_chunk = await stream.read(chunk_size)
        else:
            # Run the read() operation in a separate thread to avoid blocking the event loop.
            with concurrent.futures.ThreadPoolExecutor() as executor:
                audio_chunk = await asyncio.get_event_loop().run_in_executor(
                    executor, stream.read, chunk_size
                )

        if not audio_chunk:
            break
        yield audio_chunk


def get_version() -> str:
    """Reads the version number from the package or VERSION file"""
    try:
        return importlib.metadata.version(__package__)
    except importlib.metadata.PackageNotFoundError:
        version_path = Path(__file__).resolve().parent.parent / "VERSION"
        if version_path.exists():
            return version_path.read_text(encoding="utf-8").strip()
        return "0.0.0"
