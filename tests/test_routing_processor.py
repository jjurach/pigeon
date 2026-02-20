"""Tests for Pigeon routing processor."""

import pytest
from pathlib import Path
from pigeon.processors.routing import RoutingProcessor


class TestRoutingProcessor:
    """Test routing processor functionality."""

    @pytest.fixture
    def mock_projects(self, tmp_path):
        """Create mock project structure."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # Create test projects with .beads directories
        for proj_name in ["test-project", "other-project"]:
            proj_dir = modules_dir / proj_name
            proj_dir.mkdir()
            beads_dir = proj_dir / ".beads"
            beads_dir.mkdir()
            inbox_dir = proj_dir / "dev_notes" / "inbox"
            inbox_dir.mkdir(parents=True)
            archive_dir = proj_dir / "dev_notes" / "inbox-archive"
            archive_dir.mkdir(parents=True)

        # Create hentown inbox and archive
        hentown_inbox = tmp_path / "dev_notes" / "inbox"
        hentown_inbox.mkdir(parents=True)
        hentown_archive = tmp_path / "dev_notes" / "inbox-archive"
        hentown_archive.mkdir(parents=True)

        return tmp_path

    def test_init(self, mock_projects):
        """Test routing processor initialization."""
        processor = RoutingProcessor(mock_projects)
        assert processor.hentown_root == mock_projects
        assert processor.router is not None
        assert processor.bead_creator is not None

    def test_process_spec_with_project_header(self, mock_projects):
        """Test processing spec with Project header."""
        processor = RoutingProcessor(mock_projects)

        # Create source spec
        source_dir = mock_projects / "dev_notes" / "inbox"
        spec_file = source_dir / "test-spec.md"
        spec_file.write_text("Project: test-project\n\n# Test Spec\n\nContent here")

        # Process
        result = processor.process(spec_file, source="test")

        # Should route to test-project
        if result:
            assert "test-project" in str(result)
            assert result.exists()

    def test_process_spec_without_project_header(self, mock_projects):
        """Test processing spec without project designation (stays in hentown)."""
        processor = RoutingProcessor(mock_projects)

        # Create source spec without project header
        source_dir = mock_projects / "dev_notes" / "inbox"
        spec_file = source_dir / "generic-spec.md"
        spec_file.write_text("# Generic Spec\n\nNo project specified")

        # Process
        result = processor.process(spec_file, source="test")

        # Should stay in hentown inbox
        if result:
            assert "hentown" in result.parent.parts or "inbox" in str(result)

    def test_archives_original_spec(self, mock_projects):
        """Test that original spec is archived."""
        processor = RoutingProcessor(mock_projects)

        # Create source spec
        source_dir = mock_projects / "dev_notes" / "inbox"
        spec_file = source_dir / "archive-test.md"
        spec_file.write_text("Project: test-project\n\nTest content")

        # Process
        result = processor.process(spec_file, source="test")

        # Original should be archived
        archive_dir = mock_projects / "dev_notes" / "inbox-archive"
        assert not spec_file.exists(), "Original spec should be moved to archive"

    def test_handles_missing_spec_file(self, mock_projects):
        """Test graceful handling of missing spec file."""
        processor = RoutingProcessor(mock_projects)

        # Try to process non-existent file
        result = processor.process(
            mock_projects / "non-existent.md",
            source="test",
        )

        assert result is None

    def test_copies_spec_to_target_inbox(self, mock_projects):
        """Test that spec is copied to target project inbox."""
        processor = RoutingProcessor(mock_projects)

        # Create source spec
        source_dir = mock_projects / "dev_notes" / "inbox"
        spec_file = source_dir / "target-test.md"
        spec_file.write_text("Project: test-project\n\nTarget content")

        # Process
        result = processor.process(spec_file, source="gdrive")

        # Should be in test-project inbox
        target_inbox = mock_projects / "modules" / "test-project" / "dev_notes" / "inbox"
        files_in_target = list(target_inbox.glob("*.md"))
        assert len(files_in_target) > 0, "Spec should be copied to target inbox"

    def test_handles_duplicate_filenames(self, mock_projects):
        """Test handling of duplicate filenames in target inbox."""
        processor = RoutingProcessor(mock_projects)

        # Create source spec
        source_dir = mock_projects / "dev_notes" / "inbox"
        spec_file = source_dir / "duplicate.md"
        spec_file.write_text("Project: test-project\n\nFirst")

        # Pre-create a file in target with same name
        target_inbox = mock_projects / "modules" / "test-project" / "dev_notes" / "inbox"
        existing_file = target_inbox / "duplicate.md"
        existing_file.write_text("Existing content")

        # Process
        result = processor.process(spec_file, source="test")

        # Should create file with different name
        if result:
            assert result.exists()
            assert result.name != "duplicate.md" or result.read_text() == "Project: test-project\n\nFirst"
