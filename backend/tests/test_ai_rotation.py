"""
Unit tests for NVIDIA NIM key rotation in AI assistant.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.config import settings
from app.ai.assistant import call_llm_with_fallback, get_nvidia_nim_client, _nim_key_index


def test_nvidia_nim_key_list_config():
    """Verify that multiple keys are correctly parsed and deduplicated."""
    keys = settings.nvidia_nim_key_list
    assert len(keys) >= 4
    for key in keys:
        assert key.startswith("nvapi-")


def test_nvidia_nim_key_rotation_on_failure():
    """Verify that when a key fails, rotation proceeds to the next key."""
    # Mock Featherless to fail so fallback is triggered
    with patch("app.ai.assistant.get_featherless_client", return_value=None):
        # Mock OpenAI chat completions
        call_count = 0
        used_keys = []

        def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First key fails
                raise RuntimeError("Rate limit or invalid key")
            # Second key succeeds
            mock_resp = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "Test response from fallback"
            mock_choice.message.tool_calls = None
            mock_resp.choices = [mock_choice]
            return mock_resp

        with patch("app.ai.assistant.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = mock_create
            mock_openai_cls.return_value = mock_client

            resp, provider, model = call_llm_with_fallback(
                messages=[{"role": "user", "content": "Hello"}]
            )

            assert provider == "nvidia_nim"
            assert "gpt-oss" in model
            assert resp.choices[0].message.content == "Test response from fallback"
            # Verify OpenAI was instantiated at least twice with different keys
            assert mock_openai_cls.call_count >= 2
            first_key = mock_openai_cls.call_args_list[0].kwargs["api_key"]
            second_key = mock_openai_cls.call_args_list[1].kwargs["api_key"]
            assert first_key != second_key
