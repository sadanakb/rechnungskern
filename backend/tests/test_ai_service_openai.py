"""Tests for OpenAI GPT-4o-mini integration in ai_service (Task 1)."""
import pytest
from unittest.mock import MagicMock, patch


class TestAiServiceOpenAI:

    def test_select_provider_returns_openai_when_key_set(self):
        """When openai_api_key is set, standard tasks should use OpenAI."""
        from app.ai_service import _select_provider
        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = ""
            mock_settings.mistral_api_key = ""
            result = _select_provider("standard")
        from app.ai_service import AiProvider
        assert result == AiProvider.OPENAI

    def test_select_provider_falls_back_to_anthropic_when_no_openai(self):
        """When no openai key but anthropic key exists, use anthropic."""
        from app.ai_service import _select_provider, AiProvider
        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            mock_settings.azure_openai_api_key = ""
            mock_settings.azure_openai_endpoint = ""
            mock_settings.anthropic_api_key = "sk-ant-test"
            mock_settings.mistral_api_key = ""
            result = _select_provider("standard")
        assert result == AiProvider.ANTHROPIC

    def test_select_provider_complex_prefers_anthropic(self):
        """Complex tasks should prefer Anthropic even if OpenAI is set."""
        from app.ai_service import _select_provider, AiProvider
        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test"
            mock_settings.anthropic_api_key = "sk-ant-test"
            result = _select_provider("complex")
        assert result == AiProvider.ANTHROPIC

    def test_categorize_invoice_openai_returns_dict(self):
        """categorize_invoice with OpenAI mock should return skr03_account + category."""
        from app.ai_service import categorize_invoice, AiProvider
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"skr03_account": "4964", "category": "IT/Software"}'
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        with patch("app.ai_service._get_sync_openai_client", return_value=mock_client), \
             patch("app.ai_service._get_openai_model", return_value="gpt-4o-mini"):
            result = categorize_invoice("AWS", "Cloud Hosting", 250.0, AiProvider.OPENAI)
        assert result["skr03_account"] == "4964"
        assert result["category"] == "IT/Software"

    def test_categorize_invoice_fallback_on_error(self):
        """On provider failure, should return default fallback dict."""
        from app.ai_service import categorize_invoice, AiProvider
        with patch("app.ai_service._call_openai", side_effect=Exception("API Error")), \
             patch("app.ai_service._call_ollama", side_effect=Exception("Ollama Error")):
            result = categorize_invoice("Test", "Test", 100.0, AiProvider.OPENAI)
        assert "skr03_account" in result
        assert "category" in result
