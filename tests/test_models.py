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
