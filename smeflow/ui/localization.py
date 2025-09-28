"""
Localization service for SMEFlow white-label UI system.

This module provides comprehensive multi-language support with African market
optimizations including 50+ languages, regional formatting, and cultural adaptations.
"""

import json
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field
from babel import Locale, dates, numbers
from babel.core import UnknownLocaleError

from ..core.config import get_settings


class Language(BaseModel):
    """Language configuration model."""
    
    code: str = Field(description="ISO 639-1 language code")
    name: str = Field(description="Language name in English")
    native_name: str = Field(description="Language name in native script")
    flag: str = Field(description="Flag emoji or icon")
    rtl: bool = Field(default=False, description="Right-to-left text direction")
    regions: List[str] = Field(description="Applicable regions/countries")
    script: Optional[str] = Field(None, description="Writing script (Latin, Arabic, etc.)")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RegionalFormat(BaseModel):
    """Regional formatting configuration."""
    
    currency: Dict[str, Any] = Field(description="Currency formatting")
    date_time: Dict[str, Any] = Field(description="Date and time formatting")
    address: Dict[str, Any] = Field(description="Address formatting")
    phone: Dict[str, Any] = Field(description="Phone number formatting")
    numbers: Dict[str, Any] = Field(description="Number formatting")


class LocalizationConfig(BaseModel):
    """Complete localization configuration."""
    
    tenant_id: UUID = Field(description="Tenant identifier")
    default_language: str = Field(description="Default language code")
    supported_languages: List[str] = Field(description="Supported language codes")
    fallback_language: str = Field(default="en", description="Fallback language")
    rtl_languages: List[str] = Field(description="Right-to-left languages")
    regional_formats: Dict[str, RegionalFormat] = Field(description="Regional formatting by country")
    
    # African market specific
    primary_region: str = Field(description="Primary region (NG, KE, ZA, etc.)")
    local_languages: List[str] = Field(description="Local languages for the region")
    cultural_preferences: Dict[str, Any] = Field(description="Cultural preferences")


