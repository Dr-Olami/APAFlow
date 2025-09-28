"""
Unit tests for SMEFlow white-label UI system.

Tests theme engine, branding models, asset processing, and localization
with comprehensive coverage for African market optimizations.
"""

import pytest
import json
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from smeflow.ui.branding_models import (
    BrandingConfiguration,
    ColorPalette,
    TypographyConfig,
    LogoConfiguration,
    LayoutConfig
)
from smeflow.ui.theme_engine import ThemeEngine, ThemeConfig, CompiledTheme
from smeflow.ui.asset_processor import AssetProcessor, ProcessedAsset, AssetValidationError
from smeflow.ui.localization import LocalizationService, Language, LocalizationConfig


class TestBrandingModels:
    """Test branding configuration models."""
    
    def test_color_palette_validation(self):
        """Test color palette validation with hex colors."""
        valid_colors = ColorPalette(
            primary={"main": "#1976d2", "light": "#42a5f5", "dark": "#1565c0", "contrast": "#ffffff"},
            secondary={"main": "#dc004e", "light": "#ff5983", "dark": "#9a0036", "contrast": "#ffffff"},
            background={"default": "#fafafa", "paper": "#ffffff", "elevated": "#ffffff"},
            text={"primary": "#212121", "secondary": "#757575", "disabled": "#bdbdbd", "hint": "#9e9e9e"},
            status={"success": "#4caf50", "warning": "#ff9800", "error": "#f44336", "info": "#2196f3"}
        )
        assert valid_colors.primary["main"] == "#1976d2"
        
        # Test invalid hex color
        with pytest.raises(ValueError):
            ColorPalette(
                primary={"main": "invalid-color", "light": "#42a5f5", "dark": "#1565c0", "contrast": "#ffffff"},
                secondary={"main": "#dc004e", "light": "#ff5983", "dark": "#9a0036", "contrast": "#ffffff"},
                background={"default": "#fafafa", "paper": "#ffffff", "elevated": "#ffffff"},
                text={"primary": "#212121", "secondary": "#757575", "disabled": "#bdbdbd", "hint": "#9e9e9e"},
                status={"success": "#4caf50", "warning": "#ff9800", "error": "#f44336", "info": "#2196f3"}
            )
    
    def test_branding_configuration_creation(self):
        """Test complete branding configuration creation."""
        tenant_id = uuid4()
        config = BrandingConfiguration(
            tenant_id=tenant_id,
            name="Test Brand",
            colors=ColorPalette(
                primary={"main": "#1976d2", "light": "#42a5f5", "dark": "#1565c0", "contrast": "#ffffff"},
                secondary={"main": "#dc004e", "light": "#ff5983", "dark": "#9a0036", "contrast": "#ffffff"},
                background={"default": "#fafafa", "paper": "#ffffff", "elevated": "#ffffff"},
                text={"primary": "#212121", "secondary": "#757575", "disabled": "#bdbdbd", "hint": "#9e9e9e"},
                status={"success": "#4caf50", "warning": "#ff9800", "error": "#f44336", "info": "#2196f3"}
            ),
            typography=TypographyConfig(
                font_family={"primary": "Inter, sans-serif", "secondary": "Roboto, sans-serif", "monospace": "Fira Code, monospace"},
                font_sizes={"xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"},
                font_weights={"light": 300, "normal": 400, "medium": 500, "semibold": 600, "bold": 700},
                line_heights={"tight": 1.25, "normal": 1.5, "relaxed": 1.75}
            ),
            logo=LogoConfiguration(
                primary={"url": "https://example.com/logo.png", "width": 200, "height": 60, "alt_text": "Logo"},
                favicon={"url": "https://example.com/favicon.ico", "type": "ico"}
            ),
            layout=LayoutConfig(
                header={"height": 64, "position": "fixed", "show_logo": True, "show_search": True, "show_notifications": True, "show_user_menu": True},
                sidebar={"width": 280, "collapsible": True, "default_collapsed": False, "position": "left", "show_icons": True},
                content={"max_width": 1200, "padding": 24, "background_color": "#fafafa"},
                footer={"show": True, "height": 48, "content": "© 2025 SMEFlow"}
            ),
            region="NG",
            currency_code="NGN"
        )
        
        assert config.tenant_id == tenant_id
        assert config.name == "Test Brand"
        assert config.region == "NG"
        assert config.currency_code == "NGN"


