"""
Asset processing pipeline for SMEFlow white-label UI system.

This module handles upload, processing, optimization, and CDN distribution
of theme assets including logos, images, and fonts.
"""

import os
import hashlib
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from datetime import datetime
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageOps
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..database.connection import get_db_session
from .branding_models import ThemeAsset


class ProcessedAsset(BaseModel):
    """Processed asset with metadata and URLs."""
    
    original_url: str = Field(description="Original asset URL")
    cdn_url: str = Field(description="CDN-optimized URL")
    variants: Dict[str, str] = Field(description="Different size variants")
    optimized_formats: Dict[str, str] = Field(description="Optimized formats (WebP, AVIF)")
    metadata: Dict[str, Any] = Field(description="Asset metadata")
    file_size: int = Field(description="File size in bytes")
    processing_time: float = Field(description="Processing time in seconds")


class AssetValidationError(Exception):
    """Raised when asset validation fails."""
    pass


class AssetProcessor:
    """
    Asset processing pipeline for theme assets.
    
    Handles validation, resizing, optimization, format conversion,
    and CDN upload for tenant branding assets.
    """
    
    # Supported image formats
    SUPPORTED_IMAGE_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/svg+xml': ['.svg'],
        'image/webp': ['.webp']
    }
    
    # Supported font formats
    SUPPORTED_FONT_TYPES = {
        'font/woff': ['.woff'],
        'font/woff2': ['.woff2'],
        'font/ttf': ['.ttf'],
        'font/otf': ['.otf']
    }
    
    # Asset size limits (in bytes)
    MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_FONT_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Image size variants
    LOGO_SIZES = [32, 64, 128, 256, 512]
    IMAGE_SIZES = [150, 300, 600, 1200]
    
    def __init__(self):
        """Initialize asset processor with S3 client."""
        self.settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
            region_name=self.settings.aws_region
        )
        self.bucket_name = self.settings.s3_bucket_name
        self.cdn_base_url = self.settings.cdn_base_url
    
    async def process_logo(
        self, 
        file_data: bytes, 
        filename: str, 
        tenant_id: UUID,
        asset_type: str = "logo"
    ) -> ProcessedAsset:
        """
        Process logo asset with multiple size variants.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            tenant_id: Tenant identifier
            asset_type: Type of asset (logo, favicon, etc.)
            
        Returns:
            ProcessedAsset: Processed asset with URLs and metadata
        """
        start_time = datetime.utcnow()
        
        # Validate file
        self._validate_image_file(file_data, filename, self.MAX_LOGO_SIZE)
        
        # Generate unique filename
        file_hash = hashlib.md5(file_data).hexdigest()[:12]
        file_ext = Path(filename).suffix.lower()
        base_filename = f"{tenant_id}/{asset_type}/{file_hash}"
        
        # Process original image
        original_image = Image.open(BytesIO(file_data))
        original_image = ImageOps.exif_transpose(original_image)  # Fix rotation
        
        # Generate size variants
        variants = {}
        for size in self.LOGO_SIZES:
            variant_data = self._resize_image(original_image, size, size)
            variant_filename = f"{base_filename}_{size}x{size}{file_ext}"
            variant_url = await self._upload_to_s3(variant_data, variant_filename)
            variants[f"{size}x{size}"] = variant_url
        
        # Upload original
        original_filename = f"{base_filename}_original{file_ext}"
        original_url = await self._upload_to_s3(file_data, original_filename)
        
        # Generate optimized formats
        optimized_formats = {}
        if file_ext != '.svg':  # Don't optimize SVG files
            # WebP format
            webp_data = self._convert_to_webp(original_image)
            webp_filename = f"{base_filename}_original.webp"
            webp_url = await self._upload_to_s3(webp_data, webp_filename)
            optimized_formats['webp'] = webp_url
            
            # AVIF format (if supported)
            try:
                avif_data = self._convert_to_avif(original_image)
                avif_filename = f"{base_filename}_original.avif"
                avif_url = await self._upload_to_s3(avif_data, avif_filename)
                optimized_formats['avif'] = avif_url
            except Exception:
                # AVIF not supported, skip
                pass
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create processed asset
        processed_asset = ProcessedAsset(
            original_url=f"{self.cdn_base_url}/{original_filename}",
            cdn_url=f"{self.cdn_base_url}/{original_filename}",
            variants={k: f"{self.cdn_base_url}/{v.split('/')[-1]}" for k, v in variants.items()},
            optimized_formats={k: f"{self.cdn_base_url}/{v.split('/')[-1]}" for k, v in optimized_formats.items()},
            metadata={
                'original_filename': filename,
                'dimensions': f"{original_image.width}x{original_image.height}",
                'format': original_image.format,
                'mode': original_image.mode,
                'has_transparency': original_image.mode in ('RGBA', 'LA') or 'transparency' in original_image.info
            },
            file_size=len(file_data),
            processing_time=processing_time
        )
        
        # Save to database
        await self._save_asset_record(tenant_id, processed_asset, asset_type, filename)
        
        return processed_asset
    
    async def process_font(
        self, 
        file_data: bytes, 
        filename: str, 
        tenant_id: UUID
    ) -> ProcessedAsset:
        """
        Process font asset.
        
        Args:
            file_data: Raw font file data
            filename: Original filename
            tenant_id: Tenant identifier
            
        Returns:
            ProcessedAsset: Processed font asset
        """
        start_time = datetime.utcnow()
        
        # Validate font file
        self._validate_font_file(file_data, filename, self.MAX_FONT_SIZE)
        
        # Generate unique filename
        file_hash = hashlib.md5(file_data).hexdigest()[:12]
        file_ext = Path(filename).suffix.lower()
        font_filename = f"{tenant_id}/fonts/{file_hash}{file_ext}"
        
        # Upload to S3
        font_url = await self._upload_to_s3(file_data, font_filename)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create processed asset
        processed_asset = ProcessedAsset(
            original_url=f"{self.cdn_base_url}/{font_filename}",
            cdn_url=f"{self.cdn_base_url}/{font_filename}",
            variants={},
            optimized_formats={},
            metadata={
                'original_filename': filename,
                'font_format': file_ext[1:],  # Remove dot
                'mime_type': mimetypes.guess_type(filename)[0]
            },
            file_size=len(file_data),
            processing_time=processing_time
        )
        
        # Save to database
        await self._save_asset_record(tenant_id, processed_asset, "font", filename)
        
        return processed_asset
    
    def _validate_image_file(self, file_data: bytes, filename: str, max_size: int) -> None:
        """Validate image file format and size."""
        # Check file size
        if len(file_data) > max_size:
            raise AssetValidationError(f"File size {len(file_data)} exceeds maximum {max_size} bytes")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        mime_type = mimetypes.guess_type(filename)[0]
        
        if mime_type not in self.SUPPORTED_IMAGE_TYPES:
            raise AssetValidationError(f"Unsupported image format: {mime_type}")
        
        if file_ext not in self.SUPPORTED_IMAGE_TYPES[mime_type]:
            raise AssetValidationError(f"File extension {file_ext} doesn't match MIME type {mime_type}")
        
        # Validate image can be opened (except SVG)
        if mime_type != 'image/svg+xml':
            try:
                with Image.open(BytesIO(file_data)) as img:
                    img.verify()
            except Exception as e:
                raise AssetValidationError(f"Invalid image file: {str(e)}")
    
    def _validate_font_file(self, file_data: bytes, filename: str, max_size: int) -> None:
        """Validate font file format and size."""
        # Check file size
        if len(file_data) > max_size:
            raise AssetValidationError(f"File size {len(file_data)} exceeds maximum {max_size} bytes")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        mime_type = mimetypes.guess_type(filename)[0]
        
        # Font MIME type detection is not reliable, so check extension
        supported_extensions = []
        for exts in self.SUPPORTED_FONT_TYPES.values():
            supported_extensions.extend(exts)
        
        if file_ext not in supported_extensions:
            raise AssetValidationError(f"Unsupported font format: {file_ext}")
    
    def _resize_image(self, image: Image.Image, width: int, height: int) -> bytes:
        """Resize image to specified dimensions."""
        # Calculate aspect ratio
        aspect_ratio = image.width / image.height
        
        if aspect_ratio > 1:  # Landscape
            new_width = width
            new_height = int(width / aspect_ratio)
        else:  # Portrait or square
            new_height = height
            new_width = int(height * aspect_ratio)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        output = BytesIO()
        format_name = image.format if image.format else 'PNG'
        resized.save(output, format=format_name, optimize=True, quality=85)
        return output.getvalue()
    
    def _convert_to_webp(self, image: Image.Image) -> bytes:
        """Convert image to WebP format."""
        output = BytesIO()
        # Convert RGBA to RGB for WebP if necessary
        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
            image = background
        
        image.save(output, format='WebP', optimize=True, quality=85)
        return output.getvalue()
    
    def _convert_to_avif(self, image: Image.Image) -> bytes:
        """Convert image to AVIF format (if supported)."""
        output = BytesIO()
        # AVIF support requires pillow-avif-plugin
        try:
            image.save(output, format='AVIF', optimize=True, quality=85)
            return output.getvalue()
        except Exception:
            raise Exception("AVIF format not supported")
    
    async def _upload_to_s3(self, file_data: bytes, filename: str) -> str:
        """Upload file to S3 and return URL."""
        try:
            # Set content type
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_data,
                ContentType=content_type,
                CacheControl='public, max-age=31536000',  # 1 year cache
                ACL='public-read'
            )
            
            return f"https://{self.bucket_name}.s3.{self.settings.aws_region}.amazonaws.com/{filename}"
        
        except ClientError as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    async def _save_asset_record(
        self, 
        tenant_id: UUID, 
        asset: ProcessedAsset, 
        asset_type: str, 
        original_filename: str
    ) -> None:
        """Save asset record to database."""
        async with get_db_session() as session:
            # Extract dimensions from metadata
            dimensions = asset.metadata.get('dimensions', '0x0')
            width, height = map(int, dimensions.split('x'))
            
            # Create asset record
            asset_record = ThemeAsset(
                tenant_id=tenant_id,
                branding_id=None,  # Will be set when associated with branding
                asset_type=asset_type,
                asset_name=Path(original_filename).stem,
                original_filename=original_filename,
                url=asset.original_url,
                cdn_url=asset.cdn_url,
                file_size=asset.file_size,
                mime_type=asset.metadata.get('mime_type', 'application/octet-stream'),
                width=width if width > 0 else None,
                height=height if height > 0 else None,
                variants=asset.variants,
                optimized_formats=asset.optimized_formats
            )
            
            session.add(asset_record)
            await session.commit()
    
    async def delete_asset(self, tenant_id: UUID, asset_id: UUID) -> bool:
        """Delete asset from S3 and database."""
        async with get_db_session() as session:
            # Get asset record
            asset = await session.get(ThemeAsset, asset_id)
            if not asset or asset.tenant_id != tenant_id:
                return False
            
            try:
                # Delete from S3
                s3_key = asset.url.split('/')[-1]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                
                # Delete variants and optimized formats
                for variant_url in asset.variants.values():
                    variant_key = variant_url.split('/')[-1]
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=variant_key)
                
                for optimized_url in asset.optimized_formats.values():
                    optimized_key = optimized_url.split('/')[-1]
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=optimized_key)
                
                # Delete from database
                await session.delete(asset)
                await session.commit()
                
                return True
                
            except Exception:
                await session.rollback()
                return False
    
    async def get_asset_usage_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get asset usage statistics for a tenant."""
        async with get_db_session() as session:
            # Query asset statistics
            # This would include total size, count by type, etc.
            return {
                "total_assets": 0,
                "total_size_bytes": 0,
                "assets_by_type": {},
                "storage_cost_estimate": 0.0
            }
