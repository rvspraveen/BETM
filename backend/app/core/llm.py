"""
LLM Factory — returns the right LangChain chat model based on LLM_PROVIDER env var.

Usage:
    from app.core.llm import get_llm, get_embeddings
    llm = get_llm()
    embeddings = get_embeddings()

Switch provider:  LLM_PROVIDER=anthropic in .env
"""
from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import settings
import structlog

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_openai import OpenAIEmbeddings

log = structlog.get_logger()


@lru_cache(maxsize=1)
def get_llm() -> "BaseChatModel":
    """Return cached LLM instance. Thread-safe via lru_cache."""
    provider = settings.LLM_PROVIDER

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        log.info("llm.factory", provider="openai", model=settings.OPENAI_MODEL)
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            streaming=True,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        log.info("llm.factory", provider="anthropic", model=settings.ANTHROPIC_MODEL)
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            streaming=True,
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'openai' or 'anthropic'.")


@lru_cache(maxsize=1)
def get_embeddings() -> "OpenAIEmbeddings":
    """Always use OpenAI embeddings (best quality, consistent vector space)."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )
