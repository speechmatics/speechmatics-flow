from dataclasses import asdict

import pytest

from speechmatics_flow import models

TEMPLATE_VARS = {
    "persona": "You are an aging English butler named Humphrey.",
    "style": "Be charming but unpredictable.",
    "context": "You are taking a customer's order for fast food.",
}


@pytest.mark.parametrize(
    "config, want",
    [
        ({}, {"type": "raw", "encoding": "pcm_s16le", "sample_rate": 16000}),
        (
            {"encoding": "pcm_f32le", "sample_rate": 44100},
            {"type": "raw", "encoding": "pcm_f32le", "sample_rate": 44100},
        ),
    ],
)
def test_audio_settings(config, want):
    audio_settings = models.AudioSettings(**config)
    got = audio_settings.asdict()
    assert got == want


@pytest.mark.parametrize(
    "config, want",
    [
        ({}, {"template_id": "default"}),
        (
            {"template_id": "test", "template_variables": TEMPLATE_VARS},
            {"template_id": "test", "template_variables": TEMPLATE_VARS},
        ),
    ],
)
def test_conversation_config(config, want):
    conversation_config = models.ConversationConfig(**config)
    got = conversation_config.asdict()
    assert got == want


@pytest.mark.parametrize(
    "config, want",
    [
        ({}, {"buffering": 10, "sample_rate": 16000, "chunk_size": 256}),
        (
            {"buffering": 20, "sample_rate": 8000, "chunk_size": 512},
            {"buffering": 20, "sample_rate": 8000, "chunk_size": 512},
        ),
    ],
)
def test_playback_settings(config, want):
    audio_settings = models.PlaybackSettings(**config)
    got = asdict(audio_settings)
    assert got == want


@pytest.mark.parametrize(
    "config, want",
    [
        ({}, {"llm": False}),
        ({"llm": False}, {"llm": False}),
        ({"llm": True}, {"llm": True}),
    ],
)
def test_debug_mode(config, want):
    debug_mode_settings = models.DebugMode(**config)
    got = debug_mode_settings.asdict()
    assert got == want
