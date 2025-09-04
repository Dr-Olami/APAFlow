"""
LLM provider integrations for SMEFlow agents.

Supports multiple LLM providers with African market optimizations,
cost tracking, and multi-tenant isolation.
"""

import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    def create_llm(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """Create an LLM instance."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    def estimate_cost(self, model_name: str, tokens: int) -> float:
        """Estimate cost for token usage."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider with African market optimizations."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment variables")
        
        # Pricing per 1K tokens (as of 2024)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }
    
    def create_llm(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """
        Create OpenAI LLM instance.
        
        Args:
            model_name: OpenAI model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional model parameters
            
        Returns:
            OpenAI LLM instance
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # African market optimizations
        african_kwargs = {
            "request_timeout": 60,  # Longer timeout for slower connections
            "max_retries": 3,  # Retry for network issues
            **kwargs
        }
        
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=self.api_key,
            **african_kwargs
        )
        
        logger.info(
            f"Created OpenAI LLM: {model_name}",
            extra={
                "provider": "openai",
                "model": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        
        return llm
    
    def get_supported_models(self) -> List[str]:
        """Get supported OpenAI models."""
        return list(self.pricing.keys())
    
    def estimate_cost(self, model_name: str, tokens: int) -> float:
        """
        Estimate cost for OpenAI model usage.
        
        Args:
            model_name: Model name
            tokens: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        if model_name not in self.pricing:
            logger.warning(f"Unknown model for cost estimation: {model_name}")
            return 0.0
        
        # Assume 75% input, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        pricing = self.pricing[model_name]
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )
        
        return round(cost, 6)


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider with African market optimizations."""
    
    def __init__(self):
        """Initialize Anthropic provider."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("Anthropic API key not found in environment variables")
        
        # Pricing per 1K tokens (as of 2024)
        self.pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015}
        }
    
    def create_llm(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """
        Create Anthropic LLM instance.
        
        Args:
            model_name: Anthropic model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional model parameters
            
        Returns:
            Anthropic LLM instance
        """
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        # African market optimizations
        african_kwargs = {
            "timeout": 60,  # Longer timeout for slower connections
            "max_retries": 3,  # Retry for network issues
            **kwargs
        }
        
        llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=self.api_key,
            **african_kwargs
        )
        
        logger.info(
            f"Created Anthropic LLM: {model_name}",
            extra={
                "provider": "anthropic",
                "model": model_name,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        
        return llm
    
    def get_supported_models(self) -> List[str]:
        """Get supported Anthropic models."""
        return list(self.pricing.keys())
    
    def estimate_cost(self, model_name: str, tokens: int) -> float:
        """
        Estimate cost for Anthropic model usage.
        
        Args:
            model_name: Model name
            tokens: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        if model_name not in self.pricing:
            logger.warning(f"Unknown model for cost estimation: {model_name}")
            return 0.0
        
        # Assume 75% input, 25% output tokens
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        pricing = self.pricing[model_name]
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )
        
        return round(cost, 6)


class LLMProviderFactory:
    """Factory for creating LLM providers and instances."""
    
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> LLMProvider:
        """
        Get LLM provider instance.
        
        Args:
            provider_name: Provider name (openai, anthropic)
            
        Returns:
            LLM provider instance
        """
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
        
        return cls._providers[provider_name]()
    
    @classmethod
    def create_llm(
        cls,
        provider_name: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseLanguageModel:
        """
        Create LLM instance from provider.
        
        Args:
            provider_name: Provider name
            model_name: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            LLM instance
        """
        provider = cls.get_provider(provider_name)
        return provider.create_llm(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    @classmethod
    def get_supported_models(cls, provider_name: str) -> List[str]:
        """Get supported models for provider."""
        provider = cls.get_provider(provider_name)
        return provider.get_supported_models()
    
    @classmethod
    def estimate_cost(cls, provider_name: str, model_name: str, tokens: int) -> float:
        """Estimate cost for model usage."""
        provider = cls.get_provider(provider_name)
        return provider.estimate_cost(model_name, tokens)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers."""
        return list(cls._providers.keys())


def create_llm_for_agent(
    config: Dict[str, Any],
    tenant_id: str,
    region: str = "NG"
) -> BaseLanguageModel:
    """
    Create LLM instance optimized for African SME use cases.
    
    Args:
        config: LLM configuration
        tenant_id: Tenant identifier
        region: African region code
        
    Returns:
        Configured LLM instance
    """
    provider_name = config.get("llm_provider", "openai")
    model_name = config.get("model_name", "gpt-4o")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens")
    
    # African market optimizations based on region
    regional_optimizations = {
        "NG": {"request_timeout": 90, "max_retries": 4},  # Nigeria - variable connectivity
        "KE": {"request_timeout": 60, "max_retries": 3},  # Kenya - good connectivity
        "ZA": {"request_timeout": 45, "max_retries": 2},  # South Africa - excellent connectivity
        "GH": {"request_timeout": 75, "max_retries": 3},  # Ghana - moderate connectivity
        "UG": {"request_timeout": 90, "max_retries": 4},  # Uganda - variable connectivity
        "TZ": {"request_timeout": 75, "max_retries": 3},  # Tanzania - moderate connectivity
        "RW": {"request_timeout": 60, "max_retries": 3},  # Rwanda - good connectivity
        "ET": {"request_timeout": 90, "max_retries": 4},  # Ethiopia - variable connectivity
        "EG": {"request_timeout": 60, "max_retries": 3},  # Egypt - good connectivity
        "MA": {"request_timeout": 45, "max_retries": 2},  # Morocco - good connectivity
    }
    
    regional_config = regional_optimizations.get(region, {"request_timeout": 60, "max_retries": 3})
    
    try:
        llm = LLMProviderFactory.create_llm(
            provider_name=provider_name,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **regional_config
        )
        
        logger.info(
            f"Created LLM for tenant {tenant_id}",
            extra={
                "tenant_id": tenant_id,
                "provider": provider_name,
                "model": model_name,
                "region": region,
                "optimizations": regional_config
            }
        )
        
        return llm
        
    except Exception as e:
        logger.error(
            f"Failed to create LLM for tenant {tenant_id}: {e}",
            extra={
                "tenant_id": tenant_id,
                "provider": provider_name,
                "model": model_name,
                "error": str(e)
            }
        )
        raise
