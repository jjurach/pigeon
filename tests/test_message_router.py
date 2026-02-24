"""Comprehensive unit tests for MessageRouter."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from pigeon.routing import MessageRouter


class TestMessageRouterInitialization:
    """Test MessageRouter initialization and project discovery."""

    @pytest.fixture
    def mock_project_setup(self, tmp_path):
        """Create a mock project structure."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj_name in ["pigeon", "hatchery", "second-voice"]:
            proj_dir = modules_dir / proj_name
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()

        return tmp_path

    def test_init_discovers_projects(self, mock_project_setup):
        """Test that MessageRouter discovers projects on init."""
        router = MessageRouter(mock_project_setup)
        projects = router.list_projects()

        assert len(projects) >= 1
        assert all(isinstance(p, str) for p in projects)

    def test_init_discovers_multiple_projects(self, mock_project_setup):
        """Test that router discovers multiple projects."""
        router = MessageRouter(mock_project_setup)
        projects = router.list_projects()

        expected = {"pigeon", "hatchery", "second-voice"}
        for proj in expected:
            assert proj in projects

    def test_list_projects_sorted(self, mock_project_setup):
        """Test that list_projects returns sorted list."""
        router = MessageRouter(mock_project_setup)
        projects = router.list_projects()

        assert projects == sorted(projects)


class TestProjectDetection:
    """Test project detection from message content."""

    @pytest.fixture
    def router_with_projects(self, tmp_path):
        """Create a router with test projects."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj_name in ["pigeon", "hatchery", "second-voice"]:
            proj_dir = modules_dir / proj_name
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()

        return MessageRouter(tmp_path)

    def test_detect_from_project_tag(self, router_with_projects, tmp_path):
        """Test project detection from 'Project:' tag."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Project: pigeon\nHello world")

        projects = router_with_projects.detect_projects(msg_file)
        assert "pigeon" in projects

    def test_detect_from_mention(self, router_with_projects, tmp_path):
        """Test project detection from @mention."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("@hatchery please review this")

        projects = router_with_projects.detect_projects(msg_file)
        assert "hatchery" in projects

    def test_detect_from_target_tag(self, router_with_projects, tmp_path):
        """Test project detection from 'Target:' tag."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Target: second-voice\nDescription here")

        projects = router_with_projects.detect_projects(msg_file)
        assert "second-voice" in projects

    def test_detect_multiple_projects(self, router_with_projects, tmp_path):
        """Test detection of multiple projects."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Project: pigeon\n@hatchery help needed")

        projects = router_with_projects.detect_projects(msg_file)
        assert "pigeon" in projects
        assert "hatchery" in projects

    def test_no_project_detected(self, router_with_projects, tmp_path):
        """Test case where no projects are detected."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Just a generic message with no project info")

        projects = router_with_projects.detect_projects(msg_file)
        assert projects == []

    def test_invalid_project_ignored(self, router_with_projects, tmp_path):
        """Test that invalid project names are ignored."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Project: nonexistent-project\n@pigeon works though")

        projects = router_with_projects.detect_projects(msg_file)
        assert "nonexistent-project" not in projects
        assert "pigeon" in projects

    def test_detect_nonexistent_file(self, router_with_projects, tmp_path):
        """Test detection with nonexistent file."""
        msg_file = tmp_path / "nonexistent.md"
        projects = router_with_projects.detect_projects(msg_file)
        assert projects == []


class TestFileParsing:
    """Test message file parsing with YAML frontmatter."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        proj_dir = modules_dir / "test"
        proj_dir.mkdir()
        return MessageRouter(tmp_path)

    def test_parse_message_with_frontmatter(self, router, tmp_path):
        """Test parsing message with YAML frontmatter."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text(
            """---
source: slack
user: testuser
slack_user_id: U12345
channel: C67890
timestamp: 2026-02-24T10:00:00
original_message: 'Original text'
---
This is the main content

More details here.
"""
        )

        metadata, content, title = router._parse_message_file(msg_file)

        assert metadata["user"] == "testuser"
        assert metadata["slack_user_id"] == "U12345"
        assert "This is the main content" in content
        assert title == "This is the main content"

    def test_parse_message_without_frontmatter(self, router, tmp_path):
        """Test parsing message without frontmatter."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Just plain content\nNo frontmatter here")

        metadata, content, title = router._parse_message_file(msg_file)

        assert metadata == {}
        assert "Just plain content" in content
        assert title == "Just plain content"

    def test_parse_extracts_title_from_first_line(self, router, tmp_path):
        """Test that title is extracted from first content line."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text(
            """---
user: testuser
---
# My Feature Request

Details about the feature.
"""
        )

        metadata, content, title = router._parse_message_file(msg_file)

        # Title should have markdown header removed
        assert "My Feature Request" in title

    def test_parse_empty_content(self, router, tmp_path):
        """Test parsing message with empty content."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("---\nuser: testuser\n---\n")

        metadata, content, title = router._parse_message_file(msg_file)

        assert metadata["user"] == "testuser"
        assert content == ""


