"""End-to-end integration tests for the full Pigeon pipeline.

Tests cover:
1. Message ingestion → markdown conversion → routing → bead creation
2. Full workflow from Slack Socket Mode event to project beads
3. Error scenarios and recovery paths
4. Multi-project routing and bead creation
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from pigeon.slack_message_converter import SlackMessageConverter
from pigeon.routing import MessageRouter, InboxRouterDaemon


class TestFullPipelineIntegration:
    """Test complete message pipeline from ingestion to bead creation."""

    @pytest.fixture
    def setup_with_projects(self, tmp_path):
        """Set up hentown with multiple projects."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj in ["pigeon", "hatchery"]:
            proj_dir = modules_dir / proj
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()

        inbox_dir = tmp_path / "dev_notes" / "inbox"
        attachments_dir = tmp_path / "attachments"

        web_client = Mock()
        web_client.token = "xoxb-test-token"

        converter = SlackMessageConverter(
            inbox_dir=inbox_dir,
            attachments_dir=attachments_dir,
            web_client=web_client,
        )
        router = MessageRouter(tmp_path)
        daemon = InboxRouterDaemon(tmp_path, poll_interval=1)

        return {
            "tmp_path": tmp_path,
            "converter": converter,
            "router": router,
            "daemon": daemon,
            "inbox_dir": inbox_dir,
            "attachments_dir": attachments_dir,
        }

    def test_pipeline_simple_message_conversion_and_routing(self, setup_with_projects):
        """Test simple message: conversion → routing → bead creation."""
        setup = setup_with_projects

        # Step 1: Simulate Slack Socket Mode message event
        slack_event = {
            "type": "message",
            "user": "U123",
            "text": "Project: pigeon\nNew feature request for logging",
            "ts": "1.0",
            "channel": "C456",
        }

        # Step 2: Convert to markdown
        markdown_path = setup["converter"].convert(slack_event)
        assert markdown_path is not None
        assert markdown_path.exists()

        # Step 3: Router detects project
        projects = setup["router"].detect_projects(markdown_path)
        assert "pigeon" in projects

        # Step 4: Route and create beads
        with patch.object(setup["router"], "_create_bead_issue") as mock_create:
            mock_create.return_value = "pigeon-test123"

            results = setup["router"].route_and_create_beads(
                markdown_path, archive_unparseable=False, archive_successful=False
            )

            assert "pigeon" in results
            mock_create.assert_called_once()

    def test_pipeline_multi_project_routing(self, setup_with_projects):
        """Test message routed to multiple projects."""
        setup = setup_with_projects

        slack_event = {
            "type": "message",
            "user": "U123",
            "text": "Project: pigeon\n@hatchery please review\nNew feature idea",
            "ts": "1.0",
            "channel": "C456",
        }

        markdown_path = setup["converter"].convert(slack_event)

        # Should detect both projects
        projects = setup["router"].detect_projects(markdown_path)
        assert len(projects) == 2
        assert "pigeon" in projects
        assert "hatchery" in projects

    def test_pipeline_with_audio_attachment(self, setup_with_projects):
        """Test pipeline with audio file attachment and STT."""
        setup = setup_with_projects

        with patch("pigeon.slack_message_converter.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake audio data"
            mock_get.return_value = mock_response

            with patch("pigeon.slack_message_converter.subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Speaker: This is an important message"
                mock_result.stderr = ""
                mock_run.return_value = mock_result

                slack_event = {
                    "type": "message",
                    "user": "U123",
                    "text": "Project: pigeon\nListen to this",
                    "ts": "1.0",
                    "channel": "C456",
                    "files": [
                        {
                            "id": "F789",
                            "name": "voice.m4a",
                            "mimetype": "audio/mp4",
                            "url_private_download": "https://files.slack.com/voice.m4a",
                        }
                    ],
                }

                markdown_path = setup["converter"].convert(slack_event)
                content = markdown_path.read_text()

                # Should have transcript in content
                assert "Transcript" in content
                assert "This is an important message" in content

    def test_pipeline_metadata_preservation(self, setup_with_projects):
        """Test that metadata is preserved through the pipeline."""
        setup = setup_with_projects

        slack_event = {
            "type": "message",
            "user": "U123",
            "text": "Project: pigeon\nTest message",
            "ts": "1000.0",
            "channel": "C456",
            "thread_ts": "1000.0",
        }

        markdown_path = setup["converter"].convert(slack_event)
        content = markdown_path.read_text()

        # Check metadata preservation
        assert "slack_user_id: U123" in content
        assert "channel: C456" in content
        assert "thread_ts: 1000.0" in content
        assert "source: slack" in content

    def test_pipeline_error_handling_invalid_markdown(self, setup_with_projects):
        """Test pipeline handling of invalid/unparseable messages."""
        setup = setup_with_projects
        inbox_dir = setup["inbox_dir"]
        inbox_dir.mkdir(parents=True, exist_ok=True)

        # Create an invalid message file
        invalid_msg = inbox_dir / "invalid.md"
        invalid_msg.write_text("corrupted content without proper frontmatter")

        # Router should handle gracefully
        projects = setup["router"].detect_projects(invalid_msg)
        assert projects == []

    def test_pipeline_error_recovery_partial_failure(self, setup_with_projects):
        """Test pipeline recovery when some operations fail."""
        setup = setup_with_projects

        slack_event = {
            "type": "message",
            "user": "U123",
            "text": "Project: pigeon\n@hatchery\nMessage",
            "ts": "1.0",
            "channel": "C456",
        }

        markdown_path = setup["converter"].convert(slack_event)

        # Mock partial bead creation failure
        call_count = 0

        def mock_create_side_effect(project_path, title, description, priority, issue_type):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "pigeon-123"  # First succeeds
            else:
                return None  # Second fails

        with patch.object(
            setup["router"], "_create_bead_issue", side_effect=mock_create_side_effect
        ):
            results = setup["router"].route_and_create_beads(
                markdown_path, archive_unparseable=False, archive_successful=False
            )

            # Should have mixed results
            assert len(results) > 0

    def test_daemon_processes_inbox_messages(self, setup_with_projects):
        """Test InboxRouterDaemon processes messages in inbox."""
        setup = setup_with_projects
        daemon = setup["daemon"]

        # Create a test message in inbox
        inbox_dir = setup["inbox_dir"]
        inbox_dir.mkdir(parents=True, exist_ok=True)

        msg_file = inbox_dir / "test.md"
        msg_file.write_text(
            """---
source: slack
user: testuser
slack_user_id: U123
channel: C456
timestamp: 2026-02-24T10:00:00
---
Project: pigeon
Test message from daemon"""
        )

        with patch.object(daemon.router, "route_and_create_beads") as mock_route:
            mock_route.return_value = {"pigeon": True}

            daemon._poll_inbox()

            # Should process the message
            mock_route.assert_called_once_with(msg_file, archive_unparseable=True, archive_successful=True)
            assert "test.md" in daemon.processed_files

    def test_daemon_archives_successfully_processed(self, setup_with_projects):
        """Test that daemon processes files with archiving enabled."""
        setup = setup_with_projects
        daemon = setup["daemon"]

        inbox_dir = setup["inbox_dir"]
        inbox_dir.mkdir(parents=True, exist_ok=True)

        msg_file = inbox_dir / "success.md"
        msg_file.write_text("Project: pigeon\nContent")

        with patch.object(daemon.router, "route_and_create_beads") as mock_route:
            mock_route.return_value = {"pigeon": True}

            daemon._poll_inbox()

            # Should call route_and_create_beads with archive flags
            mock_route.assert_called_once()
            call_args = mock_route.call_args
            assert call_args[1]["archive_successful"] is True

    def test_daemon_cleanup_old_archives(self, setup_with_projects):
        """Test daemon periodic cleanup of old archives."""
        setup = setup_with_projects
        daemon = setup["daemon"]
        daemon.cleanup_interval = 0  # Force cleanup

        with patch.object(daemon.router, "cleanup_old_archives") as mock_cleanup:
            mock_cleanup.return_value = 5

            daemon._periodic_cleanup()

            mock_cleanup.assert_called_once()

    def test_full_workflow_slack_to_bead(self, setup_with_projects):
        """Test complete workflow from Slack event to bead creation."""
        setup = setup_with_projects
        inbox_dir = setup["inbox_dir"]
        inbox_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Simulate Slack event conversion
        slack_event = {
            "type": "message",
            "user": "U789",
            "text": "Project: pigeon\nImplement new dashboard feature",
            "ts": "1626.0",
            "channel": "C999",
        }

        markdown_path = setup["converter"].convert(slack_event)
        assert markdown_path.exists()

        # Step 2: Simulate routing process
        projects = setup["router"].detect_projects(markdown_path)
        assert "pigeon" in projects

        # Step 3: Route and create beads
        with patch.object(setup["router"], "_create_bead_issue") as mock_bead:
            mock_bead.return_value = "pigeon-dash-001"

            results = setup["router"].route_and_create_beads(
                markdown_path, archive_unparseable=False, archive_successful=False
            )

            assert "pigeon" in results
            assert results["pigeon"] is True


class TestIntegrationErrorScenarios:
    """Test error scenarios in the integration pipeline."""

    @pytest.fixture
    def setup(self, tmp_path):
        """Set up test environment."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        proj_dir = modules_dir / "test-proj"
        proj_dir.mkdir()
        (proj_dir / ".beads").mkdir()

        inbox_dir = tmp_path / "dev_notes" / "inbox"
        converter = SlackMessageConverter(inbox_dir=inbox_dir)
        router = MessageRouter(tmp_path)

        return {"tmp_path": tmp_path, "converter": converter, "router": router, "inbox_dir": inbox_dir}

    def test_error_missing_required_metadata(self, setup):
        """Test handling of missing required metadata."""
        setup["inbox_dir"].mkdir(parents=True, exist_ok=True)

        # Message without user info
        slack_event = {"type": "message", "text": "Orphan message", "ts": "1.0"}

        markdown_path = setup["converter"].convert(slack_event)

        # Should still create a file with defaults
        assert markdown_path is not None

    def test_error_invalid_project_reference(self, setup):
        """Test handling of invalid project references."""
        slack_event = {
            "type": "message",
            "text": "Project: nonexistent-project\nContent",
            "user": "U123",
            "ts": "1.0",
        }

        markdown_path = setup["converter"].convert(slack_event)
        projects = setup["router"].detect_projects(markdown_path)

        # Should not find invalid project
        assert "nonexistent-project" not in projects

    def test_error_beads_creation_timeout(self, setup):
        """Test handling of beads creation timeout."""
        setup["inbox_dir"].mkdir(parents=True, exist_ok=True)

        slack_event = {
            "type": "message",
            "text": "Project: test-proj\nContent",
            "user": "U123",
            "ts": "1.0",
        }

        markdown_path = setup["converter"].convert(slack_event)

        with patch("subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired("bd", 10)

            results = setup["router"].route_and_create_beads(
                markdown_path, archive_unparseable=False, archive_successful=False
            )

            # Should handle timeout gracefully
            assert isinstance(results, dict)


class TestIntegrationRecovery:
    """Test recovery mechanisms in the pipeline."""

    @pytest.fixture
    def setup_with_daemon(self, tmp_path):
        """Set up with daemon."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        proj_dir = modules_dir / "test-proj"
        proj_dir.mkdir()
        (proj_dir / ".beads").mkdir()

        daemon = InboxRouterDaemon(tmp_path, poll_interval=1)
        return {"tmp_path": tmp_path, "daemon": daemon}

    def test_daemon_recovers_from_file_error(self, setup_with_daemon):
        """Test daemon recovers when file processing fails."""
        daemon = setup_with_daemon["daemon"]
        inbox_dir = setup_with_daemon["tmp_path"] / "dev_notes" / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)

        msg_file = inbox_dir / "problematic.md"
        msg_file.write_text("Content")

        with patch.object(daemon.router, "route_and_create_beads") as mock_route:
            mock_route.side_effect = Exception("Test error")

            # Should not crash
            daemon._poll_inbox()

            # File should still be marked as processed
            assert "problematic.md" in daemon.processed_files

    def test_daemon_continues_after_partial_failure(self, setup_with_daemon):
        """Test daemon continues processing after one file fails."""
        daemon = setup_with_daemon["daemon"]
        inbox_dir = setup_with_daemon["tmp_path"] / "dev_notes" / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)

        # Create two message files
        (inbox_dir / "msg1.md").write_text("Content 1")
        (inbox_dir / "msg2.md").write_text("Content 2")

        call_count = 0

        def route_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First file failed")
            return {}

        with patch.object(daemon.router, "route_and_create_beads") as mock_route:
            mock_route.side_effect = route_side_effect

            daemon._poll_inbox()

            # Should have tried both files
            assert call_count == 2
            # Both should be marked as processed
            assert "msg1.md" in daemon.processed_files
            assert "msg2.md" in daemon.processed_files


