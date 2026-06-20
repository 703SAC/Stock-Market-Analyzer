"""Role-based LLM model selection."""

from __future__ import annotations

from typing import Literal

from config import get_settings

LlmRole = Literal["flash", "pro", "formatter", "rerank"]

OPENROUTER_DEFAULTS: dict[LlmRole, str] = {
    "flash": "meta-llama/llama-3.2-3b-instruct:free",
    "pro": "meta-llama/llama-3.3-70b-instruct:free",
    "formatter": "qwen/qwen3-coder-480b-a35b:free",
    "rerank": "nvidia/llama-nemotron-rerank-vl-1b-v2:free",
}


def normalize_role(role: str | None = None) -> LlmRole:
    value = (role or get_settings().llm_default_role or "flash").lower().strip()
    if value in {"flash", "pro", "formatter", "rerank"}:
        return value  # type: ignore[return-value]
    return "flash"


def model_for_role(role: LlmRole, provider: str | None = None, settings=None) -> str:
    settings = settings or get_settings()
    provider = (provider or settings.llm_provider or "openai").lower().strip()

    if provider == "openrouter":
        configured = {
            "flash": settings.llm_flash_model,
            "pro": settings.llm_pro_model,
            "formatter": settings.llm_formatter_model,
            "rerank": settings.llm_rerank_model,
        }[role]
        return configured.strip() if configured and configured.strip() else OPENROUTER_DEFAULTS[role]

    if provider in {"google", "anthropic"}:
        if role in {"pro", "formatter"}:
            return settings.llm_advanced_model_resolved
        return settings.llm_model_resolved

    return settings.llm_model_resolved


def role_model_map(provider: str | None = None) -> dict[LlmRole, str]:
    return {role: model_for_role(role, provider) for role in ("flash", "pro", "formatter", "rerank")}