class TestMetadataExtraction:
    """Test extraction of metadata from messages."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        return MessageRouter(tmp_path)

    def test_extract_priority_from_content(self, router):
        """Test priority extraction from content."""
        content = "This is a P2 priority task"
        priority = router._extract_priority({}, content)
        assert priority == "P2"

    def test_extract_priority_from_metadata(self, router):
        """Test priority extraction from metadata."""
        metadata = {"priority": "P1"}
        content = "Some content with P4 in it"
        priority = router._extract_priority(metadata, content)
        assert priority == "P1"

    def test_extract_priority_default(self, router):
        """Test that priority defaults to P3."""
        metadata = {}
        content = "No priority specified"
        priority = router._extract_priority(metadata, content)
        assert priority == "P3"

    def test_extract_type_feature(self, router):
        """Test type extraction for feature."""
        content = "This is a new feature request for better performance"
        issue_type = router._extract_type({}, content)
        assert issue_type == "feature"

    def test_extract_type_bug(self, router):
        """Test type extraction for bug."""
        content = "There's a bug in the login flow that needs fixing"
        issue_type = router._extract_type({}, content)
        assert issue_type == "bug"

    def test_extract_type_default(self, router):
        """Test that type defaults to task."""
        content = "Some generic work item"
        issue_type = router._extract_type({}, content)
        assert issue_type == "task"

    def test_extract_type_from_metadata(self, router):
        """Test type extraction from metadata."""
        metadata = {"type": "feature"}
        content = "Some content"
        issue_type = router._extract_type(metadata, content)
        assert issue_type == "feature"


class TestBeadDescription:
    """Test building bead descriptions with metadata."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        return MessageRouter(tmp_path)

    def test_build_description_with_metadata(self, router):
        """Test building description with all metadata."""
        desc = router._build_bead_description(
            description="Main content",
            slack_user_id="U12345",
            slack_timestamp="2026-02-24T10:00:00",
            original_message="Original text",
        )

        assert "Main content" in desc
        assert "U12345" in desc
        assert "2026-02-24T10:00:00" in desc
        assert "Original text" in desc

    def test_build_description_partial_metadata(self, router):
        """Test building description with partial metadata."""
        desc = router._build_bead_description(
            description="Content",
            slack_user_id="",
            slack_timestamp="",
            original_message="",
        )

        assert "Content" in desc
        # Should not crash with missing metadata

    def test_build_description_truncates_long_message(self, router):
        """Test that long original messages are truncated."""
        long_msg = "x" * 500
        desc = router._build_bead_description(
            description="Content",
            slack_user_id="U123",
            slack_timestamp="2026-02-24",
            original_message=long_msg,
        )

        # Should not contain the full 500 chars
        assert long_msg not in desc
        assert "..." in desc or len(desc) < len(long_msg)