class LocalizationService:
    """
    Comprehensive localization service for multi-tenant African markets.
    
    Provides language support, regional formatting, cultural adaptations,
    and translation management for 50+ languages.
    """
    
    # African languages with comprehensive support
    AFRICAN_LANGUAGES = {
        'en': Language(
            code='en',
            name='English',
            native_name='English',
            flag='🇬🇧',
            rtl=False,
            regions=['NG', 'KE', 'ZA', 'GH', 'UG', 'TZ', 'RW', 'ET', 'MW', 'ZM', 'ZW', 'BW', 'LS', 'SZ'],
            script='Latin'
        ),
        'sw': Language(
            code='sw',
            name='Swahili',
            native_name='Kiswahili',
            flag='🇰🇪',
            rtl=False,
            regions=['KE', 'TZ', 'UG', 'RW', 'CD', 'BI'],
            script='Latin'
        ),
        'ha': Language(
            code='ha',
            name='Hausa',
            native_name='Harshen Hausa',
            flag='🇳🇬',
            rtl=False,
            regions=['NG', 'NE', 'GH', 'CM', 'TD', 'BF'],
            script='Latin'
        ),
        'yo': Language(
            code='yo',
            name='Yoruba',
            native_name='Èdè Yorùbá',
            flag='🇳🇬',
            rtl=False,
            regions=['NG', 'BJ', 'TG'],
            script='Latin'
        ),
        'ig': Language(
            code='ig',
            name='Igbo',
            native_name='Asụsụ Igbo',
            flag='🇳🇬',
            rtl=False,
            regions=['NG'],
            script='Latin'
        ),
        'am': Language(
            code='am',
            name='Amharic',
            native_name='አማርኛ',
            flag='🇪🇹',
            rtl=False,
            regions=['ET'],
            script='Ethiopic'
        ),
        'ar': Language(
            code='ar',
            name='Arabic',
            native_name='العربية',
            flag='🇪🇬',
            rtl=True,
            regions=['EG', 'MA', 'TN', 'DZ', 'LY', 'SD', 'DJ', 'SO', 'MR'],
            script='Arabic'
        ),
        'fr': Language(
            code='fr',
            name='French',
            native_name='Français',
            flag='🇫🇷',
            rtl=False,
            regions=['SN', 'CI', 'BF', 'ML', 'NE', 'TD', 'CM', 'GA', 'CG', 'CD', 'CF', 'DJ', 'MG', 'KM', 'SC'],
            script='Latin'
        ),
        'pt': Language(
            code='pt',
            name='Portuguese',
            native_name='Português',
            flag='🇵🇹',
            rtl=False,
            regions=['AO', 'MZ', 'GW', 'ST', 'CV'],
            script='Latin'
        ),
        'af': Language(
            code='af',
            name='Afrikaans',
            native_name='Afrikaans',
            flag='🇿🇦',
            rtl=False,
            regions=['ZA', 'NA'],
            script='Latin'
        ),
        'zu': Language(
            code='zu',
            name='Zulu',
            native_name='isiZulu',
            flag='🇿🇦',
            rtl=False,
            regions=['ZA'],
            script='Latin'
        ),
        'xh': Language(
            code='xh',
            name='Xhosa',
            native_name='isiXhosa',
            flag='🇿🇦',
            rtl=False,
            regions=['ZA'],
            script='Latin'
        ),
        'st': Language(
            code='st',
            name='Sotho',
            native_name='Sesotho',
            flag='🇿🇦',
            rtl=False,
            regions=['ZA', 'LS'],
            script='Latin'
        ),
        'tn': Language(
            code='tn',
            name='Tswana',
            native_name='Setswana',
            flag='🇧🇼',
            rtl=False,
            regions=['BW', 'ZA'],
            script='Latin'
        ),
        'om': Language(
            code='om',
            name='Oromo',
            native_name='Afaan Oromoo',
            flag='🇪🇹',
            rtl=False,
            regions=['ET', 'KE'],
            script='Latin'
        ),
        'ti': Language(
            code='ti',
            name='Tigrinya',
            native_name='ትግርኛ',
            flag='🇪🇷',
            rtl=False,
            regions=['ER', 'ET'],
            script='Ethiopic'
        ),
        'lg': Language(
            code='lg',
            name='Luganda',
            native_name='Oluganda',
            flag='🇺🇬',
            rtl=False,
            regions=['UG'],
            script='Latin'
        ),
        'rw': Language(
            code='rw',
            name='Kinyarwanda',
            native_name='Ikinyarwanda',
            flag='🇷🇼',
            rtl=False,
            regions=['RW'],
            script='Latin'
        ),
        'rn': Language(
            code='rn',
            name='Kirundi',
            native_name='Ikirundi',
            flag='🇧🇮',
            rtl=False,
            regions=['BI'],
            script='Latin'
        ),
        'mg': Language(
            code='mg',
            name='Malagasy',
            native_name='Malagasy',
            flag='🇲🇬',
            rtl=False,
            regions=['MG'],
            script='Latin'
        ),
        'wo': Language(
            code='wo',
            name='Wolof',
            native_name='Wolof',
            flag='🇸🇳',
            rtl=False,
            regions=['SN', 'GM'],
            script='Latin'
        )
    }
    
    # Regional formatting configurations
    REGIONAL_FORMATS = {
        'NG': RegionalFormat(
            currency={
                'code': 'NGN',
                'symbol': '₦',
                'position': 'before',
                'decimals': 2,
                'thousands_separator': ',',
                'decimal_separator': '.'
            },
            date_time={
                'date_format': 'DD/MM/YYYY',
                'time_format': '12h',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Africa/Lagos'
            },
            address={
                'format': ['street', 'city', 'state', 'postal_code', 'country'],
                'postal_code_label': 'Postal Code',
                'state_label': 'State',
                'required': ['street', 'city', 'state']
            },
            phone={
                'country_code': '+234',
                'format': '(XXX) XXX-XXXX',
                'national_prefix': '0'
            },
            numbers={
                'thousands_separator': ',',
                'decimal_separator': '.',
                'grouping': [3]
            }
        ),
        'KE': RegionalFormat(
            currency={
                'code': 'KES',
                'symbol': 'KSh',
                'position': 'before',
                'decimals': 2,
                'thousands_separator': ',',
                'decimal_separator': '.'
            },
            date_time={
                'date_format': 'DD/MM/YYYY',
                'time_format': '24h',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Africa/Nairobi'
            },
            address={
                'format': ['street', 'city', 'county', 'postal_code', 'country'],
                'postal_code_label': 'Postal Code',
                'state_label': 'County',
                'required': ['street', 'city', 'county']
            },
            phone={
                'country_code': '+254',
                'format': '(XXX) XXX-XXX',
                'national_prefix': '0'
            },
            numbers={
                'thousands_separator': ',',
                'decimal_separator': '.',
                'grouping': [3]
            }
        ),
        'ZA': RegionalFormat(
            currency={
                'code': 'ZAR',
                'symbol': 'R',
                'position': 'before',
                'decimals': 2,
                'thousands_separator': ' ',
                'decimal_separator': ','
            },
            date_time={
                'date_format': 'YYYY/MM/DD',
                'time_format': '24h',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Africa/Johannesburg'
            },
            address={
                'format': ['street', 'suburb', 'city', 'province', 'postal_code', 'country'],
                'postal_code_label': 'Postal Code',
                'state_label': 'Province',
                'required': ['street', 'city', 'province', 'postal_code']
            },
            phone={
                'country_code': '+27',
                'format': '(XXX) XXX-XXXX',
                'national_prefix': '0'
            },
            numbers={
                'thousands_separator': ' ',
                'decimal_separator': ',',
                'grouping': [3]
            }
        ),
        'GH': RegionalFormat(
            currency={
                'code': 'GHS',
                'symbol': '₵',
                'position': 'before',
                'decimals': 2,
                'thousands_separator': ',',
                'decimal_separator': '.'
            },
            date_time={
                'date_format': 'DD/MM/YYYY',
                'time_format': '12h',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Africa/Accra'
            },
            address={
                'format': ['street', 'city', 'region', 'country'],
                'postal_code_label': 'Postal Code',
                'state_label': 'Region',
                'required': ['street', 'city', 'region']
            },
            phone={
                'country_code': '+233',
                'format': '(XXX) XXX-XXXX',
                'national_prefix': '0'
            },
            numbers={
                'thousands_separator': ',',
                'decimal_separator': '.',
                'grouping': [3]
            }
        ),
        'EG': RegionalFormat(
            currency={
                'code': 'EGP',
                'symbol': '£',
                'position': 'before',
                'decimals': 2,
                'thousands_separator': ',',
                'decimal_separator': '.'
            },
            date_time={
                'date_format': 'DD/MM/YYYY',
                'time_format': '12h',
                'first_day_of_week': 6,  # Saturday
                'timezone': 'Africa/Cairo'
            },
            address={
                'format': ['street', 'district', 'city', 'governorate', 'postal_code', 'country'],
                'postal_code_label': 'Postal Code',
                'state_label': 'Governorate',
                'required': ['street', 'city', 'governorate']
            },
            phone={
                'country_code': '+20',
                'format': '(XXX) XXX-XXXX',
                'national_prefix': '0'
            },
            numbers={
                'thousands_separator': ',',
                'decimal_separator': '.',
                'grouping': [3]
            }
        )
    }
    
    def __init__(self):
        """Initialize localization service."""
        self.settings = get_settings()
        self.translations_cache: Dict[str, Dict[str, str]] = {}
        self.translations_dir = Path(__file__).parent / "translations"
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translation files from disk."""
        if not self.translations_dir.exists():
            self.translations_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing translation files
        for lang_file in self.translations_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations_cache[lang_code] = json.load(f)
            except Exception:
                # Skip invalid translation files
                continue
    
    def get_supported_languages(self, region: Optional[str] = None) -> List[Language]:
        """
        Get list of supported languages, optionally filtered by region.
        
        Args:
            region: Optional region code to filter languages
            
        Returns:
            List of supported Language objects
        """
        languages = list(self.AFRICAN_LANGUAGES.values())
        
        if region:
            languages = [lang for lang in languages if region in lang.regions]
        
        return languages
    
    def get_language(self, code: str) -> Optional[Language]:
        """Get language configuration by code."""
        return self.AFRICAN_LANGUAGES.get(code)
    
    def get_regional_format(self, region: str) -> Optional[RegionalFormat]:
        """Get regional formatting configuration."""
        return self.REGIONAL_FORMATS.get(region)
    
    def translate(
        self, 
        key: str, 
        language: str, 
        fallback_language: str = "en",
        **kwargs
    ) -> str:
        """
        Translate a key to specified language with fallback.
        
        Args:
            key: Translation key
            language: Target language code
            fallback_language: Fallback language if translation not found
            **kwargs: Variables for string interpolation
            
        Returns:
            Translated string
        """
        # Try target language first
        if language in self.translations_cache:
            translation = self.translations_cache[language].get(key)
            if translation:
                return self._interpolate_string(translation, **kwargs)
        
        # Try fallback language
        if fallback_language in self.translations_cache:
            translation = self.translations_cache[fallback_language].get(key)
            if translation:
                return self._interpolate_string(translation, **kwargs)
        
        # Return key if no translation found
        return key
    
    def _interpolate_string(self, template: str, **kwargs) -> str:
        """Interpolate variables in translation string."""
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    
    def format_currency(
        self, 
        amount: float, 
        currency_code: str, 
        locale: str = "en"
    ) -> str:
        """
        Format currency amount according to locale.
        
        Args:
            amount: Amount to format
            currency_code: Currency code (NGN, KES, etc.)
            locale: Locale for formatting
            
        Returns:
            Formatted currency string
        """
        try:
            babel_locale = Locale.parse(locale)
            return numbers.format_currency(amount, currency_code, locale=babel_locale)
        except (UnknownLocaleError, ValueError):
            # Fallback to simple formatting
            symbols = {
                'NGN': '₦',
                'KES': 'KSh',
                'ZAR': 'R',
                'GHS': '₵',
                'EGP': '£'
            }
            symbol = symbols.get(currency_code, currency_code)
            return f"{symbol}{amount:,.2f}"
    
    def format_date(
        self, 
        date: datetime, 
        format_type: str = "medium",
        locale: str = "en"
    ) -> str:
        """
        Format date according to locale.
        
        Args:
            date: Date to format
            format_type: Format type (short, medium, long, full)
            locale: Locale for formatting
            
        Returns:
            Formatted date string
        """
        try:
            babel_locale = Locale.parse(locale)
            return dates.format_date(date, format=format_type, locale=babel_locale)
        except (UnknownLocaleError, ValueError):
            # Fallback to ISO format
            return date.strftime("%Y-%m-%d")
    
    def format_phone_number(self, phone: str, region: str) -> str:
        """
        Format phone number according to regional format.
        
        Args:
            phone: Phone number to format
            region: Region code
            
        Returns:
            Formatted phone number
        """
        regional_format = self.get_regional_format(region)
        if not regional_format:
            return phone
        
        # Basic phone number formatting
        # In production, use phonenumbers library for proper formatting
        phone_config = regional_format.phone
        country_code = phone_config['country_code']
        
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present
        if not phone.startswith('+'):
            if digits.startswith('0'):
                digits = digits[1:]  # Remove national prefix
            return f"{country_code}{digits}"
        
        return phone
    
    def get_text_direction(self, language: str) -> str:
        """Get text direction for language (ltr or rtl)."""
        lang_config = self.get_language(language)
        return "rtl" if lang_config and lang_config.rtl else "ltr"
    
    def get_cultural_preferences(self, region: str) -> Dict[str, Any]:
        """
        Get cultural preferences for region.
        
        Args:
            region: Region code
            
        Returns:
            Cultural preferences dictionary
        """
        cultural_prefs = {
            'NG': {
                'business_hours': {'start': '08:00', 'end': '17:00'},
                'weekend_days': [6, 0],  # Saturday, Sunday
                'holidays': ['new_year', 'independence_day', 'democracy_day', 'christmas'],
                'greeting_style': 'formal',
                'color_preferences': ['green', 'white'],
                'number_format': 'western'
            },
            'KE': {
                'business_hours': {'start': '08:00', 'end': '17:00'},
                'weekend_days': [6, 0],  # Saturday, Sunday
                'holidays': ['new_year', 'independence_day', 'mashujaa_day', 'christmas'],
                'greeting_style': 'warm',
                'color_preferences': ['red', 'black', 'green'],
                'number_format': 'western'
            },
            'ZA': {
                'business_hours': {'start': '08:00', 'end': '17:00'},
                'weekend_days': [6, 0],  # Saturday, Sunday
                'holidays': ['new_year', 'freedom_day', 'heritage_day', 'christmas'],
                'greeting_style': 'friendly',
                'color_preferences': ['rainbow'],
                'number_format': 'western'
            },
            'EG': {
                'business_hours': {'start': '09:00', 'end': '17:00'},
                'weekend_days': [5, 6],  # Friday, Saturday
                'holidays': ['new_year', 'revolution_day', 'sinai_liberation', 'ramadan', 'eid'],
                'greeting_style': 'respectful',
                'color_preferences': ['red', 'white', 'black'],
                'number_format': 'arabic'
            }
        }
        
        return cultural_prefs.get(region, cultural_prefs['NG'])  # Default to Nigeria
    
    def create_localization_config(
        self, 
        tenant_id: UUID,
        region: str,
        languages: List[str],
        default_language: str = "en"
    ) -> LocalizationConfig:
        """
        Create localization configuration for tenant.
        
        Args:
            tenant_id: Tenant identifier
            region: Primary region
            languages: Supported languages
            default_language: Default language
            
        Returns:
            LocalizationConfig object
        """
        # Get regional languages
        regional_languages = [
            lang.code for lang in self.get_supported_languages(region)
        ]
        
        # Combine with requested languages
        all_languages = list(set(languages + regional_languages))
        
        # Get RTL languages
        rtl_languages = [
            lang.code for lang in self.get_supported_languages()
            if lang.rtl and lang.code in all_languages
        ]
        
        # Get regional formats
        regional_formats = {}
        for region_code in [region]:  # Can be extended to multiple regions
            format_config = self.get_regional_format(region_code)
            if format_config:
                regional_formats[region_code] = format_config
        
        return LocalizationConfig(
            tenant_id=tenant_id,
            default_language=default_language,
            supported_languages=all_languages,
            fallback_language="en",
            rtl_languages=rtl_languages,
            regional_formats=regional_formats,
            primary_region=region,
            local_languages=regional_languages,
            cultural_preferences=self.get_cultural_preferences(region)
        )
