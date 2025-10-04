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
    keycloak_admin_username: str = Field(default="admin", env="KEYCLOAK_ADMIN_USERNAME")
    keycloak_admin_password: str = Field(default="admin_password", env="KEYCLOAK_ADMIN_PASSWORD")
    
    # Cerbos Configuration
    cerbos_host: str = Field(default="localhost", env="CERBOS_HOST")
    cerbos_port: int = Field(default=3593, env="CERBOS_PORT")
    
    # Domain Configuration
    DOMAIN: str = Field(default="localhost", description="Application domain")
    
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
    
    # N8n Integration Settings
    N8N_BASE_URL: Optional[str] = Field(default="http://localhost:5678", description="N8n instance URL")
    N8N_API_KEY: Optional[str] = Field(default=None, description="N8n API key")
    N8N_TIMEOUT: Optional[int] = Field(default=30, description="N8n request timeout")
    N8N_MAX_RETRIES: Optional[int] = Field(default=3, description="N8n max retry attempts")
    N8N_TENANT_PREFIX: Optional[str] = Field(default="smeflow", description="N8n tenant prefix")
    
    # Credential Management
    CREDENTIAL_ENCRYPTION_KEY: Optional[str] = Field(
        default=None, 
        description="Encryption key for n8N credentials (32 bytes base64)"
    )
    
    # API Security Settings
    RATE_LIMIT_PER_MINUTE: Optional[int] = Field(default=60, description="Rate limit per minute")
    RATE_LIMIT_PER_HOUR: Optional[int] = Field(default=1000, description="Rate limit per hour")
    RATE_LIMIT_BURST: Optional[int] = Field(default=10, description="Burst rate limit")
    RATE_LIMIT_BLOCK_DURATION: Optional[int] = Field(default=15, description="Block duration in minutes")
    CORS_ORIGINS: Optional[str] = Field(default=None, description="Comma-separated CORS origins")
    ENABLE_SECURITY_HEADERS: Optional[bool] = Field(default=True, description="Enable security headers")
    HSTS_MAX_AGE: Optional[int] = Field(default=31536000, description="HSTS max age in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