class TestThemeEngine:
    """Test theme engine functionality."""
    
    @pytest.fixture
    def theme_engine(self):
        """Create theme engine instance."""
        with patch('smeflow.ui.theme_engine.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                redis_host="localhost",
                redis_port=6379,
                redis_db=0
            )
            with patch('smeflow.ui.theme_engine.redis.Redis'):
                return ThemeEngine()
    
    @pytest.fixture
    def sample_branding(self):
        """Create sample branding configuration."""
        return BrandingConfiguration(
            tenant_id=uuid4(),
            name="Sample Brand",
            colors=ColorPalette(
                primary={"main": "#1976d2", "light": "#42a5f5", "dark": "#1565c0", "contrast": "#ffffff"},
                secondary={"main": "#dc004e", "light": "#ff5983", "dark": "#9a0036", "contrast": "#ffffff"},
                background={"default": "#fafafa", "paper": "#ffffff", "elevated": "#ffffff"},
                text={"primary": "#212121", "secondary": "#757575", "disabled": "#bdbdbd", "hint": "#9e9e9e"},
                status={"success": "#4caf50", "warning": "#ff9800", "error": "#f44336", "info": "#2196f3"}
            ),
            typography=TypographyConfig(
                font_family={"primary": "Inter, sans-serif", "secondary": "Roboto, sans-serif", "monospace": "Fira Code, monospace"},
                font_sizes={"xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"},
                font_weights={"light": 300, "normal": 400, "medium": 500, "semibold": 600, "bold": 700},
                line_heights={"tight": 1.25, "normal": 1.5, "relaxed": 1.75}
            ),
            logo=LogoConfiguration(
                primary={"url": "https://example.com/logo.png", "width": 200, "height": 60, "alt_text": "Logo"},
                favicon={"url": "https://example.com/favicon.ico", "type": "ico"}
            ),
            layout=LayoutConfig(
                header={"height": 64, "position": "fixed", "show_logo": True, "show_search": True, "show_notifications": True, "show_user_menu": True},
                sidebar={"width": 280, "collapsible": True, "default_collapsed": False, "position": "left", "show_icons": True},
                content={"max_width": 1200, "padding": 24, "background_color": "#fafafa"},
                footer={"show": True, "height": 48, "content": "© 2025 SMEFlow"}
            ),
            region="NG",
            currency_code="NGN"
        )
    
    @pytest.mark.asyncio
    async def test_generate_theme(self, theme_engine, sample_branding):
        """Test theme generation from branding configuration."""
        theme_config = ThemeConfig(
            tenant_id=sample_branding.tenant_id,
            branding=sample_branding,
            cdn_base_url="https://cdn.example.com"
        )
        
        compiled_theme = await theme_engine.generate_theme(theme_config)
        
        assert isinstance(compiled_theme, CompiledTheme)
        assert "--color-primary-main: #1976d2" in compiled_theme.css_variables
        assert "--font-family-primary: Inter, sans-serif" in compiled_theme.css_variables
        assert compiled_theme.cache_key is not None
    
    def test_css_variable_generation(self, theme_engine, sample_branding):
        """Test CSS variable generation."""
        css_vars = theme_engine._generate_css_variables(sample_branding)
        
        assert "--color-primary-main: #1976d2" in css_vars
        assert "--font-family-primary: Inter, sans-serif" in css_vars
        assert "--region: 'NG'" in css_vars
        assert "--currency: 'NGN'" in css_vars
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, theme_engine):
        """Test theme cache invalidation."""
        tenant_id = uuid4()
        
        # Mock Redis client
        theme_engine.redis_client.keys = Mock(return_value=[f"theme:{tenant_id}:key1", f"theme:{tenant_id}:key2"])
        theme_engine.redis_client.delete = Mock()
        
        await theme_engine.invalidate_theme_cache(tenant_id)
        
        theme_engine.redis_client.keys.assert_called_once()
        theme_engine.redis_client.delete.assert_called_once()


