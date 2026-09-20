"""
Unit Tests — AI Assistant (Somesh's module)
============================================
Tests for LLM orchestrator with Featherless AI + NVIDIA NIM fallback.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.assistant import (
    call_llm_with_fallback,
    execute_default_tool,
    get_featherless_client,
    get_nvidia_nim_client,
    _resolve_featherless_model,
    _resolve_nim_model,
    research_query,
    explain_backtest,
)


class TestModelResolution:
    """Test model name normalization."""

    def test_resolve_featherless_model_gpt_oss_120b(self):
        assert _resolve_featherless_model("gpt-oss-120b") == "openai/gpt-oss-120b"
        assert _resolve_featherless_model("openai/gpt-oss-120b") == "openai/gpt-oss-120b"

    def test_resolve_featherless_model_other(self):
        assert _resolve_featherless_model("other-model") == "other-model"

    def test_resolve_nim_model_gpt_oss_variants(self):
        assert _resolve_nim_model("gpt-oss-120b") == "openai/gpt-oss-20b"
        assert _resolve_nim_model("openai/gpt-oss-120b") == "openai/gpt-oss-20b"
        assert _resolve_nim_model("gpt-oss-20b") == "openai/gpt-oss-20b"
        assert _resolve_nim_model("openai/gpt-oss-20b") == "openai/gpt-oss-20b"

    def test_resolve_nim_model_other(self):
        assert _resolve_nim_model("llama-3.1") == "llama-3.1"


class TestClientCreation:
    """Test LLM client creation functions."""

    @patch("app.ai.assistant.settings")
    def test_get_featherless_client_with_key(self, mock_settings):
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.LLM_BASE_URL = "https://api.featherless.ai/v1"
        client = get_featherless_client()
        assert client is not None
        assert client.api_key == "test-key"
        assert str(client.base_url) == "https://api.featherless.ai/v1/"

    @patch("app.ai.assistant.settings")
    def test_get_featherless_client_no_key(self, mock_settings):
        mock_settings.LLM_API_KEY = None
        client = get_featherless_client()
        assert client is None

    @patch("app.ai.assistant.settings")
    def test_get_nvidia_nim_client_with_key(self, mock_settings):
        mock_settings.nvidia_nim_key_list = ["key1", "key2"]
        mock_settings.NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
        client = get_nvidia_nim_client("explicit-key")
        assert client is not None
        assert client.api_key == "explicit-key"

    @patch("app.ai.assistant.settings")
    def test_get_nvidia_nim_client_from_list(self, mock_settings):
        mock_settings.nvidia_nim_key_list = ["key1", "key2"]
        mock_settings.NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
        import app.ai.assistant as assistant_module
        assistant_module._nim_key_index = 0
        client = get_nvidia_nim_client()
        assert client is not None
        assert client.api_key == "key1"

    @patch("app.ai.assistant.settings")
    def test_get_nvidia_nim_client_no_keys(self, mock_settings):
        mock_settings.nvidia_nim_key_list = []
        client = get_nvidia_nim_client()
        assert client is None


class TestCallLLMWithFallback:
    """Test the main LLM calling function with fallback logic."""

    @patch("app.ai.assistant.get_featherless_client")
    @patch("app.ai.assistant.settings")
    def test_call_llm_featherless_success(self, mock_settings, mock_get_client):
        mock_settings.LLM_MODEL = "gpt-oss-120b"
        mock_settings.LLM_API_KEY = "test-key"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Featherless"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        response, provider, model = call_llm_with_fallback(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.1,
            max_tokens=100,
        )

        assert provider == "featherless"
        assert model == "openai/gpt-oss-120b"
        assert response == mock_response

    @patch("app.ai.assistant.get_featherless_client")
    @patch("app.ai.assistant.settings")
    def test_call_llm_featherless_exception(self, mock_settings, mock_get_client):
        """Test Featherless AI exception triggers fallback."""
        mock_settings.LLM_MODEL = "gpt-oss-120b"
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.NVIDIA_NIM_MODEL = "gpt-oss-20b"
        mock_settings.nvidia_nim_key_list = ["nim-key-1"]
        mock_settings.NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Featherless failed")
        mock_get_client.return_value = mock_client

        with patch("app.ai.assistant.OpenAI") as mock_openai:
            mock_nim_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello from NVIDIA"
            mock_nim_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_nim_client

            import app.ai.assistant as assistant_module
            assistant_module._nim_key_index = 0

            response, provider, model = call_llm_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
            )

        assert provider == "nvidia_nim"

    @patch("app.ai.assistant.get_featherless_client")
    @patch("app.ai.assistant.settings")
    def test_call_llm_fallback_to_nvidia(self, mock_settings, mock_get_featherless):
        mock_settings.LLM_MODEL = "gpt-oss-120b"
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.NVIDIA_NIM_MODEL = "gpt-oss-20b"
        mock_settings.nvidia_nim_key_list = ["nim-key-1", "nim-key-2"]
        mock_settings.NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

        mock_get_featherless.return_value = None

        with patch("app.ai.assistant.OpenAI") as mock_openai:
            mock_nim_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello from NVIDIA NIM"
            mock_nim_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_nim_client

            import app.ai.assistant as assistant_module
            assistant_module._nim_key_index = 0

            response, provider, model = call_llm_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.1,
                max_tokens=100,
            )

        assert provider == "nvidia_nim"
        assert model == "openai/gpt-oss-20b"
        assert response == mock_response

    @patch("app.ai.assistant.get_featherless_client")
    @patch("app.ai.assistant.settings")
    def test_call_llm_with_tools(self, mock_settings, mock_get_client):
        mock_settings.LLM_MODEL = "gpt-oss-120b"
        mock_settings.LLM_API_KEY = "test-key"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Tool response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        response, provider, model = call_llm_with_fallback(
            messages=[{"role": "user", "content": "Use tool"}],
            tools=tools,
            tool_choice="auto",
        )

        assert provider == "featherless"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools

    @patch("app.ai.assistant.get_featherless_client")
    @patch("app.ai.assistant.settings")
    def test_call_llm_all_nvidia_keys_fail(self, mock_settings, mock_get_featherless):
        """Test all NVIDIA NIM keys fail - raises last error."""
        mock_settings.LLM_MODEL = "gpt-oss-120b"
        mock_settings.LLM_API_KEY = "test-key"
        mock_settings.NVIDIA_NIM_MODEL = "gpt-oss-20b"
        mock_settings.nvidia_nim_key_list = ["nim-key-1", "nim-key-2"]
        mock_settings.NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

        mock_get_featherless.return_value = None

        with patch("app.ai.assistant.OpenAI") as mock_openai:
            mock_nim_client = MagicMock()
            mock_nim_client.chat.completions.create.side_effect = Exception("NIM failed")
            mock_openai.return_value = mock_nim_client

            import app.ai.assistant as assistant_module
            assistant_module._nim_key_index = 0

            with pytest.raises(Exception, match="NIM failed"):
                call_llm_with_fallback(
                    messages=[{"role": "user", "content": "Hello"}],
                )


class TestExecuteDefaultTool:
    """Test the default tool executor for CoinGecko integration."""

    @pytest.mark.asyncio
    @patch("app.ai.assistant.coingecko_client")
    async def test_get_crypto_price(self, mock_coingecko):
        mock_coingecko.get_simple_price = AsyncMock(
            return_value={"bitcoin": {"usd": 50000}, "ethereum": {"usd": 3000}}
        )
        result = await execute_default_tool(
            "get_crypto_price",
            {"coin_ids": ["bitcoin", "ethereum"], "vs_currencies": ["usd"]},
        )
        assert "bitcoin" in result
        assert result["bitcoin"]["usd"] == 50000

    @pytest.mark.asyncio
    @patch("app.ai.assistant.coingecko_client")
    async def test_get_crypto_market_chart(self, mock_coingecko):
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "price": np.array([50000, 51000, 50500]),
            "return": np.array([0.01, -0.005, 0.02]),
        })
        mock_coingecko.get_market_chart = AsyncMock(return_value=df)
        result = await execute_default_tool(
            "get_crypto_market_chart",
            {"coin_id": "bitcoin", "days": 30, "vs_currency": "usd"},
        )
        assert result["coin_id"] == "bitcoin"
        assert result["days"] == 30
        assert result["data_points"] == 3

    @pytest.mark.asyncio
    @patch("app.ai.assistant.coingecko_client")
    async def test_get_trending_crypto(self, mock_coingecko):
        mock_coingecko.get_trending = AsyncMock(
            return_value=[{"id": "bitcoin", "name": "Bitcoin"}]
        )
        result = await execute_default_tool("get_trending_crypto", {})
        assert "trending" in result
        assert len(result["trending"]) == 1

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        result = await execute_default_tool("unknown_tool", {"arg": "value"})
        assert result == {"info": "Tool unknown_tool executed with args {'arg': 'value'}"}


class TestResearchQuery:
    """Test the research_query function."""

    @pytest.mark.asyncio
    @patch("app.ai.assistant.call_llm_with_fallback")
    async def test_research_query_no_tools(self, mock_call_llm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Direct answer"
        mock_response.choices[0].message.tool_calls = None
        mock_call_llm.return_value = (mock_response, "featherless", "model")

        result = await research_query("What is Bitcoin?", tool_executor=None, conversation_history=None)

        assert result["response"] == "Direct answer"
        assert result["tools_called"] == []
        assert result["model"] == "model"
        assert result["provider"] == "featherless"

    @pytest.mark.asyncio
    @patch("app.ai.assistant.call_llm_with_fallback")
    @patch("app.ai.assistant.execute_default_tool")
    async def test_research_query_with_tools(self, mock_execute_tool, mock_call_llm):
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_crypto_price"
        mock_tool_call.function.arguments = json.dumps({"coin_ids": ["bitcoin"]})

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = None
        mock_response1.choices[0].message.tool_calls = [mock_tool_call]

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "Bitcoin price is $50,000"
        mock_response2.choices[0].message.tool_calls = None

        mock_call_llm.side_effect = [
            (mock_response1, "featherless", "model"),
            (mock_response2, "featherless", "model"),
        ]
        mock_execute_tool.return_value = {"bitcoin": {"usd": 50000}}

        result = await research_query("What is Bitcoin price?", tool_executor=None)

        assert "Bitcoin price is" in result["response"]
        assert len(result["tools_called"]) == 1
        assert result["tools_called"][0]["name"] == "get_crypto_price"

    @pytest.mark.asyncio
    @patch("app.ai.assistant.call_llm_with_fallback")
    async def test_research_query_error_handling(self, mock_call_llm):
        mock_call_llm.side_effect = Exception("API Error")

        result = await research_query("Test query")

        assert "error" in result
        assert "API Error" in result["error"]
        assert "tools_called" in result

    @patch("app.ai.assistant.call_llm_with_fallback")
    @pytest.mark.asyncio
    async def test_research_query_tool_executor_error(self, mock_call_llm):
        """Test tool executor error handling."""
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_crypto_price"
        mock_tool_call.function.arguments = '{"coin_ids": ["bitcoin"]}'

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock()]
        mock_response1.choices[0].message.content = None
        mock_response1.choices[0].message.tool_calls = [mock_tool_call]

        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock()]
        mock_response2.choices[0].message.content = "Result"
        mock_response2.choices[0].message.tool_calls = None

        mock_call_llm.side_effect = [
            (mock_response1, "featherless", "model"),
            (mock_response2, "featherless", "model"),
        ]

        async def failing_executor(name, args):
            raise Exception("Tool failed")

        result = await research_query("Test", tool_executor=failing_executor)

        assert "tools_called" in result
        assert len(result["tools_called"]) == 1
        # Should handle tool error gracefully


class TestExplainBacktest:
    """Test the explain_backtest function."""

    @pytest.mark.asyncio
    @patch("app.ai.assistant.call_llm_with_fallback")
    async def test_explain_backtest_success(self, mock_call_llm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Backtest shows positive returns with low risk."
        mock_call_llm.return_value = (mock_response, "featherless", "model")

        backtest_result = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
        }
        result = await explain_backtest(backtest_result)

        assert "positive returns" in result.lower()
        assert "low risk" in result.lower()

    @pytest.mark.asyncio
    @patch("app.ai.assistant.call_llm_with_fallback")
    async def test_explain_backtest_fallback(self, mock_call_llm):
        mock_call_llm.side_effect = Exception("LLM unavailable")

        backtest_result = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
        }
        result = await explain_backtest(backtest_result)

        assert "Total Return: 0.15" in result
        assert "Sharpe: 1.2" in result
        assert "LLM explanation unavailable" in result