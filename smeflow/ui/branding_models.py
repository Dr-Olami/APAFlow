"""
Branding configuration models for SMEFlow white-label UI system.

This module defines the data models for tenant branding configurations,
including colors, typography, logos, and layout customizations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ..database.connection import Base


class ColorPalette(BaseModel):
    """Color palette configuration for tenant branding."""
    
    primary: Dict[str, str] = Field(
        description="Primary brand colors",
        example={
            "main": "#1976d2",
            "light": "#42a5f5", 
            "dark": "#1565c0",
            "contrast": "#ffffff"
        }
    )
    secondary: Dict[str, str] = Field(
        description="Secondary/accent colors",
        example={
            "main": "#dc004e",
            "light": "#ff5983",
            "dark": "#9a0036",
            "contrast": "#ffffff"
        }
    )
    background: Dict[str, str] = Field(
        description="Background colors",
        example={
            "default": "#fafafa",
            "paper": "#ffffff",
            "elevated": "#ffffff"
        }
    )
    text: Dict[str, str] = Field(
        description="Text colors",
        example={
            "primary": "#212121",
            "secondary": "#757575",
            "disabled": "#bdbdbd",
            "hint": "#9e9e9e"
        }
    )
    status: Dict[str, str] = Field(
        description="Status indicator colors",
        example={
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3"
        }
    )

    @validator('primary', 'secondary', 'background', 'text', 'status')
    def validate_hex_colors(cls, v):
        """Validate that color values are valid hex codes."""
        for key, color in v.items():
            if not color.startswith('#') or len(color) not in [4, 7]:
                raise ValueError(f"Invalid hex color '{color}' for key '{key}'")
        return v


class TypographyConfig(BaseModel):
    """Typography configuration for tenant branding."""
    
    font_family: Dict[str, str] = Field(
        description="Font family definitions",
        example={
            "primary": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            "secondary": "Roboto, Arial, sans-serif",
            "monospace": "Fira Code, Consolas, monospace"
        }
    )
    font_sizes: Dict[str, str] = Field(
        description="Font size scale",
        example={
            "xs": "0.75rem",
            "sm": "0.875rem", 
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem"
        }
    )
    font_weights: Dict[str, int] = Field(
        description="Font weight scale",
        example={
            "light": 300,
            "normal": 400,
            "medium": 500,
            "semibold": 600,
            "bold": 700
        }
    )
    line_heights: Dict[str, float] = Field(
        description="Line height scale",
        example={
            "tight": 1.25,
            "normal": 1.5,
            "relaxed": 1.75
        }
    )


class LogoConfiguration(BaseModel):
    """Logo configuration for tenant branding."""
    
    primary: Dict[str, Any] = Field(
        description="Primary logo configuration",
        example={
            "url": "https://cdn.smeflow.com/tenant123/logo-primary.png",
            "width": 200,
            "height": 60,
            "alt_text": "Company Logo"
        }
    )
    secondary: Optional[Dict[str, Any]] = Field(
        None,
        description="Secondary logo (light/dark variant)",
        example={
            "url": "https://cdn.smeflow.com/tenant123/logo-secondary.png",
            "width": 200,
            "height": 60,
            "alt_text": "Company Logo Light"
        }
    )
    favicon: Dict[str, Any] = Field(
        description="Favicon configuration",
        example={
            "url": "https://cdn.smeflow.com/tenant123/favicon.ico",
            "type": "ico"
        }
    )
    loading_logo: Optional[Dict[str, Any]] = Field(
        None,
        description="Loading screen logo",
        example={
            "url": "https://cdn.smeflow.com/tenant123/loading-logo.png",
            "animation": "pulse"
        }
    )


class LayoutConfig(BaseModel):
    """Layout configuration for tenant branding."""
    
    header: Dict[str, Any] = Field(
        description="Header configuration",
        example={
            "height": 64,
            "position": "fixed",
            "show_logo": True,
            "show_search": True,
            "show_notifications": True,
            "show_user_menu": True
        }
    )
    sidebar: Dict[str, Any] = Field(
        description="Sidebar configuration", 
        example={
            "width": 280,
            "collapsible": True,
            "default_collapsed": False,
            "position": "left",
            "show_icons": True
        }
    )
    content: Dict[str, Any] = Field(
        description="Content area configuration",
        example={
            "max_width": 1200,
            "padding": 24,
            "background_color": "#fafafa"
        }
    )
    footer: Dict[str, Any] = Field(
        description="Footer configuration",
        example={
            "show": True,
            "height": 48,
            "content": "© 2025 SMEFlow. All rights reserved."
        }
    )
    border_radius: int = Field(8, description="Base border radius in pixels")
    spacing_unit: int = Field(8, description="Base spacing unit in pixels")


class BrandingConfiguration(BaseModel):
    """Complete branding configuration for a tenant."""
    
    tenant_id: UUID = Field(description="Tenant identifier")
    name: str = Field(description="Configuration name", max_length=255)
    version: str = Field(default="1.0.0", description="Configuration version")
    
    colors: ColorPalette = Field(description="Color palette configuration")
    typography: TypographyConfig = Field(description="Typography configuration")
    logo: LogoConfiguration = Field(description="Logo configuration")
    layout: LayoutConfig = Field(description="Layout configuration")
    
    custom_css: Optional[str] = Field(None, description="Custom CSS overrides")
    is_active: bool = Field(True, description="Whether configuration is active")
    
    # African market optimizations
    region: str = Field(description="Target region (NG, KE, ZA, etc.)")
    language_code: str = Field(default="en", description="Primary language code")
    currency_code: str = Field(description="Primary currency (NGN, KES, ZAR, etc.)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class TenantBranding(Base):
    """Database model for tenant branding configurations."""
    
    __tablename__ = "tenant_branding"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # Branding configuration stored as JSON
    colors = Column(JSON, nullable=False)
    typography = Column(JSON, nullable=False)
    logo = Column(JSON, nullable=False)
    layout = Column(JSON, nullable=False)
    
    custom_css = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # African market fields
    region = Column(String(10), nullable=False)
    language_code = Column(String(10), nullable=False, default="en")
    currency_code = Column(String(10), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_pydantic(self) -> BrandingConfiguration:
        """Convert database model to Pydantic model."""
        return BrandingConfiguration(
            tenant_id=self.tenant_id,
            name=self.name,
            version=self.version,
            colors=ColorPalette(**self.colors),
            typography=TypographyConfig(**self.typography),
            logo=LogoConfiguration(**self.logo),
            layout=LayoutConfig(**self.layout),
            custom_css=self.custom_css,
            is_active=self.is_active,
            region=self.region,
            language_code=self.language_code,
            currency_code=self.currency_code,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class ThemeAsset(Base):
    """Database model for theme assets (logos, images, fonts)."""
    
    __tablename__ = "theme_assets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    branding_id = Column(PGUUID(as_uuid=True), nullable=False)
    
    asset_type = Column(String(50), nullable=False)  # logo, font, image, etc.
    asset_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    
    # Asset URLs and metadata
    url = Column(String(500), nullable=False)
    cdn_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Image-specific metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Processing metadata
    variants = Column(JSON, nullable=True)  # Different sizes/formats
    optimized_formats = Column(JSON, nullable=True)  # WebP, AVIF versions
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CustomDomain(Base):
    """Database model for custom domain configurations."""
    
    __tablename__ = "custom_domains"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    domain = Column(String(255), nullable=False, unique=True)
    subdomain = Column(String(100), nullable=True)
    
    # SSL configuration
    ssl_provider = Column(String(50), nullable=False, default="letsencrypt")
    ssl_auto_renew = Column(Boolean, default=True, nullable=False)
    ssl_certificate = Column(Text, nullable=True)
    ssl_private_key = Column(Text, nullable=True)
    
    # Verification
    verification_method = Column(String(20), nullable=False, default="dns")
    verification_token = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    # DNS records for setup
    dns_records = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
