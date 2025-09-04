"""
Unit tests for template versioning system.

Tests the template versioning functionality including version creation,
management, migration, and API integration.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from smeflow.workflows.template_versioning import (
    TemplateVersionManager,
    TemplateVersionCreate,
    TemplateVersionInfo,
    initialize_default_templates
)
from smeflow.workflows.templates import IndustryTemplateFactory
from smeflow.workflows.templates import IndustryType
from smeflow.database.models import WorkflowTemplate, WorkflowTemplateVersion


class TestTemplateVersionManager:
    """Test suite for TemplateVersionManager."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock(spec=AsyncSession)
        # Ensure execute returns an awaitable mock
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def version_manager(self, mock_db_session):
        """Create a TemplateVersionManager instance with mock session."""
        return TemplateVersionManager(mock_db_session)

    @pytest.fixture
    def sample_template(self):
        """Create a sample WorkflowTemplate for testing."""
        return WorkflowTemplate(
            id=uuid.uuid4(),
            industry_type="consulting",
            name="Professional Consulting",
            description="Consulting workflow template",
            supported_regions=["NG", "KE", "ZA"],
            supported_currencies=["NGN", "KES", "ZAR"],
            supported_languages=["en", "ha", "sw"]
        )

    @pytest.fixture
    def sample_version(self, sample_template):
        """Create a sample WorkflowTemplateVersion for testing."""
        return WorkflowTemplateVersion(
            id=uuid.uuid4(),
            template_id=sample_template.id,
            version="1.0.0",
            is_current=True,
            is_deprecated=False,
            created_at=datetime.utcnow(),
            changelog="Initial version",
            breaking_changes=False,
            template_definition={"test": "definition"}
        )

    async def test_create_template_from_factory_success(self, version_manager, mock_db_session, sample_template):
        """Test successful template creation from factory."""
        # Mock that template doesn't exist initially
        mock_execute_result = Mock()  # This should be a regular Mock, not AsyncMock
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock flush and commit
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.add = AsyncMock()
        
        template, version = await version_manager.create_template_from_factory(
            IndustryType.CONSULTING, "1.0.0"
        )
        
        # Verify template was created
        assert template is not None
        assert version is not None
        assert version.version == "1.0.0"
        assert version.is_current is True
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()

    async def test_create_template_from_factory_already_exists(self, version_manager, mock_db_session, sample_template):
        """Test template creation when template already exists."""
        # Mock that template already exists
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = sample_template
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        with pytest.raises(ValueError, match="Template for industry IndustryType.CONSULTING already exists"):
            await version_manager.create_template_from_factory(IndustryType.CONSULTING, "1.0.0")

    async def test_create_version_success(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test successful version creation."""
        # Set up sample_version.version to return a proper string
        sample_version.version = "1.0.0"
        
        # Mock existing template, no existing version (for version check), then get current version to deprecate old versions
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = None  # No existing version with same number
        mock_execute_result3 = Mock()
        mock_execute_result3.scalar_one_or_none.return_value = sample_version  # Current version exists
        mock_execute_result4 = Mock()
        mock_execute_result4.scalars.return_value.all.return_value = [sample_version]  # All versions to deprecate
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2, mock_execute_result3, mock_execute_result4])

        version_data = TemplateVersionCreate(
            version="2.0.0",
            template_definition={"new": "definition"},
            changelog="Major update"
        )
        version = await version_manager.create_new_version(IndustryType.CONSULTING, version_data)
        
        assert version is not None
        assert version.version == "2.0.0"
        assert version.is_current is True
        
        # Verify database operations
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()

    async def test_create_version_template_not_found(self, version_manager, mock_db_session):
        """Test version creation when template doesn't exist."""
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        version_data = TemplateVersionCreate(
            version="1.0.0",
            template_definition={"test": "definition"},
            changelog="Initial version"
        )
        with pytest.raises(ValueError, match="Template for industry .* not found"):
            await version_manager.create_new_version(IndustryType.CONSULTING, version_data)

    async def test_create_version_already_exists(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test version creation when version already exists."""
        # Mock existing template and existing version
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        version_data = TemplateVersionCreate(
            version="1.0.0",
            template_definition={"test": "definition"},
            changelog="Duplicate version"
        )
        with pytest.raises(ValueError, match="Version .* already exists"):
            await version_manager.create_new_version(IndustryType.CONSULTING, version_data)

    async def test_create_new_version_success(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test successful creation of new template version."""
        # Mock template exists and current version lookup
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = None
        mock_execute_result3 = Mock()
        mock_execute_result3.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute.side_effect = [mock_execute_result1, mock_execute_result2, mock_execute_result3]
        
        version_data = TemplateVersionCreate(
            version="1.1.0",
            changelog="Added new features",
            breaking_changes=False,
            template_definition={"updated": "definition"}
        )
        
        new_version = await version_manager.create_new_version(IndustryType.CONSULTING, version_data)
        
        assert new_version.version == "1.1.0"
        assert new_version.is_current is True
        assert new_version.changelog == "Added new features"
        
        # Verify current version was marked as non-current
        assert sample_version.is_current is False
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()

    async def test_create_new_version_template_not_found(self, version_manager, mock_db_session):
        """Test new version creation when template doesn't exist."""
        # Mock template not found
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        version_data = TemplateVersionCreate(
            version="1.1.0",
            changelog="Test",
            template_definition={"test": "definition"}
        )
        
        with pytest.raises(ValueError, match="Template for industry IndustryType.CONSULTING not found"):
            await version_manager.create_new_version(IndustryType.CONSULTING, version_data)

    async def test_create_new_version_already_exists(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test new version creation when version already exists."""
        # Mock template exists and version already exists
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute.side_effect = [mock_execute_result1, mock_execute_result2]
        
        version_data = TemplateVersionCreate(
            version="1.0.0",
            changelog="Test",
            template_definition={"test": "definition"}
        )
        
        with pytest.raises(ValueError, match="Version 1.0.0 already exists"):
            await version_manager.create_new_version(IndustryType.CONSULTING, version_data)

    async def test_create_new_version_not_newer(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test new version creation with version that's not newer."""
        # Mock template exists, version doesn't exist, but current version is newer
        sample_version.version = "2.0.0"  # Current version is newer
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = None
        mock_execute_result3 = Mock()
        mock_execute_result3.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute.side_effect = [mock_execute_result1, mock_execute_result2, mock_execute_result3]
        
        version_data = TemplateVersionCreate(
            version="1.5.0",  # Older than current 2.0.0
            changelog="Test",
            template_definition={"test": "definition"}
        )
        
        with pytest.raises(ValueError, match="New version 1.5.0 must be newer than current 2.0.0"):
            await version_manager.create_new_version(IndustryType.CONSULTING, version_data)

    async def test_get_current_version_success(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test successful retrieval of current version."""
        # Mock template exists and has current version
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        current_version = await version_manager.get_current_version(IndustryType.CONSULTING)
        
        assert current_version == sample_version
        assert current_version.version == "1.0.0"
        assert current_version.is_current is True

    async def test_get_current_version_template_not_found(self, version_manager, mock_db_session):
        """Test current version retrieval when template doesn't exist."""
        # Mock template not found
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        current_version = await version_manager.get_current_version(IndustryType.CONSULTING)
        
        assert current_version is None

    async def test_get_version_history_success(self, version_manager, mock_db_session, sample_template):
        """Test successful retrieval of version history."""
        # Create multiple versions
        versions = [
            WorkflowTemplateVersion(
                id=uuid.uuid4(),
                template_id=sample_template.id,
                version="1.0.0",
                is_current=False,
                is_deprecated=False,
                created_at=datetime(2024, 1, 1),
                changelog="Initial version",
                breaking_changes=False
            ),
            WorkflowTemplateVersion(
                id=uuid.uuid4(),
                template_id=sample_template.id,
                version="1.1.0",
                is_current=True,
                is_deprecated=False,
                created_at=datetime(2024, 2, 1),
                changelog="Added features",
                breaking_changes=False
            )
        ]
        
        # Mock template exists and version history
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = versions
        mock_execute_result2.scalars.return_value = mock_scalars_result
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        history = await version_manager.get_version_history(IndustryType.CONSULTING)
        
        assert len(history) == 2
        assert all(isinstance(v, TemplateVersionInfo) for v in history)
        assert history[0].version in ["1.0.0", "1.1.0"]
        assert history[1].version in ["1.0.0", "1.1.0"]

    async def test_get_version_history_template_not_found(self, version_manager, mock_db_session):
        """Test version history retrieval when template doesn't exist."""
        # Mock template not found
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        history = await version_manager.get_version_history(IndustryType.CONSULTING)
        
        assert history == []

    async def test_deprecate_version_success(self, version_manager, mock_db_session, sample_template):
        """Test successful version deprecation."""
        # Create a non-current version to deprecate
        version_to_deprecate = WorkflowTemplateVersion(
            id=uuid.uuid4(),
            template_id=sample_template.id,
            version="1.0.0",
            is_current=False,
            is_deprecated=False
        )
        
        # Mock template exists and version exists
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = version_to_deprecate
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        success = await version_manager.deprecate_version(IndustryType.CONSULTING, "1.0.0")
        
        assert success is True
        assert version_to_deprecate.is_deprecated is True
        mock_db_session.commit.assert_called_once()

    async def test_deprecate_version_current_version(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test deprecation of current version (should fail)."""
        # Mock template exists and version is current
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        with pytest.raises(ValueError, match="Cannot deprecate current version"):
            await version_manager.deprecate_version(IndustryType.CONSULTING, "1.0.0")

    async def test_deprecate_version_not_found(self, version_manager, mock_db_session, sample_template):
        """Test deprecation of non-existent version."""
        # Mock template exists but version doesn't exist
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        success = await version_manager.deprecate_version(IndustryType.CONSULTING, "1.0.0")
        
        assert success is False

    async def test_migrate_template_definition(self, version_manager):
        """Test template definition migration."""
        old_definition = {"field1": "value1", "field2": "value2"}
        
        migrated = await version_manager.migrate_template_definition(
            old_definition, "1.0.0", "1.1.0"
        )
        
        # Should preserve original data
        assert migrated["field1"] == "value1"
        assert migrated["field2"] == "value2"
        
        # Should add migration metadata
        assert "_migration_info" in migrated
        assert migrated["_migration_info"]["from_version"] == "1.0.0"
        assert migrated["_migration_info"]["to_version"] == "1.1.0"
        assert "migrated_at" in migrated["_migration_info"]

    async def test_get_template_definition_current(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test getting current template definition."""
        # Mock template exists and has current version
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        definition = await version_manager.get_template_definition(IndustryType.CONSULTING)
        
        assert definition == {"test": "definition"}

    async def test_get_template_definition_specific_version(self, version_manager, mock_db_session, sample_template, sample_version):
        """Test getting specific version template definition."""
        # Mock template exists and specific version exists
        mock_execute_result1 = Mock()
        mock_execute_result1.scalar_one_or_none.return_value = sample_template
        mock_execute_result2 = Mock()
        mock_execute_result2.scalar_one_or_none.return_value = sample_version
        mock_db_session.execute = AsyncMock(side_effect=[mock_execute_result1, mock_execute_result2])
        
        definition = await version_manager.get_template_definition(IndustryType.CONSULTING, "1.0.0")
        
        assert definition == {"test": "definition"}

    async def test_get_template_by_industry_found(self, version_manager, mock_db_session, sample_template):
        """Test getting template by industry when found."""
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = sample_template
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)

        result = await version_manager._get_template_by_industry(IndustryType.CONSULTING)
        
        assert result == sample_template
        mock_db_session.execute.assert_called_once()

    async def test_get_template_definition_not_found(self, version_manager, mock_db_session):
        """Test getting template definition when template not found."""
        # Mock template not found
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_execute_result)
        
        definition = await version_manager.get_template_definition(IndustryType.CONSULTING)
        
        assert definition is None

    def test_validate_version_format_valid(self, version_manager):
        """Test version format validation with valid versions."""
        # Should not raise exception
        version_manager._validate_version_format("1.0.0")
        version_manager._validate_version_format("2.1.3")
        version_manager._validate_version_format("0.1.0")

    def test_validate_version_format_invalid(self, version_manager):
        """Test version format validation with invalid versions."""
        with pytest.raises(ValueError, match="Invalid version format"):
            version_manager._validate_version_format("invalid")
        
        with pytest.raises(ValueError, match="Invalid version format"):
            version_manager._validate_version_format("")
        
        with pytest.raises(ValueError, match="Invalid version format"):
            version_manager._validate_version_format("1.0.0-")

    def test_is_version_newer(self, version_manager):
        """Test version comparison logic."""
        assert version_manager._is_version_newer("1.1.0", "1.0.0") is True
        assert version_manager._is_version_newer("2.0.0", "1.9.9") is True
        assert version_manager._is_version_newer("1.0.1", "1.0.0") is True
        
        assert version_manager._is_version_newer("1.0.0", "1.0.0") is False
        assert version_manager._is_version_newer("1.0.0", "1.1.0") is False
        assert version_manager._is_version_newer("0.9.0", "1.0.0") is False

    def test_is_version_newer_invalid_format(self, version_manager):
        """Test version comparison with invalid formats."""
        assert version_manager._is_version_newer("invalid", "1.0.0") is False
        assert version_manager._is_version_newer("1.0.0", "invalid") is False


class TestTemplateVersionInfo:
    """Test suite for TemplateVersionInfo model."""

    def test_template_version_info_creation(self):
        """Test TemplateVersionInfo model creation."""
        version_info = TemplateVersionInfo(
            id=uuid.uuid4(),
            template_id=uuid.uuid4(),
            version="1.0.0",
            is_current=True,
            is_deprecated=False,
            created_at=datetime.utcnow(),
            changelog="Initial version",
            breaking_changes=False,
            migration_notes="No migration needed"
        )
        
        assert version_info.version == "1.0.0"
        assert version_info.is_current is True
        assert version_info.is_deprecated is False
        assert version_info.changelog == "Initial version"
        assert version_info.breaking_changes is False


class TestTemplateVersionCreate:
    """Test suite for TemplateVersionCreate model."""

    def test_template_version_create_valid(self):
        """Test TemplateVersionCreate model with valid data."""
        version_create = TemplateVersionCreate(
            version="1.1.0",
            changelog="Added new features",
            breaking_changes=True,
            migration_notes="Update configuration",
            template_definition={"field": "value"}
        )
        
        assert version_create.version == "1.1.0"
        assert version_create.changelog == "Added new features"
        assert version_create.breaking_changes is True
        assert version_create.migration_notes == "Update configuration"
        assert version_create.template_definition == {"field": "value"}

    def test_template_version_create_minimal(self):
        """Test TemplateVersionCreate model with minimal required data."""
        version_create = TemplateVersionCreate(
            version="1.0.0",
            template_definition={"field": "value"}
        )
        
        assert version_create.version == "1.0.0"
        assert version_create.template_definition == {"field": "value"}
        assert version_create.changelog is None
        assert version_create.breaking_changes is False
        assert version_create.migration_notes is None


class TestInitializeDefaultTemplates:
    """Test suite for initialize_default_templates function."""

    async def test_initialize_default_templates(self):
        """Test initialization of default templates."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        # Mock that no templates exist initially - return None for all execute calls
        mock_execute_result = Mock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_execute_result)
        
        # Mock flush and commit
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        
        await initialize_default_templates(mock_session)
        
        # Should attempt to create templates for available industry types only (5 implemented)
        # Verify database operations were called - each template creates 2 objects (template + version)
        available_count = len(IndustryTemplateFactory.list_available_industries())
        expected_add_calls = available_count * 2  # template + version for each industry
        assert mock_session.add.call_count == expected_add_calls
        assert mock_session.commit.call_count >= available_count