class TestIntegrationArchiving:
    """Test archiving functionality in integration."""

    @pytest.fixture
    def setup(self, tmp_path):
        """Set up test environment."""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()
        proj_dir = modules_dir / "test-proj"
        proj_dir.mkdir()
        (proj_dir / ".beads").mkdir()

        router = MessageRouter(tmp_path)
        inbox_dir = tmp_path / "dev_notes" / "inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)

        return {"tmp_path": tmp_path, "router": router, "inbox_dir": inbox_dir}

    def test_archive_unparseable_message(self, setup):
        """Test archiving of unparseable messages."""
        msg_file = setup["inbox_dir"] / "unparseable.md"
        msg_file.write_text("No project tag or mentions")

        archive_dir = setup["tmp_path"] / "dev_notes" / "inbox-archive"

        archived = setup["router"].archive_message(msg_file, archive_dir=archive_dir, reason="no-project")

        assert archived is not None
        assert archived.exists()
        assert "[no-project]" in archived.name
        assert not msg_file.exists()

    def test_archive_processed_file_with_date_structure(self, setup):
        """Test archiving with date-based directory structure."""
        msg_file = setup["inbox_dir"] / "processed.md"
        msg_file.write_text("Content")

        archive_dir = setup["tmp_path"] / "dev_notes" / "inbox-archive"

        archived = setup["router"].archive_processed_file(msg_file, archive_dir=archive_dir)

        assert archived is not None
        assert archived.exists()
        # Should be in a date-based subdirectory
        assert "/" in str(archived.relative_to(archive_dir))
        assert not msg_file.exists()