class TestAssetProcessor:
    """Test asset processing functionality."""
    
    @pytest.fixture
    def asset_processor(self):
        """Create asset processor instance."""
        with patch('smeflow.ui.asset_processor.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                aws_region="us-east-1",
                s3_bucket_name="test-bucket",
                cdn_base_url="https://cdn.example.com"
            )
            with patch('smeflow.ui.asset_processor.boto3.client'):
                return AssetProcessor()
    
    @patch('smeflow.ui.asset_processor.Image')
    def test_image_validation_success(self, mock_image, asset_processor):
        """Test successful image validation."""
        # Mock PIL Image validation
        mock_img = Mock()
        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_img.verify.return_value = None  # No exception means valid
        
        # Create simple PNG data
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        # Should not raise exception
        asset_processor._validate_image_file(png_data, "test.png", 1024*1024)
    
    def test_image_validation_size_error(self, asset_processor):
        """Test image validation with size error."""
        large_data = b'x' * (3 * 1024 * 1024)  # 3MB
        
        with pytest.raises(AssetValidationError, match="exceeds maximum"):
            asset_processor._validate_image_file(large_data, "test.png", 2 * 1024 * 1024)
    
    def test_image_validation_format_error(self, asset_processor):
        """Test image validation with format error."""
        invalid_data = b'invalid image data'
        
        with pytest.raises(AssetValidationError, match="Unsupported image format"):
            asset_processor._validate_image_file(invalid_data, "test.txt", 1024*1024)
    
    @pytest.mark.asyncio
    @patch('smeflow.ui.asset_processor.BytesIO')
    @patch('smeflow.ui.asset_processor.Image')
    async def test_logo_processing(self, mock_image, mock_bytesio, asset_processor):
        """Test logo processing with variants."""
        tenant_id = uuid4()
        mock_img = Mock()
        mock_img.width = 200
        mock_img.height = 60
        # Ensure width and height support arithmetic operations
        mock_img.width.__truediv__ = Mock(return_value=3.33)  # 200/60 = 3.33
        mock_img.width.__gt__ = Mock(return_value=True)  # width > height
        mock_img.format = 'PNG'
        mock_img.mode = 'RGB'
        mock_img.verify.return_value = None
        mock_img.copy.return_value = mock_img
        mock_img.resize.return_value = mock_img
        mock_img.save = Mock()
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Mock BytesIO for resize operations
        mock_bytesio.return_value.getvalue.return_value = b'resized_image_data'
        
        # Mock S3 upload
        asset_processor._upload_to_s3 = AsyncMock(return_value="https://s3.example.com/test.png")
        asset_processor._save_asset_record = AsyncMock()
        
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        result = await asset_processor.process_logo(png_data, "logo.png", tenant_id)
        
        assert isinstance(result, ProcessedAsset)
        assert result.original_url.startswith("https://cdn.example.com")
        assert len(result.variants) > 0
        assert result.file_size == len(png_data)


