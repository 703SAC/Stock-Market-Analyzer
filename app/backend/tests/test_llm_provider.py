"""LLM provider factory and parsing tests."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.llm.schemas import NewsPriceReportJson


def test_news_price_report_json_validation():
    data = {
        "summary": "테스트 요약",
        "key_points": ["포인트1"],
        "possible_reasons": ["이유1"],
        "risks": ["주의1"],
        "confidence": "MEDIUM",
    }
    report = NewsPriceReportJson.model_validate(data)
    assert report.summary == "테스트 요약"
    assert report.confidence == "MEDIUM"


@patch("services.llm.base.get_settings")
def test_get_llm_provider_openai(mock_settings):
    mock_settings.return_value = MagicMock(llm_provider="openai")
    from services.llm.base import get_llm_provider
    from services.llm.openai_provider import OpenAiLlmProvider

    provider = get_llm_provider()
    assert isinstance(provider, OpenAiLlmProvider)
    assert provider.provider_name == "openai"


@patch("services.llm.base.get_settings")
def test_get_llm_provider_google(mock_settings):
    mock_settings.return_value = MagicMock(llm_provider="google")
    from services.llm.base import get_llm_provider
    from services.llm.google_provider import GoogleLlmProvider

    provider = get_llm_provider()
    assert isinstance(provider, GoogleLlmProvider)
    assert provider.provider_name == "google"


@patch("services.llm.openrouter_provider.get_settings")
@patch("services.llm.base.get_settings")
def test_get_llm_provider_openrouter_role(mock_base_settings, mock_or_settings):
    settings = MagicMock(
        llm_provider="openrouter",
        llm_default_role="flash",
        llm_flash_model="flash-model",
        llm_pro_model="pro-model",
        llm_formatter_model="formatter-model",
        llm_rerank_model="rerank-model",
        openrouter_api_key="test-key",
        openrouter_base_url="https://openrouter.ai/api/v1",
    )
    mock_base_settings.return_value = settings
    mock_or_settings.return_value = settings
    from services.llm.base import get_llm_provider
    from services.llm.openrouter_provider import OpenRouterLlmProvider

    provider = get_llm_provider("pro")
    assert isinstance(provider, OpenRouterLlmProvider)
    assert provider.provider_name == "openrouter"
    assert provider.model_name == "pro-model"
    assert provider.is_configured is True


@patch("services.llm.base.get_settings")
def test_get_llm_provider_anthropic_seat(mock_settings):
    """Legacy anthropic slot is now backed by Gemini 3.5 Flash advanced mode."""
    mock_settings.return_value = MagicMock(llm_provider="anthropic")
    from services.llm.base import get_llm_provider
    from services.llm.google_provider import GoogleAdvancedLlmProvider

    provider = get_llm_provider()
    assert isinstance(provider, GoogleAdvancedLlmProvider)
    assert provider.provider_name == "google_advanced"
    assert provider.model_name == "gemini-3.5-flash"


@patch("services.llm.base.get_settings")
def test_get_llm_provider_unsupported(mock_settings):
    mock_settings.return_value = MagicMock(llm_provider="llama")
    from services.llm.base import get_llm_provider

    with pytest.raises(ValueError, match="Unsupported"):
        get_llm_provider()


@patch("services.llm.openai_provider.get_settings")
def test_openai_not_configured_without_key(mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="",
        llm_model_resolved="gpt-4o-mini",
    )
    from services.llm.openai_provider import OpenAiLlmProvider

    provider = OpenAiLlmProvider()
    assert provider.is_configured is False


@patch("services.llm.google_provider.get_settings")
def test_google_not_configured_without_key(mock_settings):
    mock_settings.return_value = MagicMock(
        google_api_key="",
        llm_model_resolved="gemini-2.5-flash",
    )
    from services.llm.google_provider import GoogleLlmProvider

    provider = GoogleLlmProvider()
    assert provider.is_configured is False


@patch("services.llm.openai_provider.get_settings")
@pytest.mark.asyncio
async def test_openai_generate_parses_json(mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="test-key",
        llm_model_resolved="gpt-4o-mini",
    )
    payload = {
        "summary": "요약",
        "key_points": ["a"],
        "possible_reasons": ["b"],
        "risks": ["c"],
        "confidence": "LOW",
    }
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(message=MagicMock(content=json.dumps(payload, ensure_ascii=False)))
            ]
        )
    )

    from services.llm.openai_provider import OpenAiLlmProvider

    provider = OpenAiLlmProvider()
    provider._client = mock_client

    result = await provider.generate_news_price_report("sys", "user")
    assert result.summary == "요약"
    assert result.confidence == "LOW"


@patch("services.llm.google_provider.asyncio.to_thread")
@patch("services.llm.google_provider.get_settings")
@pytest.mark.asyncio
async def test_google_generate_parses_json(mock_settings, mock_to_thread):
    mock_settings.return_value = MagicMock(
        google_api_key="test-key",
        llm_model_resolved="gemini-2.5-flash",
    )
    payload = {
        "summary": "gemini 요약",
        "key_points": [],
        "possible_reasons": [],
        "risks": [],
        "confidence": "HIGH",
    }
    mock_to_thread.return_value = json.dumps(payload, ensure_ascii=False)

    from services.llm.google_provider import GoogleLlmProvider

    provider = GoogleLlmProvider()
    provider._client = MagicMock()

    result = await provider.generate_news_price_report("sys", "user")
    assert result.summary == "gemini 요약"
    assert result.confidence == "HIGH"


@patch("services.llm.openrouter_provider.get_settings")
@pytest.mark.asyncio
async def test_openrouter_generate_parses_json(mock_settings):
    mock_settings.return_value = MagicMock(
        llm_provider="openrouter",
        llm_default_role="flash",
        llm_flash_model="flash-model",
        llm_pro_model="pro-model",
        llm_formatter_model="formatter-model",
        llm_rerank_model="rerank-model",
        openrouter_api_key="test-key",
        openrouter_base_url="https://openrouter.ai/api/v1",
    )
    payload = {
        "summary": "openrouter 요약",
        "key_points": ["a"],
        "possible_reasons": [],
        "risks": [],
        "confidence": "MEDIUM",
    }
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]
    }
    client = MagicMock()
    client.post = AsyncMock(return_value=response)

    from services.llm.openrouter_provider import OpenRouterLlmProvider

    provider = OpenRouterLlmProvider(role="formatter", client=client)
    result = await provider.generate_news_price_report("sys", "user")

    assert result.summary == "openrouter 요약"
    assert result.confidence == "MEDIUM"
    request = client.post.call_args.kwargs
    assert request["json"]["model"] == "formatter-model"
    assert request["json"]["response_format"]["type"] == "json_schema"
