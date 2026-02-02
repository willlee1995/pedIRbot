"""LLM integration for OpenAI-compatible and Ollama APIs."""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from openai import OpenAI
import ollama
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider."""

    def __init__(self,
                 model: str = None,
                 api_key: str = None,
                 base_url: str = None,
                 temperature: float = 0.3,
                 max_tokens: int = 1024):
        """
        Initialize OpenAI provider.

        Args:
            model: Model name (default from settings)
            api_key: API key (default from settings)
            base_url: API base URL (default from settings)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model = model or settings.openai_chat_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = OpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_api_base
        )

        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=False
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """
        Generate a streaming response from OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Yields:
            Response chunks
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama local API provider."""

    def __init__(self,
                 model: str = None,
                 base_url: str = None,
                 temperature: float = 0.1):
        """
        Initialize Ollama provider.

        Args:
            model: Model name (default from settings)
            base_url: Ollama API base URL (default from settings)
            temperature: Sampling temperature
        """
        self.model = model or settings.ollama_chat_model
        self.temperature = temperature
        self.base_url = base_url or settings.ollama_api_base

        # Set the Ollama host
        if self.base_url:
            import os
            os.environ['OLLAMA_HOST'] = self.base_url

        logger.info(f"Initialized Ollama provider with model: {self.model}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': kwargs.get('temperature', self.temperature),
                },
                stream=False
            )

            return response['message']['content']
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            raise

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """
        Generate a streaming response from Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Yields:
            Response chunks
        """
        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': kwargs.get('temperature', self.temperature),
                },
                stream=True
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except Exception as e:
            logger.error(f"Error streaming from Ollama: {e}")
            raise


class LMStudioProvider(LLMProvider):
    """LM Studio local API provider using OpenAI-compatible API."""

    def __init__(self,
                 model: str = None,
                 base_url: str = None,
                 temperature: float = 0.3,
                 max_tokens: int = 1024):
        """
        Initialize LM Studio provider.

        Args:
            model: Model name (default from settings)
            base_url: LM Studio API base URL (default from settings)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model = model or settings.lmstudio_chat_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url or settings.lmstudio_api_base

        self.client = OpenAI(
            api_key="lm-studio",  # LM Studio doesn't require real key
            base_url=self.base_url
        )

        logger.info(f"Initialized LM Studio provider with model: {self.model}")
        logger.info(f"LM Studio API base: {self.base_url}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from LM Studio.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=False
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from LM Studio: {e}")
            logger.error(f"Make sure LM Studio is running with a chat model loaded")
            raise

    def stream_generate(self, messages: List[Dict[str, str]], **kwargs):
        """
        Generate a streaming response from LM Studio.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Yields:
            Response chunks
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error streaming from LM Studio: {e}")
            raise


def get_llm_provider(provider: str = None, **kwargs) -> LLMProvider:
    """
    Factory function to get the appropriate LLM provider.

    Args:
        provider: 'openai', 'ollama', or 'lmstudio' (default from settings)
        **kwargs: Additional parameters for provider initialization

    Returns:
        LLMProvider instance
    """
    provider = provider or settings.llm_provider

    if provider == "openai":
        return OpenAIProvider(**kwargs)
    elif provider == "ollama":
        return OllamaProvider(**kwargs)
    elif provider == "lmstudio":
        return LMStudioProvider(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
