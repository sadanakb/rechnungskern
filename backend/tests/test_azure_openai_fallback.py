"""Tests für Azure OpenAI Fallback-Logik (DSGVO-Compliance)."""
import pytest
from unittest.mock import patch, MagicMock


class TestAzureOpenAIFallback:
    """Testet _get_client() in stage2 und _get_sync_openai_client() in ai_service."""

    def setup_method(self):
        """Reset lazy-init client cache vor jedem Test."""
        import app.ocr.stage2_llm_text as s2
        s2._client = None

    def test_azure_key_creates_azure_client(self):
        """Wenn AZURE_OPENAI_API_KEY + ENDPOINT gesetzt → AzureOpenAI Client."""
        import app.ocr.stage2_llm_text as s2

        with patch("app.ocr.stage2_llm_text.settings") as mock_settings:
            mock_settings.azure_openai_api_key = "azure-test-key"
            mock_settings.azure_openai_endpoint = "https://myresource.openai.azure.com/"
            mock_settings.azure_openai_api_version = "2024-10-21"
            mock_settings.openai_api_key = ""

            mock_azure_client = MagicMock()
            with patch("openai.AsyncAzureOpenAI", return_value=mock_azure_client) as MockAzure:
                s2._client = None
                client = s2._get_client()
                MockAzure.assert_called_once_with(
                    api_key="azure-test-key",
                    api_version="2024-10-21",
                    azure_endpoint="https://myresource.openai.azure.com/",
                )
                assert client is mock_azure_client

    def test_openai_key_only_creates_openai_client(self):
        """Wenn nur OPENAI_API_KEY gesetzt (kein Azure) → OpenAI direkter Client."""
        import app.ocr.stage2_llm_text as s2

        with patch("app.ocr.stage2_llm_text.settings") as mock_settings:
            mock_settings.azure_openai_api_key = ""
            mock_settings.azure_openai_endpoint = ""
            mock_settings.openai_api_key = "sk-direct-fallback"

            mock_openai_client = MagicMock()
            with patch("openai.AsyncOpenAI", return_value=mock_openai_client) as MockOpenAI:
                s2._client = None
                client = s2._get_client()
                MockOpenAI.assert_called_once_with(api_key="sk-direct-fallback")
                assert client is mock_openai_client

    def test_no_key_returns_none(self):
        """Wenn kein API Key konfiguriert → None zurückgeben (kein Crash)."""
        import app.ocr.stage2_llm_text as s2

        with patch("app.ocr.stage2_llm_text.settings") as mock_settings:
            mock_settings.azure_openai_api_key = ""
            mock_settings.azure_openai_endpoint = ""
            mock_settings.openai_api_key = ""

            s2._client = None
            client = s2._get_client()
            assert client is None

    def test_get_sync_client_prefers_azure(self):
        """ai_service._get_sync_openai_client nutzt Azure wenn Key gesetzt."""
        from app.ai_service import _get_sync_openai_client

        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.azure_openai_api_key = "azure-key"
            mock_settings.azure_openai_endpoint = "https://x.openai.azure.com/"
            mock_settings.azure_openai_api_version = "2024-10-21"
            mock_settings.openai_api_key = "sk-also-set"

            mock_client = MagicMock()
            with patch("openai.AzureOpenAI", return_value=mock_client) as MockAzure:
                client = _get_sync_openai_client()
                assert MockAzure.called
                assert client is mock_client

    def test_get_sync_client_falls_back_to_openai_direct(self):
        """ai_service._get_sync_openai_client fällt auf OpenAI direkt zurück."""
        from app.ai_service import _get_sync_openai_client

        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.azure_openai_api_key = ""
            mock_settings.azure_openai_endpoint = ""
            mock_settings.openai_api_key = "sk-fallback"

            mock_client = MagicMock()
            with patch("openai.OpenAI", return_value=mock_client) as MockOpenAI:
                client = _get_sync_openai_client()
                MockOpenAI.assert_called_once_with(api_key="sk-fallback")
                assert client is mock_client

    def test_get_sync_client_raises_without_keys(self):
        """ai_service._get_sync_openai_client wirft ValueError wenn kein Key."""
        from app.ai_service import _get_sync_openai_client

        with patch("app.ai_service.settings") as mock_settings:
            mock_settings.azure_openai_api_key = ""
            mock_settings.azure_openai_endpoint = ""
            mock_settings.openai_api_key = ""

            with pytest.raises(ValueError, match="Kein OpenAI/Azure-API-Key"):
                _get_sync_openai_client()
