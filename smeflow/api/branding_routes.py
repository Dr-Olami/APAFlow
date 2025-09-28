"""
API routes for SMEFlow white-label branding system.

This module provides REST API endpoints for managing tenant branding
configurations, theme generation, asset upload, and localization.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from ..database.connection import get_db_session
from ..auth.dependencies import get_current_tenant, require_permissions
from ..ui.branding_models import (
    BrandingConfiguration, 
    TenantBranding,
    ColorPalette,
    TypographyConfig,
    LogoConfiguration,
    LayoutConfig
)
from ..ui.theme_engine import ThemeEngine, ThemeConfig, CompiledTheme
from ..ui.asset_processor import AssetProcessor, ProcessedAsset, AssetValidationError
from ..ui.localization import LocalizationService, Language, LocalizationConfig


# Request/Response Models
class BrandingCreateRequest(BaseModel):
    """Request model for creating branding configuration."""
    
    name: str = Field(description="Configuration name", max_length=255)
    colors: ColorPalette = Field(description="Color palette")
    typography: TypographyConfig = Field(description="Typography settings")
    logo: LogoConfiguration = Field(description="Logo configuration")
    layout: LayoutConfig = Field(description="Layout settings")
    custom_css: Optional[str] = Field(None, description="Custom CSS overrides")
    region: str = Field(description="Target region")
    language_code: str = Field(default="en", description="Primary language")
    currency_code: str = Field(description="Primary currency")


class BrandingUpdateRequest(BaseModel):
    """Request model for updating branding configuration."""
    
    name: Optional[str] = Field(None, max_length=255)
    colors: Optional[ColorPalette] = None
    typography: Optional[TypographyConfig] = None
    logo: Optional[LogoConfiguration] = None
    layout: Optional[LayoutConfig] = None
    custom_css: Optional[str] = None
    is_active: Optional[bool] = None


class BrandingResponse(BaseModel):
    """Response model for branding configuration."""
    
    id: UUID
    tenant_id: UUID
    name: str
    version: str
    colors: ColorPalette
    typography: TypographyConfig
    logo: LogoConfiguration
    layout: LayoutConfig
    custom_css: Optional[str]
    is_active: bool
    region: str
    language_code: str
    currency_code: str
    created_at: datetime
    updated_at: datetime


class ThemeGenerateRequest(BaseModel):
    """Request model for theme generation."""
    
    branding_id: UUID = Field(description="Branding configuration ID")
    cache_duration: int = Field(default=3600, description="Cache duration in seconds")
    enable_optimization: bool = Field(default=True, description="Enable optimizations")


class AssetUploadResponse(BaseModel):
    """Response model for asset upload."""
    
    asset_id: UUID
    original_url: str
    cdn_url: str
    variants: Dict[str, str]
    optimized_formats: Dict[str, str]
    metadata: Dict[str, Any]
    processing_time: float


class LocalizationResponse(BaseModel):
    """Response model for localization configuration."""
    
    tenant_id: UUID
    default_language: str
    supported_languages: List[str]
    regional_formats: Dict[str, Any]
    cultural_preferences: Dict[str, Any]


# Initialize services
theme_engine = ThemeEngine()
asset_processor = AssetProcessor()
localization_service = LocalizationService()

# Router setup
router = APIRouter(prefix="/api/branding", tags=["branding"])


@router.post("/configurations", response_model=BrandingResponse)
async def create_branding_configuration(
    request: BrandingCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:write"]))
):
    """
    Create a new branding configuration for the tenant.
    
    Creates a complete branding configuration including colors, typography,
    logos, and layout settings with African market optimizations.
    """
    try:
        # Create branding configuration
        branding_config = BrandingConfiguration(
            tenant_id=tenant_id,
            name=request.name,
            colors=request.colors,
            typography=request.typography,
            logo=request.logo,
            layout=request.layout,
            custom_css=request.custom_css,
            region=request.region,
            language_code=request.language_code,
            currency_code=request.currency_code
        )
        
        # Save to database
        db_branding = TenantBranding(
            tenant_id=tenant_id,
            name=request.name,
            colors=request.colors.dict(),
            typography=request.typography.dict(),
            logo=request.logo.dict(),
            layout=request.layout.dict(),
            custom_css=request.custom_css,
            region=request.region,
            language_code=request.language_code,
            currency_code=request.currency_code
        )
        
        session.add(db_branding)
        await session.commit()
        await session.refresh(db_branding)
        
        # Invalidate theme cache
        await theme_engine.invalidate_theme_cache(tenant_id)
        
        return BrandingResponse(
            id=db_branding.id,
            tenant_id=db_branding.tenant_id,
            name=db_branding.name,
            version=db_branding.version,
            colors=ColorPalette(**db_branding.colors),
            typography=TypographyConfig(**db_branding.typography),
            logo=LogoConfiguration(**db_branding.logo),
            layout=LayoutConfig(**db_branding.layout),
            custom_css=db_branding.custom_css,
            is_active=db_branding.is_active,
            region=db_branding.region,
            language_code=db_branding.language_code,
            currency_code=db_branding.currency_code,
            created_at=db_branding.created_at,
            updated_at=db_branding.updated_at
        )
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create branding configuration: {str(e)}")


@router.get("/configurations", response_model=List[BrandingResponse])
async def list_branding_configurations(
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    active_only: bool = Query(False, description="Return only active configurations"),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """List all branding configurations for the tenant."""
    try:
        query = select(TenantBranding).where(TenantBranding.tenant_id == tenant_id)
        
        if active_only:
            query = query.where(TenantBranding.is_active == True)
        
        result = await session.execute(query)
        configurations = result.scalars().all()
        
        return [
            BrandingResponse(
                id=config.id,
                tenant_id=config.tenant_id,
                name=config.name,
                version=config.version,
                colors=ColorPalette(**config.colors),
                typography=TypographyConfig(**config.typography),
                logo=LogoConfiguration(**config.logo),
                layout=LayoutConfig(**config.layout),
                custom_css=config.custom_css,
                is_active=config.is_active,
                region=config.region,
                language_code=config.language_code,
                currency_code=config.currency_code,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            for config in configurations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list configurations: {str(e)}")


@router.get("/configurations/{config_id}", response_model=BrandingResponse)
async def get_branding_configuration(
    config_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """Get a specific branding configuration."""
    try:
        query = select(TenantBranding).where(
            TenantBranding.id == config_id,
            TenantBranding.tenant_id == tenant_id
        )
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        return BrandingResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            name=config.name,
            version=config.version,
            colors=ColorPalette(**config.colors),
            typography=TypographyConfig(**config.typography),
            logo=LogoConfiguration(**config.logo),
            layout=LayoutConfig(**config.layout),
            custom_css=config.custom_css,
            is_active=config.is_active,
            region=config.region,
            language_code=config.language_code,
            currency_code=config.currency_code,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.put("/configurations/{config_id}", response_model=BrandingResponse)
async def update_branding_configuration(
    config_id: UUID,
    request: BrandingUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:write"]))
):
    """Update a branding configuration."""
    try:
        query = select(TenantBranding).where(
            TenantBranding.id == config_id,
            TenantBranding.tenant_id == tenant_id
        )
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(config, field):
                if field in ['colors', 'typography', 'logo', 'layout'] and value:
                    setattr(config, field, value.dict())
                else:
                    setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(config)
        
        # Invalidate theme cache
        await theme_engine.invalidate_theme_cache(tenant_id)
        
        return BrandingResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            name=config.name,
            version=config.version,
            colors=ColorPalette(**config.colors),
            typography=TypographyConfig(**config.typography),
            logo=LogoConfiguration(**config.logo),
            layout=LayoutConfig(**config.layout),
            custom_css=config.custom_css,
            is_active=config.is_active,
            region=config.region,
            language_code=config.language_code,
            currency_code=config.currency_code,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.post("/theme/generate", response_model=CompiledTheme)
async def generate_theme(
    request: ThemeGenerateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """Generate a compiled theme from branding configuration."""
    try:
        # Get branding configuration
        query = select(TenantBranding).where(
            TenantBranding.id == request.branding_id,
            TenantBranding.tenant_id == tenant_id
        )
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        # Convert to Pydantic model
        branding_config = config.to_pydantic()
        
        # Create theme config
        theme_config = ThemeConfig(
            tenant_id=tenant_id,
            branding=branding_config,
            cache_duration=request.cache_duration,
            cdn_base_url="https://cdn.smeflow.com",  # From settings
            enable_optimization=request.enable_optimization
        )
        
        # Generate theme
        compiled_theme = await theme_engine.generate_theme(theme_config)
        
        return compiled_theme
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate theme: {str(e)}")


@router.get("/theme/css/{config_id}")
async def get_theme_css(
    config_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """Get compiled CSS for a branding configuration."""
    try:
        # Generate theme
        request = ThemeGenerateRequest(branding_id=config_id)
        compiled_theme = await generate_theme(request, tenant_id, session)
        
        # Combine CSS
        full_css = compiled_theme.css_variables
        if compiled_theme.custom_css:
            full_css += "\n\n/* Custom CSS */\n" + compiled_theme.custom_css
        full_css += "\n\n/* Component Styles */\n" + compiled_theme.component_styles
        
        return Response(
            content=full_css,
            media_type="text/css",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Type": "text/css; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get theme CSS: {str(e)}")


@router.post("/assets/upload", response_model=AssetUploadResponse)
async def upload_asset(
    file: UploadFile = File(...),
    asset_type: str = Form(..., description="Asset type (logo, font, image)"),
    tenant_id: UUID = Depends(get_current_tenant),
    _: None = Depends(require_permissions(["branding:write"]))
):
    """Upload and process a branding asset."""
    try:
        # Read file data
        file_data = await file.read()
        
        # Process based on asset type
        if asset_type in ["logo", "favicon", "image"]:
            processed_asset = await asset_processor.process_logo(
                file_data, file.filename, tenant_id, asset_type
            )
        elif asset_type == "font":
            processed_asset = await asset_processor.process_font(
                file_data, file.filename, tenant_id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported asset type: {asset_type}")
        
        return AssetUploadResponse(
            asset_id=UUID("00000000-0000-0000-0000-000000000000"),  # Would be from database
            original_url=processed_asset.original_url,
            cdn_url=processed_asset.cdn_url,
            variants=processed_asset.variants,
            optimized_formats=processed_asset.optimized_formats,
            metadata=processed_asset.metadata,
            processing_time=processed_asset.processing_time
        )
        
    except AssetValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload asset: {str(e)}")


@router.get("/languages", response_model=List[Language])
async def get_supported_languages(
    region: Optional[str] = Query(None, description="Filter by region"),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """Get list of supported languages."""
    try:
        languages = localization_service.get_supported_languages(region)
        return languages
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")


@router.post("/localization", response_model=LocalizationResponse)
async def create_localization_config(
    region: str = Form(..., description="Primary region"),
    languages: List[str] = Form(..., description="Supported languages"),
    default_language: str = Form(default="en", description="Default language"),
    tenant_id: UUID = Depends(get_current_tenant),
    _: None = Depends(require_permissions(["branding:write"]))
):
    """Create localization configuration for tenant."""
    try:
        config = localization_service.create_localization_config(
            tenant_id=tenant_id,
            region=region,
            languages=languages,
            default_language=default_language
        )
        
        return LocalizationResponse(
            tenant_id=config.tenant_id,
            default_language=config.default_language,
            supported_languages=config.supported_languages,
            regional_formats=config.regional_formats,
            cultural_preferences=config.cultural_preferences
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create localization config: {str(e)}")


@router.get("/metrics", response_model=Dict[str, Any])
async def get_branding_metrics(
    tenant_id: UUID = Depends(get_current_tenant),
    _: None = Depends(require_permissions(["branding:read"]))
):
    """Get branding and theme performance metrics."""
    try:
        # Get theme metrics
        theme_metrics = await theme_engine.get_theme_metrics(tenant_id)
        
        # Get asset usage stats
        asset_stats = await asset_processor.get_asset_usage_stats(tenant_id)
        
        return {
            "theme_metrics": theme_metrics,
            "asset_usage": asset_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.delete("/configurations/{config_id}")
async def delete_branding_configuration(
    config_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permissions(["branding:delete"]))
):
    """Delete a branding configuration."""
    try:
        query = select(TenantBranding).where(
            TenantBranding.id == config_id,
            TenantBranding.tenant_id == tenant_id
        )
        result = await session.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise HTTPException(status_code=404, detail="Branding configuration not found")
        
        await session.delete(config)
        await session.commit()
        
        # Invalidate theme cache
        await theme_engine.invalidate_theme_cache(tenant_id)
        
        return {"message": "Branding configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for branding service."""
    return {
        "status": "healthy",
        "service": "branding",
        "features": [
            "theme_generation",
            "asset_processing", 
            "multi_language_support",
            "african_market_optimization",
            "custom_domain_support"
        ],
        "supported_assets": ["logo", "favicon", "font", "image"],
        "supported_languages": len(localization_service.AFRICAN_LANGUAGES),
        "supported_regions": list(localization_service.REGIONAL_FORMATS.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }
