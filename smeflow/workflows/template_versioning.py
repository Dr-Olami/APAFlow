"""
Template versioning system for workflow templates.

This module provides version management capabilities for workflow templates,
including creation, updates, migrations, and deprecation handling.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from packaging import version
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from smeflow.database.models import WorkflowTemplate, WorkflowTemplateVersion
from smeflow.workflows.templates import IndustryTemplate, IndustryType, IndustryTemplateFactory

logger = logging.getLogger(__name__)


class TemplateVersionInfo(BaseModel):
    """Template version information model."""
    
    id: uuid.UUID
    template_id: uuid.UUID
    version: str
    is_current: bool
    is_deprecated: bool
    created_at: datetime
    changelog: Optional[str] = None
    breaking_changes: bool = False
    migration_notes: Optional[str] = None


class TemplateVersionCreate(BaseModel):
    """Template version creation model."""
    
    version: str = Field(..., description="Semantic version string (e.g., '1.0.0')")
    changelog: Optional[str] = Field(None, description="Changes made in this version")
    breaking_changes: bool = Field(False, description="Whether this version has breaking changes")
    migration_notes: Optional[str] = Field(None, description="Notes for migrating from previous versions")
    template_definition: Dict = Field(..., description="Complete template definition")


class TemplateVersionManager:
    """
    Manages workflow template versions and migrations.
    
    Provides functionality for:
    - Creating new template versions
    - Managing current/deprecated versions
    - Template migration logic
    - Version comparison and compatibility
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize template version manager.

        Args:
            db_session: Database session for operations.
        """
        self.db_session = db_session

    async def create_template_from_factory(
        self, 
        industry_type: IndustryType, 
        initial_version: str = "1.0.0"
    ) -> Tuple[WorkflowTemplate, WorkflowTemplateVersion]:
        """
        Create a new template with initial version from factory.

        Args:
            industry_type: Industry type for template creation.
            initial_version: Initial version string.

        Returns:
            Tuple of created template and version.

        Raises:
            ValueError: If template already exists or invalid version.
        """
        # Check if template already exists
        existing = await self._get_template_by_industry(industry_type)
        if existing:
            raise ValueError(f"Template for industry {industry_type} already exists")

        # Get template from factory
        industry_template = IndustryTemplateFactory.get_template(industry_type)
        
        # Create template record
        template = WorkflowTemplate(
            industry_type=industry_type.value,
            name=industry_template.name,
            description=industry_template.description,
            supported_regions=industry_template.supported_regions,
            supported_currencies=industry_template.supported_currencies,
            supported_languages=industry_template.supported_languages
        )
        
        self.db_session.add(template)
        await self.db_session.flush()  # Get template ID

        # Create initial version
        template_version = WorkflowTemplateVersion(
            template_id=template.id,
            version=initial_version,
            is_current=True,
            template_definition=industry_template.model_dump(),
            changelog="Initial template version",
            breaking_changes=False
        )
        
        self.db_session.add(template_version)
        await self.db_session.commit()
        
        logger.info(f"Created template {industry_type} with version {initial_version}")
        return template, template_version

    async def create_new_version(
        self, 
        industry_type: IndustryType, 
        version_data: TemplateVersionCreate
    ) -> WorkflowTemplateVersion:
        """
        Create a new version of an existing template.

        Args:
            industry_type: Industry type of template.
            version_data: Version creation data.

        Returns:
            Created template version.

        Raises:
            ValueError: If template doesn't exist or version conflicts.
        """
        # Get existing template
        template = await self._get_template_by_industry(industry_type)
        if not template:
            raise ValueError(f"Template for industry {industry_type} not found")

        # Validate version format
        self._validate_version_format(version_data.version)

        # Check if version already exists
        existing_version = await self._get_version_by_string(template.id, version_data.version)
        if existing_version:
            raise ValueError(f"Version {version_data.version} already exists")

        # Get current version for comparison
        current_version = await self._get_current_version(template.id)
        if current_version and not self._is_version_newer(version_data.version, current_version.version):
            raise ValueError(f"New version {version_data.version} must be newer than current {current_version.version}")

        # Mark current version as non-current
        if current_version:
            current_version.is_current = False

        # Create new version
        new_version = WorkflowTemplateVersion(
            template_id=template.id,
            version=version_data.version,
            is_current=True,
            changelog=version_data.changelog,
            breaking_changes=version_data.breaking_changes,
            migration_notes=version_data.migration_notes,
            template_definition=version_data.template_definition
        )
        
        self.db_session.add(new_version)
        await self.db_session.commit()
        
        logger.info(f"Created version {version_data.version} for template {industry_type}")
        return new_version

    async def get_current_version(self, industry_type: IndustryType) -> Optional[WorkflowTemplateVersion]:
        """
        Get current version of a template.

        Args:
            industry_type: Industry type of template.

        Returns:
            Current template version or None if not found.
        """
        template = await self._get_template_by_industry(industry_type)
        if not template:
            return None
        
        return await self._get_current_version(template.id)

    async def get_version_history(self, industry_type: IndustryType) -> List[TemplateVersionInfo]:
        """
        Get version history for a template.

        Args:
            industry_type: Industry type of template.

        Returns:
            List of template versions ordered by creation date (newest first).
        """
        template = await self._get_template_by_industry(industry_type)
        if not template:
            return []

        stmt = (
            select(WorkflowTemplateVersion)
            .where(WorkflowTemplateVersion.template_id == template.id)
            .order_by(desc(WorkflowTemplateVersion.created_at))
        )
        
        result = await self.db_session.execute(stmt)
        versions = result.scalars().all()
        
        return [
            TemplateVersionInfo(
                id=v.id,
                template_id=v.template_id,
                version=v.version,
                is_current=v.is_current,
                is_deprecated=v.is_deprecated,
                created_at=v.created_at,
                changelog=v.changelog,
                breaking_changes=v.breaking_changes,
                migration_notes=v.migration_notes
            )
            for v in versions
        ]

    async def deprecate_version(self, industry_type: IndustryType, version_string: str) -> bool:
        """
        Mark a specific version as deprecated.

        Args:
            industry_type: Industry type of template.
            version_string: Version to deprecate.

        Returns:
            True if version was deprecated, False if not found.

        Raises:
            ValueError: If trying to deprecate current version.
        """
        template = await self._get_template_by_industry(industry_type)
        if not template:
            return False

        version_obj = await self._get_version_by_string(template.id, version_string)
        if not version_obj:
            return False

        if version_obj.is_current:
            raise ValueError("Cannot deprecate current version")

        version_obj.is_deprecated = True
        await self.db_session.commit()
        
        logger.info(f"Deprecated version {version_string} for template {industry_type}")
        return True

    async def migrate_template_definition(
        self, 
        old_definition: Dict, 
        from_version: str, 
        to_version: str
    ) -> Dict:
        """
        Migrate template definition between versions.

        Args:
            old_definition: Old template definition.
            from_version: Source version.
            to_version: Target version.

        Returns:
            Migrated template definition.
        """
        # Reason: Basic migration logic - in production this would be more sophisticated
        # with version-specific migration rules and field mappings
        migrated = old_definition.copy()
        
        # Add migration metadata
        migrated["_migration_info"] = {
            "from_version": from_version,
            "to_version": to_version,
            "migrated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Migrated template definition from {from_version} to {to_version}")
        return migrated

    async def get_template_definition(
        self, 
        industry_type: IndustryType, 
        version_string: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get template definition for specific version or current.

        Args:
            industry_type: Industry type of template.
            version_string: Specific version, or None for current.

        Returns:
            Template definition or None if not found.
        """
        template = await self._get_template_by_industry(industry_type)
        if not template:
            return None

        if version_string:
            version_obj = await self._get_version_by_string(template.id, version_string)
        else:
            version_obj = await self._get_current_version(template.id)

        return version_obj.template_definition if version_obj else None

    # Private helper methods

    async def _get_template_by_industry(self, industry_type: IndustryType) -> Optional[WorkflowTemplate]:
        """Get template by industry type."""
        stmt = select(WorkflowTemplate).where(WorkflowTemplate.industry_type == industry_type.value)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_current_version(self, template_id: uuid.UUID) -> Optional[WorkflowTemplateVersion]:
        """Get current version of a template."""
        stmt = (
            select(WorkflowTemplateVersion)
            .where(
                and_(
                    WorkflowTemplateVersion.template_id == template_id,
                    WorkflowTemplateVersion.is_current == True
                )
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_version_by_string(
        self, 
        template_id: uuid.UUID, 
        version_string: str
    ) -> Optional[WorkflowTemplateVersion]:
        """Get version by template ID and version string."""
        stmt = (
            select(WorkflowTemplateVersion)
            .where(
                and_(
                    WorkflowTemplateVersion.template_id == template_id,
                    WorkflowTemplateVersion.version == version_string
                )
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    def _validate_version_format(self, version_string: str) -> None:
        """Validate semantic version format."""
        try:
            version.Version(version_string)
        except version.InvalidVersion:
            raise ValueError(f"Invalid version format: {version_string}")

    def _is_version_newer(self, new_version: str, current_version: str) -> bool:
        """Check if new version is newer than current."""
        try:
            return version.Version(new_version) > version.Version(current_version)
        except version.InvalidVersion:
            return False


async def initialize_default_templates(db_session: AsyncSession) -> None:
    """
    Initialize default templates from factory if they don't exist.

    Args:
        db_session: Database session for operations.
    """
    manager = TemplateVersionManager(db_session)
    
    # Initialize only implemented industry templates
    available_industries = IndustryTemplateFactory.list_available_industries()
    for industry_type in available_industries:
        try:
            existing = await manager._get_template_by_industry(industry_type)
            if not existing:
                await manager.create_template_from_factory(industry_type)
                logger.info(f"Initialized default template for {industry_type}")
        except Exception as e:
            logger.error(f"Failed to initialize template for {industry_type}: {e}")