class TestArchiveOperations:
    """Test message archiving functionality."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        return MessageRouter(tmp_path)

    def test_archive_message(self, router, tmp_path):
        """Test archiving a message file."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Test content")

        archive_path = router.archive_message(msg_file, reason="test-reason")

        assert archive_path.exists()
        assert not msg_file.exists()
        assert "[test-reason]_test.md" in archive_path.name

    def test_archive_message_custom_dir(self, router, tmp_path):
        """Test archiving to custom directory."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Content")
        archive_dir = tmp_path / "custom-archive"

        archive_path = router.archive_message(msg_file, archive_dir=archive_dir)

        assert archive_path.parent == archive_dir

    def test_archive_processed_file(self, router, tmp_path):
        """Test archiving a processed file with date subdirectory."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Content")

        archive_path = router.archive_processed_file(msg_file)

        assert archive_path.exists()
        assert not msg_file.exists()
        # Should be in a date-based subdirectory
        assert "/" in str(archive_path.relative_to(tmp_path / "dev_notes" / "inbox-archive"))

    def test_archive_processed_handles_duplicates(self, router, tmp_path):
        """Test that archive handles duplicate filenames."""
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir(parents=True)

        msg_file1 = tmp_path / "test1.md"
        msg_file1.write_text("Content 1")
        msg_file2 = tmp_path / "test2.md"
        msg_file2.write_text("Content 2")

        archive_path1 = router.archive_processed_file(msg_file1, archive_dir=archive_dir)
        archive_path2 = router.archive_processed_file(msg_file2, archive_dir=archive_dir)

        # Both should exist and be different
        assert archive_path1.exists()
        assert archive_path2.exists()
        assert archive_path1 != archive_path2

    def test_cleanup_old_archives(self, router, tmp_path):
        """Test cleaning up old archive files."""
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir(parents=True)

        # Create old archive directory (31 days ago)
        old_date = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
        old_dir = archive_dir / old_date
        old_dir.mkdir(parents=True)
        old_file = old_dir / "old_msg.md"
        old_file.write_text("Old content")

        # Create recent archive directory (5 days ago)
        recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        recent_dir = archive_dir / recent_date
        recent_dir.mkdir(parents=True)
        recent_file = recent_dir / "recent_msg.md"
        recent_file.write_text("Recent content")

        # Cleanup with 30-day retention
        deleted = router.cleanup_old_archives(archive_dir=archive_dir, retention_days=30)

        assert deleted >= 1
        assert not old_dir.exists()
        assert recent_dir.exists()


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        proj_dir = modules_dir / "test-project"
        proj_dir.mkdir()
        (proj_dir / ".beads").mkdir()
        return MessageRouter(tmp_path)

    def test_detect_nonexistent_file_returns_empty(self, router, tmp_path):
        """Test that detecting project for nonexistent file returns empty."""
        msg_file = tmp_path / "nonexistent.md"
        projects = router.detect_projects(msg_file)
        assert projects == []

    def test_create_bead_nonexistent_file(self, router, tmp_path):
        """Test creating bead for nonexistent file."""
        msg_file = tmp_path / "nonexistent.md"
        result = router.create_bead(msg_file, "test-project")
        assert result is None

    def test_create_bead_nonexistent_project(self, router, tmp_path):
        """Test creating bead for nonexistent project."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Content")
        result = router.create_bead(msg_file, "nonexistent-project")
        assert result is None

    def test_archive_nonexistent_file(self, router, tmp_path):
        """Test archiving nonexistent file."""
        msg_file = tmp_path / "nonexistent.md"
        archive_path = router.archive_message(msg_file)
        assert archive_path is None

    def test_route_and_create_beads_no_projects(self, router, tmp_path):
        """Test routing message with no projects detected."""
        msg_file = tmp_path / "test.md"
        msg_file.write_text("Generic message")

        results = router.route_and_create_beads(msg_file, archive_unparseable=False)

        assert results == {}
        # File should remain (not archived since archive_unparseable=False)
        assert msg_file.exists()

    def test_route_and_create_beads_nonexistent_file(self, router, tmp_path):
        """Test routing nonexistent file."""
        msg_file = tmp_path / "nonexistent.md"
        results = router.route_and_create_beads(msg_file)
        assert results == {}


class TestHighLevelWorkflow:
    """Test high-level routing and creation workflows."""

    @pytest.fixture
    def router_and_projects(self, tmp_path):
        """Create router with multiple projects."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj in ["pigeon", "hatchery"]:
            proj_dir = modules_dir / proj
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()

        return MessageRouter(tmp_path), tmp_path

    def test_route_and_create_workflow(self, router_and_projects):
        """Test complete routing and bead creation workflow."""
        router, tmp_path = router_and_projects

        msg_file = tmp_path / "test.md"
        msg_file.write_text(
            """---
source: slack
user: testuser
slack_user_id: U123
channel: C456
timestamp: 2026-02-24T10:00:00
original_message: 'Test message'
---
Project: pigeon
Feature request for better logging
"""
        )

        # This will fail at bead creation (no beads CLI), but should handle gracefully
        results = router.route_and_create_beads(
            msg_file, archive_unparseable=False, archive_successful=False
        )

        # Should have detected pigeon
        assert "pigeon" in results

    def test_partial_failure_keeps_file(self, router_and_projects):
        """Test that partial failure keeps file in inbox for retry."""
        router, tmp_path = router_and_projects

        msg_file = tmp_path / "test.md"
        msg_file.write_text("Project: pigeon\n@hatchery\nSome content")

        results = router.route_and_create_beads(
            msg_file, archive_unparseable=False, archive_successful=False
        )

        # With no beads CLI, this will fail, but the file should be kept
        if not any(results.values()):
            # On failure, file should be kept (since archive_unparseable=False)
            assert msg_file.exists()


class TestExtractKeywords:
    """Test keyword extraction for beads database queries."""

    @pytest.fixture
    def router(self, tmp_path):
        """Create a simple router."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        return MessageRouter(tmp_path)

    def test_extract_keywords_from_title(self, router):
        """Test extracting keywords from message title."""
        content = "Fix critical login bug\n\nDetails go here"
        keywords = router._extract_keywords(content)

        assert len(keywords) > 0
        assert "Fix critical login bug" in keywords

    def test_extract_keywords_limits_to_5(self, router):
        """Test that keyword extraction limits to 5."""
        content = "@project1 @project2 @project3 @project4 @project5 @project6"
        keywords = router._extract_keywords(content)

        assert len(keywords) <= 5

    def test_extract_keywords_empty_content(self, router):
        """Test keyword extraction with empty content."""
        keywords = router._extract_keywords("")
        # Should be empty or have very limited keywords
        assert len(keywords) <= 1


class TestGetProjectPath:
    """Test retrieving project paths."""

    @pytest.fixture
    def router_with_projects(self, tmp_path):
        """Create router with test projects."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj in ["pigeon", "hatchery"]:
            proj_dir = modules_dir / proj
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()

        return MessageRouter(tmp_path)

    def test_get_project_path_found(self, router_with_projects):
        """Test getting path for existing project."""
        path = router_with_projects.get_project_path("pigeon")
        assert path is not None
        assert path.name == "pigeon"
        assert (path / ".beads").exists()

    def test_get_project_path_not_found(self, router_with_projects):
        """Test getting path for nonexistent project."""
        path = router_with_projects.get_project_path("nonexistent")
        assert path is None
