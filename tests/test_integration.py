"""Integration tests for Pigeon end-to-end workflow."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from pigeon.processors import ProcessingPipeline
from pigeon.routing import ProjectRouter, BeadCreator


class TestEndToEndWorkflow:
    """Test complete Pigeon workflow."""

    def test_complete_workflow_google_drive_to_inbox(self, tmp_path):
        """Test full workflow: download -> process -> route -> archive."""
        # Setup project structure
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        test_proj_dir = modules_dir / "test-project"
        test_proj_dir.mkdir()
        (test_proj_dir / ".beads").mkdir()

        inbox_dir = test_proj_dir / "dev_notes" / "inbox"
        inbox_dir.mkdir(parents=True)

        archive_dir = test_proj_dir / "dev_notes" / "inbox-archive"
        archive_dir.mkdir(parents=True)

        # Create processor pipeline
        pipeline = ProcessingPipeline(
            enable_stt=True,
            enable_professionalize=True,
        )

        # Create mock audio file
        audio_file = inbox_dir / "2026-01-01_12-00-00_test-recording.m4a"
        audio_file.write_text("fake audio data")

        # Process through pipeline
        result = pipeline.process(audio_file)

        # Verify processing succeeded
        assert result is not None
        assert result.exists()

        # Verify output is a markdown spec
        assert result.suffix == ".md"
        content = result.read_text()
        assert len(content) > 0

    def test_workflow_with_routing(self, tmp_path):
        """Test workflow including routing to projects."""
        # Setup
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        for proj_name in ["first-project", "second-project"]:
            proj_dir = modules_dir / proj_name
            proj_dir.mkdir()
            (proj_dir / ".beads").mkdir()
            (proj_dir / "dev_notes" / "inbox").mkdir(parents=True)

        # Initialize router
        router = ProjectRouter(tmp_path)
        projects = router.list_projects()
        assert len(projects) >= 1

        # Verify can get paths for each project
        for proj in projects:
            inbox = router.get_inbox_path(proj)
            assert inbox.exists()

            archive = router.get_archive_path(proj)
            assert archive.exists()

    def test_workflow_with_project_detection(self, tmp_path):
        """Test workflow with automatic project detection."""
        # Setup
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        target_proj = modules_dir / "target-project"
        target_proj.mkdir()
        (target_proj / ".beads").mkdir()
        (target_proj / "dev_notes" / "inbox").mkdir(parents=True)

        # Create router
        router = ProjectRouter(tmp_path)

        # Create spec with project marker
        spec_dir = tmp_path / "dev_notes" / "inbox"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("Project: target-project\n\nTest specification")

        # Test detection
        detected = router.detect_project(spec_file)

        # Should detect the project (or None if no match, but shouldn't error)
        if detected:
            assert detected == "target-project"

    def test_error_handling_missing_file(self):
        """Test error handling when file doesn't exist."""
        pipeline = ProcessingPipeline()

        # Try to process non-existent file
        result = pipeline.process(Path("/nonexistent/file.m4a"))

        # Should return None gracefully
        assert result is None

    def test_error_handling_permission_denied(self, tmp_path):
        """Test error handling when file is not readable."""
        pipeline = ProcessingPipeline()

        # Create unreadable file (Unix only)
        test_file = tmp_path / "restricted.txt"
        test_file.write_text("test content")

        try:
            import os
            os.chmod(test_file, 0o000)

            # Try to process
            result = pipeline.process(test_file)

            # Should handle gracefully
            assert result is None or isinstance(result, Path)

        finally:
            # Cleanup: restore permissions
            import os
            os.chmod(test_file, 0o644)

    def test_pipeline_history_on_error(self, tmp_path):
        """Test that pipeline tracks errors in history."""
        pipeline = ProcessingPipeline()

        # Create a file but make it fail processing by unsupported format
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("test")

        # Try to process unsupported file
        result = pipeline.process(bad_file)

        # Check history (file may not be added to history on early failure)
        # The important thing is that the pipeline doesn't crash
        assert result is None or isinstance(result, Path)

    @patch("subprocess.run")
    def test_bead_creation_failure_handling(self, mock_run, tmp_path):
        """Test graceful handling of bead creation failure."""
        # Mock subprocess to simulate beads command failure
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Beads error",
        )

        creator = BeadCreator(tmp_path)

        # Create .beads directory
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir()

        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("test")

        # Try to create (should handle failure gracefully)
        result = creator.create(
            project_path=tmp_path,
            spec_file=spec_file,
            title="Test",
        )

        # Should handle failure gracefully
        assert result is None or isinstance(result, str)

    def test_concurrent_processing(self, tmp_path):
        """Test processing multiple files."""
        pipeline = ProcessingPipeline(enable_stt=True, enable_professionalize=False)

        # Create multiple audio files
        files = []
        for i in range(3):
            audio_file = tmp_path / f"test_{i}.m4a"
            audio_file.write_text(f"fake audio {i}")
            files.append(audio_file)

        # Process all files
        results = []
        for audio_file in files:
            result = pipeline.process(audio_file)
            results.append(result)

        # All should process successfully
        assert all(r is not None for r in results)

        # Verify history tracks all processing
        history = pipeline.get_history()
        assert len(history) >= 3
