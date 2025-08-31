"""
SMEFlow configuration management.
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """
    
    # Application
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://smeflow:smeflow123@localhost:5432/smeflow"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    
    # Redis Cache Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Authentication
    KEYCLOAK_URL: str = Field(
        default="http://localhost:8080",
        description="Keycloak server URL"
    )
    KEYCLOAK_REALM: str = Field(default="smeflow", description="Keycloak realm")
    KEYCLOAK_CLIENT_ID: str = Field(default="smeflow-api", description="Keycloak client ID")
    KEYCLOAK_CLIENT_SECRET: Optional[str] = Field(
        default=None, description="Keycloak client secret"
    )
    
    # JWT
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=30, description="JWT expiration in minutes")
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API key")
    
    # Observability
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None, description="Langfuse secret key")
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None, description="Langfuse public key")
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse host URL"
    )
    
    # Voice Communication
    LIVEKIT_API_KEY: Optional[str] = Field(default=None, description="LiveKit API key")
    LIVEKIT_API_SECRET: Optional[str] = Field(default=None, description="LiveKit API secret")
    LIVEKIT_WS_URL: str = Field(
        default="ws://localhost:7880",
        description="LiveKit WebSocket URL"
    )
    
    # African Market Integrations
    MPESA_CONSUMER_KEY: Optional[str] = Field(default=None, description="M-Pesa consumer key")
    MPESA_CONSUMER_SECRET: Optional[str] = Field(default=None, description="M-Pesa consumer secret")
    PAYSTACK_SECRET_KEY: Optional[str] = Field(default=None, description="Paystack secret key")
    JUMIA_API_KEY: Optional[str] = Field(default=None, description="Jumia API key")
    
    # Multi-tenancy
    DEFAULT_TENANT_REGION: str = Field(default="NG", description="Default tenant region")
    MAX_TENANTS_PER_INSTANCE: int = Field(
        default=10, description="Maximum tenants per monolith instance"
    )
    
    # Performance
    CACHE_TTL_SECONDS: int = Field(default=300, description="Default cache TTL in seconds")
    LLM_CACHE_TTL_SECONDS: int = Field(
        default=3600, description="LLM response cache TTL in seconds"
    )
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100, description="Maximum concurrent requests"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
