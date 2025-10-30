"""LLM integration for OpenAI-compatible and Ollama APIs with LangChain support."""
from typing import List, Dict, Any, Optional

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from config import settings


def get_langchain_llm(provider: str = None, **kwargs) -> BaseChatModel:
    """
    Get a LangChain LLM instance.

    Args:
        provider: 'openai' or 'ollama' (default from settings)
        **kwargs: Additional parameters for LLM initialization

    Returns:
        LangChain BaseChatModel instance
    """
    provider = provider or settings.llm_provider

    if provider == "openai":
        return ChatOpenAI(
            model=kwargs.get('model', settings.openai_chat_model),
            api_key=kwargs.get('api_key', settings.openai_api_key),
            base_url=kwargs.get('base_url', settings.openai_api_base),
            temperature=kwargs.get('temperature', settings.agent_temperature),
            max_tokens=kwargs.get('max_tokens', 1024),
            streaming=kwargs.get('streaming', False),
        )
    elif provider == "ollama":
        base_url = kwargs.get('base_url', settings.ollama_api_base)
        # Set Ollama host if needed
        if base_url and base_url != "http://localhost:11434":
            import os
            os.environ['OLLAMA_HOST'] = base_url.replace('http://', '').replace('https://', '')

        return ChatOllama(
            model=kwargs.get('model', settings.ollama_chat_model),
            base_url=base_url,
            temperature=kwargs.get('temperature', settings.agent_temperature),
            num_ctx=kwargs.get('num_ctx', 4096),
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


# Legacy compatibility classes (kept for backward compatibility)
class LLMProvider:
    """Abstract base class for LLM providers (legacy compatibility)."""

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        raise NotImplementedError("Use get_langchain_llm instead")

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from the LLM."""
        raise NotImplementedError("Use get_langchain_llm instead")


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider (legacy compatibility)."""

    def __init__(self, **kwargs):
        """Initialize OpenAI provider."""
        self.langchain_llm = get_langchain_llm(provider="openai", **kwargs)
        logger.info(f"Initialized OpenAI provider (legacy mode)")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from OpenAI."""
        try:
            # Convert messages to LangChain format
            langchain_messages = _convert_messages_to_langchain(messages)
            response = self.langchain_llm.invoke(langchain_messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from OpenAI."""
        try:
            langchain_messages = _convert_messages_to_langchain(messages)
            for chunk in self.langchain_llm.stream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama local API provider (legacy compatibility)."""

    def __init__(self, **kwargs):
        """Initialize Ollama provider."""
        self.langchain_llm = get_langchain_llm(provider="ollama", **kwargs)
        logger.info(f"Initialized Ollama provider (legacy mode)")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from Ollama."""
        try:
            langchain_messages = _convert_messages_to_langchain(messages)
            response = self.langchain_llm.invoke(langchain_messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            raise

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from Ollama."""
        try:
            langchain_messages = _convert_messages_to_langchain(messages)
            for chunk in self.langchain_llm.stream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming from Ollama: {e}")
            raise


def _convert_messages_to_langchain(messages: List[Dict[str, str]]) -> List:
    """Convert message dicts to LangChain message objects."""
    langchain_messages = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')

        if role == 'system':
            langchain_messages.append(SystemMessage(content=content))
        elif role == 'assistant':
            langchain_messages.append(AIMessage(content=content))
        else:  # user or default
            langchain_messages.append(HumanMessage(content=content))

    return langchain_messages


def get_llm_provider(provider: str = None, **kwargs) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider (legacy compatibility).

    Args:
        provider: 'openai' or 'ollama' (default from settings)
        **kwargs: Additional parameters for provider initialization

    Returns:
        LLMProvider instance
    """
    provider = provider or settings.llm_provider

    if provider == "openai":
        return OpenAIProvider(**kwargs)
    elif provider == "ollama":
        return OllamaProvider(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
