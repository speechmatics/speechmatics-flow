import asyncio

import pyaudio


async def audio_playback(audio_queue: asyncio.Queue):
    """Continuously read from the audio queue and play audio back to the user."""

    p = pyaudio.PyAudio()
    player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)
    try:
        while True:
            audio = await audio_queue.get()
            player_stream.write(audio)
            await asyncio.sleep(0.005)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()
