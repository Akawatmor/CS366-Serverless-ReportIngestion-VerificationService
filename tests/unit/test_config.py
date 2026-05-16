"""Tests for src/config.py Gemini configuration helpers."""

from unittest.mock import patch


def test_numbered_models_become_default_chain():
    with patch.dict(
        "os.environ",
        {
            "GEMINI_MODEL1": "gemini-3.1-flash-lite",
            "GEMINI_MODEL2": "gemini-3-flash-preview",
            "GEMINI_MODEL3": "gemma-4-26b-a4b-it",
        },
        clear=True,
    ):
        from src.config import Config

        cfg = Config()

    assert cfg.GEMINI_MODEL == "gemini-3.1-flash-lite"
    assert cfg.GEMINI_MODEL_FALLBACKS == [
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
        "gemma-4-26b-a4b-it",
    ]


def test_placeholder_keys_and_models_are_ignored():
    with patch.dict(
        "os.environ",
        {
            "GEMINI_API_KEY1": "-",
            "GEMINI_API_KEY2": "real-key-2",
            "GEMINI_MODEL1": "-",
            "GEMINI_MODEL2": "your_model_here",
            "GEMINI_MODEL3": "gemini-2.5-flash",
        },
        clear=True,
    ):
        from src.config import Config

        cfg = Config()

    assert cfg.GEMINI_API_KEYS == ["real-key-2"]
    assert cfg.GEMINI_MODEL == "gemini-2.5-flash"
    assert cfg.GEMINI_MODEL_FALLBACKS == ["gemini-2.5-flash"]