class TestLocalizationService:
    """Test localization service functionality."""
    
    @pytest.fixture
    def localization_service(self):
        """Create localization service instance."""
        return LocalizationService()
    
    def test_get_supported_languages(self, localization_service):
        """Test getting supported languages."""
        all_languages = localization_service.get_supported_languages()
        assert len(all_languages) > 15  # Should have many African languages
        
        # Test filtering by region
        ng_languages = localization_service.get_supported_languages("NG")
        assert any(lang.code == "en" for lang in ng_languages)
        assert any(lang.code == "ha" for lang in ng_languages)
        assert any(lang.code == "yo" for lang in ng_languages)
    
    def test_get_language(self, localization_service):
        """Test getting specific language."""
        swahili = localization_service.get_language("sw")
        assert swahili is not None
        assert swahili.name == "Swahili"
        assert swahili.native_name == "Kiswahili"
        assert "KE" in swahili.regions
        
        # Test non-existent language
        unknown = localization_service.get_language("unknown")
        assert unknown is None
    
    def test_get_regional_format(self, localization_service):
        """Test getting regional format."""
        ng_format = localization_service.get_regional_format("NG")
        assert ng_format is not None
        assert ng_format.currency["code"] == "NGN"
        assert ng_format.currency["symbol"] == "₦"
        assert ng_format.phone["country_code"] == "+234"
        
        ke_format = localization_service.get_regional_format("KE")
        assert ke_format.currency["code"] == "KES"
        assert ke_format.currency["symbol"] == "KSh"
    
    def test_currency_formatting(self, localization_service):
        """Test currency formatting."""
        formatted = localization_service.format_currency(1234.56, "NGN", "en")
        assert "1,234.56" in formatted or "₦" in formatted
    
    def test_phone_number_formatting(self, localization_service):
        """Test phone number formatting."""
        formatted = localization_service.format_phone_number("08012345678", "NG")
        assert formatted.startswith("+234")
        
        formatted_with_plus = localization_service.format_phone_number("+2348012345678", "NG")
        assert formatted_with_plus.startswith("+234")
    
    def test_text_direction(self, localization_service):
        """Test text direction detection."""
        assert localization_service.get_text_direction("en") == "ltr"
        assert localization_service.get_text_direction("ar") == "rtl"
        assert localization_service.get_text_direction("sw") == "ltr"
    
    def test_cultural_preferences(self, localization_service):
        """Test cultural preferences."""
        ng_prefs = localization_service.get_cultural_preferences("NG")
        assert ng_prefs["business_hours"]["start"] == "08:00"
        assert ng_prefs["weekend_days"] == [6, 0]  # Saturday, Sunday
        assert "independence_day" in ng_prefs["holidays"]
        
        eg_prefs = localization_service.get_cultural_preferences("EG")
        assert eg_prefs["weekend_days"] == [5, 6]  # Friday, Saturday
        assert "ramadan" in eg_prefs["holidays"]
    
    def test_create_localization_config(self, localization_service):
        """Test creating localization configuration."""
        tenant_id = uuid4()
        config = localization_service.create_localization_config(
            tenant_id=tenant_id,
            region="NG",
            languages=["en", "ha", "yo"],
            default_language="en"
        )
        
        assert isinstance(config, LocalizationConfig)
        assert config.tenant_id == tenant_id
        assert config.primary_region == "NG"
        assert config.default_language == "en"
        assert "en" in config.supported_languages
        assert "ha" in config.supported_languages
        assert "yo" in config.supported_languages


class TestAfricanMarketOptimizations:
    """Test African market specific optimizations."""
    
    def test_nigerian_market_config(self):
        """Test Nigerian market configuration."""
        service = LocalizationService()
        ng_format = service.get_regional_format("NG")
        
        assert ng_format.currency["code"] == "NGN"
        assert ng_format.currency["symbol"] == "₦"
        assert ng_format.date_time["timezone"] == "Africa/Lagos"
        assert ng_format.phone["country_code"] == "+234"
    
    def test_kenyan_market_config(self):
        """Test Kenyan market configuration."""
        service = LocalizationService()
        ke_format = service.get_regional_format("KE")
        
        assert ke_format.currency["code"] == "KES"
        assert ke_format.currency["symbol"] == "KSh"
        assert ke_format.date_time["timezone"] == "Africa/Nairobi"
        assert ke_format.phone["country_code"] == "+254"
    
    def test_south_african_market_config(self):
        """Test South African market configuration."""
        service = LocalizationService()
        za_format = service.get_regional_format("ZA")
        
        assert za_format.currency["code"] == "ZAR"
        assert za_format.currency["symbol"] == "R"
        assert za_format.date_time["timezone"] == "Africa/Johannesburg"
        assert za_format.phone["country_code"] == "+27"
    
    def test_multi_language_support(self):
        """Test comprehensive multi-language support."""
        service = LocalizationService()
        
        # Test major African languages
        languages = ["en", "sw", "ha", "yo", "ig", "am", "ar", "fr", "pt", "af", "zu", "xh"]
        for lang_code in languages:
            lang = service.get_language(lang_code)
            assert lang is not None
            assert lang.code == lang_code
            assert len(lang.regions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
