"""
Dynamic theme engine for SMEFlow white-label UI system.

This module provides the core theme generation and management capabilities
for multi-tenant branding with African market optimizations.
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field
import redis
from jinja2 import Template

from .branding_models import BrandingConfiguration, ColorPalette, TypographyConfig
from ..core.config import get_settings
from ..database.connection import get_db_session


class CompiledTheme(BaseModel):
    """Compiled theme with all generated assets."""
    
    css_variables: str = Field(description="Generated CSS custom properties")
    custom_css: Optional[str] = Field(None, description="Custom CSS overrides")
    component_styles: str = Field(description="Generated component styles")
    assets: Dict[str, str] = Field(description="Asset URLs and metadata")
    fonts: List[str] = Field(description="Font URLs to preload")
    cache_key: str = Field(description="Cache key for theme")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ThemeConfig(BaseModel):
    """Theme configuration for generation."""
    
    tenant_id: UUID
    branding: BrandingConfiguration
    cache_duration: int = Field(default=3600, description="Cache duration in seconds")
    cdn_base_url: str = Field(description="CDN base URL for assets")
    enable_optimization: bool = Field(default=True, description="Enable CSS optimization")


class ThemeEngine:
    """
    Dynamic theme engine for generating tenant-specific themes.
    
    Handles CSS generation, asset processing, caching, and optimization
    for multi-tenant white-label UI system.
    """
    
    def __init__(self):
        """Initialize theme engine with Redis cache and templates."""
        self.settings = get_settings()
        self.redis_client = redis.Redis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            db=self.settings.redis_db,
            decode_responses=True
        )
        self.cache_prefix = "theme:"
        self.template_dir = Path(__file__).parent / "templates"
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load CSS and component templates."""
        self.css_template = Template("""
/* SMEFlow Dynamic Theme - Generated {{ generated_at }} */
:root {
  /* Primary Colors */
  --color-primary-main: {{ colors.primary.main }};
  --color-primary-light: {{ colors.primary.light }};
  --color-primary-dark: {{ colors.primary.dark }};
  --color-primary-contrast: {{ colors.primary.contrast }};
  
  /* Secondary Colors */
  --color-secondary-main: {{ colors.secondary.main }};
  --color-secondary-light: {{ colors.secondary.light }};
  --color-secondary-dark: {{ colors.secondary.dark }};
  --color-secondary-contrast: {{ colors.secondary.contrast }};
  
  /* Background Colors */
  --color-background-default: {{ colors.background.default }};
  --color-background-paper: {{ colors.background.paper }};
  --color-background-elevated: {{ colors.background.elevated }};
  
  /* Text Colors */
  --color-text-primary: {{ colors.text.primary }};
  --color-text-secondary: {{ colors.text.secondary }};
  --color-text-disabled: {{ colors.text.disabled }};
  --color-text-hint: {{ colors.text.hint }};
  
  /* Status Colors */
  --color-success: {{ colors.status.success }};
  --color-warning: {{ colors.status.warning }};
  --color-error: {{ colors.status.error }};
  --color-info: {{ colors.status.info }};
  
  /* Typography */
  --font-family-primary: {{ typography.font_family.primary }};
  --font-family-secondary: {{ typography.font_family.secondary }};
  --font-family-monospace: {{ typography.font_family.monospace }};
  
  /* Font Sizes */
  --font-size-xs: {{ typography.font_sizes.xs }};
  --font-size-sm: {{ typography.font_sizes.sm }};
  --font-size-base: {{ typography.font_sizes.base }};
  --font-size-lg: {{ typography.font_sizes.lg }};
  --font-size-xl: {{ typography.font_sizes.xl }};
  --font-size-2xl: {{ typography.font_sizes['2xl'] }};
  --font-size-3xl: {{ typography.font_sizes['3xl'] }};
  --font-size-4xl: {{ typography.font_sizes['4xl'] }};
  
  /* Font Weights */
  --font-weight-light: {{ typography.font_weights.light }};
  --font-weight-normal: {{ typography.font_weights.normal }};
  --font-weight-medium: {{ typography.font_weights.medium }};
  --font-weight-semibold: {{ typography.font_weights.semibold }};
  --font-weight-bold: {{ typography.font_weights.bold }};
  
  /* Line Heights */
  --line-height-tight: {{ typography.line_heights.tight }};
  --line-height-normal: {{ typography.line_heights.normal }};
  --line-height-relaxed: {{ typography.line_heights.relaxed }};
  
  /* Layout */
  --header-height: {{ layout.header.height }}px;
  --sidebar-width: {{ layout.sidebar.width }}px;
  --content-max-width: {{ layout.content.max_width }}px;
  --content-padding: {{ layout.content.padding }}px;
  --border-radius-base: {{ layout.border_radius }}px;
  --spacing-unit: {{ layout.spacing_unit }}px;
  
  /* African Market Optimizations */
  --region: '{{ region }}';
  --language: '{{ language_code }}';
  --currency: '{{ currency_code }}';
}

/* Base Styles */
body {
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
  background-color: var(--color-background-default);
  margin: 0;
  padding: 0;
}

/* Header Styles */
.smeflow-header {
  height: var(--header-height);
  background-color: var(--color-background-paper);
  border-bottom: 1px solid var(--color-primary-light);
  position: {{ layout.header.position }};
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-unit);
}

.smeflow-header .logo {
  height: calc(var(--header-height) - 16px);
  width: auto;
  max-width: 200px;
}

/* Sidebar Styles */
.smeflow-sidebar {
  width: var(--sidebar-width);
  background-color: var(--color-background-paper);
  border-right: 1px solid var(--color-primary-light);
  position: fixed;
  top: var(--header-height);
  left: 0;
  bottom: 0;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.smeflow-sidebar.collapsed {
  transform: translateX(-100%);
}

/* Content Area */
.smeflow-content {
  margin-left: var(--sidebar-width);
  margin-top: var(--header-height);
  padding: var(--content-padding);
  max-width: var(--content-max-width);
  background-color: var(--color-background-default);
  min-height: calc(100vh - var(--header-height));
}

/* Button Styles */
.btn-primary {
  background-color: var(--color-primary-main);
  border: 1px solid var(--color-primary-main);
  color: var(--color-primary-contrast);
  padding: calc(var(--spacing-unit) * 1.5) calc(var(--spacing-unit) * 3);
  border-radius: var(--border-radius-base);
  font-family: var(--font-family-primary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.btn-secondary {
  background-color: var(--color-secondary-main);
  border: 1px solid var(--color-secondary-main);
  color: var(--color-secondary-contrast);
  padding: calc(var(--spacing-unit) * 1.5) calc(var(--spacing-unit) * 3);
  border-radius: var(--border-radius-base);
  font-family: var(--font-family-primary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-secondary:hover {
  background-color: var(--color-secondary-dark);
  border-color: var(--color-secondary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Form Styles */
.form-input {
  width: 100%;
  padding: calc(var(--spacing-unit) * 1.5);
  border: 1px solid var(--color-text-disabled);
  border-radius: var(--border-radius-base);
  font-family: var(--font-family-primary);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background-color: var(--color-background-paper);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary-main);
  box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: calc(var(--spacing-unit) / 2);
}

/* Card Styles */
.card {
  background-color: var(--color-background-paper);
  border-radius: calc(var(--border-radius-base) * 2);
  padding: calc(var(--spacing-unit) * 3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

/* Status Indicators */
.status-success {
  color: var(--color-success);
  background-color: rgba(76, 175, 80, 0.1);
  padding: calc(var(--spacing-unit) / 2) var(--spacing-unit);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-warning {
  color: var(--color-warning);
  background-color: rgba(255, 152, 0, 0.1);
  padding: calc(var(--spacing-unit) / 2) var(--spacing-unit);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-error {
  color: var(--color-error);
  background-color: rgba(244, 67, 54, 0.1);
  padding: calc(var(--spacing-unit) / 2) var(--spacing-unit);
  border-radius: var(--border-radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

/* African Market Responsive Design */
@media (max-width: 768px) {
  .smeflow-sidebar {
    transform: translateX(-100%);
  }
  
  .smeflow-content {
    margin-left: 0;
    padding: var(--spacing-unit);
  }
  
  .smeflow-header {
    padding: 0 var(--spacing-unit);
  }
}

/* RTL Support for Arabic */
[dir="rtl"] .smeflow-sidebar {
  left: auto;
  right: 0;
  border-right: none;
  border-left: 1px solid var(--color-primary-light);
}

[dir="rtl"] .smeflow-content {
  margin-left: 0;
  margin-right: var(--sidebar-width);
}

/* High Contrast Mode */
@media (prefers-contrast: high) {
  :root {
    --color-primary-main: #000000;
    --color-text-primary: #000000;
    --color-background-default: #ffffff;
    --color-background-paper: #ffffff;
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
""")
    
    async def generate_theme(self, config: ThemeConfig) -> CompiledTheme:
        """
        Generate a complete theme for a tenant.
        
        Args:
            config: Theme configuration with branding settings
            
        Returns:
            CompiledTheme: Generated theme with CSS and assets
        """
        # Check cache first
        cache_key = self._generate_cache_key(config)
        cached_theme = await self._get_cached_theme(cache_key)
        if cached_theme:
            return cached_theme
        
        # Generate CSS variables and styles
        css_variables = self._generate_css_variables(config.branding)
        component_styles = self._generate_component_styles(config.branding)
        
        # Process assets
        assets = await self._process_theme_assets(config)
        
        # Load fonts
        fonts = self._extract_font_urls(config.branding.typography)
        
        # Compile theme
        compiled_theme = CompiledTheme(
            css_variables=css_variables,
            custom_css=config.branding.custom_css,
            component_styles=component_styles,
            assets=assets,
            fonts=fonts,
            cache_key=cache_key,
            generated_at=datetime.utcnow()
        )
        
        # Cache the compiled theme
        await self._cache_theme(cache_key, compiled_theme, config.cache_duration)
        
        return compiled_theme
    
    def _generate_css_variables(self, branding: BrandingConfiguration) -> str:
        """Generate CSS custom properties from branding configuration."""
        return self.css_template.render(
            colors=branding.colors.dict(),
            typography=branding.typography.dict(),
            layout=branding.layout.dict(),
            region=branding.region,
            language_code=branding.language_code,
            currency_code=branding.currency_code,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _generate_component_styles(self, branding: BrandingConfiguration) -> str:
        """Generate component-specific styles."""
        # This would include Flowise node styling, form components, etc.
        flowise_styles = f"""
/* Flowise Node Styling */
.react-flow__node {{
  background-color: {branding.colors.background['paper']};
  border: 2px solid {branding.colors.primary['light']};
  border-radius: {branding.layout.border_radius}px;
  font-family: {branding.typography.font_family['primary']};
  color: {branding.colors.text['primary']};
}}

.react-flow__node.selected {{
  border-color: {branding.colors.primary['main']};
  box-shadow: 0 0 0 3px {branding.colors.primary['main']}33;
}}

.react-flow__edge-path {{
  stroke: {branding.colors.primary['main']};
  stroke-width: 2;
}}

/* SMEFlow Agent Nodes */
.node-category-agents {{
  background-color: {branding.colors.primary['light']}33;
  border-color: {branding.colors.primary['main']};
}}

.node-category-african-integrations {{
  background-color: {branding.colors.secondary['light']}33;
  border-color: {branding.colors.secondary['main']};
}}

.node-category-compliance {{
  background-color: {branding.colors.status['info']}33;
  border-color: {branding.colors.status['info']};
}}
"""
        return flowise_styles
    
    async def _process_theme_assets(self, config: ThemeConfig) -> Dict[str, str]:
        """Process and return theme assets."""
        assets = {}
        
        # Logo assets
        if config.branding.logo.primary:
            assets["logo_primary"] = config.branding.logo.primary.get("url", "")
        
        if config.branding.logo.secondary:
            assets["logo_secondary"] = config.branding.logo.secondary.get("url", "")
        
        if config.branding.logo.favicon:
            assets["favicon"] = config.branding.logo.favicon.get("url", "")
        
        # Add CDN URLs if available
        for key, url in assets.items():
            if url and not url.startswith("http"):
                assets[key] = f"{config.cdn_base_url}/{url}"
        
        return assets
    
    def _extract_font_urls(self, typography: TypographyConfig) -> List[str]:
        """Extract font URLs for preloading."""
        fonts = []
        
        # Google Fonts detection
        for font_family in typography.font_family.values():
            if "googleapis.com" in font_family:
                fonts.append(font_family)
        
        return fonts
    
    def _generate_cache_key(self, config: ThemeConfig) -> str:
        """Generate cache key for theme configuration."""
        content = f"{config.tenant_id}:{config.branding.version}:{config.branding.updated_at}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _get_cached_theme(self, cache_key: str) -> Optional[CompiledTheme]:
        """Get cached theme if available."""
        try:
            cached_data = self.redis_client.get(f"{self.cache_prefix}{cache_key}")
            if cached_data:
                return CompiledTheme.parse_raw(cached_data)
        except Exception:
            # Cache miss or error, continue with generation
            pass
        return None
    
    async def _cache_theme(self, cache_key: str, theme: CompiledTheme, duration: int) -> None:
        """Cache compiled theme."""
        try:
            self.redis_client.setex(
                f"{self.cache_prefix}{cache_key}",
                duration,
                theme.json()
            )
        except Exception:
            # Cache error, continue without caching
            pass
    
    async def invalidate_theme_cache(self, tenant_id: UUID) -> None:
        """Invalidate all cached themes for a tenant."""
        try:
            pattern = f"{self.cache_prefix}*{tenant_id}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception:
            # Cache error, continue
            pass
    
    async def get_theme_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get theme performance metrics."""
        # This would integrate with monitoring system
        return {
            "cache_hit_rate": 0.85,
            "average_load_time": 120,  # milliseconds
            "css_size": 45000,  # bytes
            "asset_count": 3,
            "last_generated": datetime.utcnow().isoformat()
        }
