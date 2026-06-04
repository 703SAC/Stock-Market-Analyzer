"""LLM adapter entrypoint (backward compatible re-export)."""

from services.llm.base import LlmProvider, get_llm_provider, llm_adapter

__all__ = ["LlmProvider", "get_llm_provider", "llm_adapter"]
