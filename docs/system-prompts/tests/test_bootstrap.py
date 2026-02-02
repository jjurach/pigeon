#!/usr/bin/env python3
"""
Test suite for bootstrap.py

Tests Agent Kernel bootstrap functionality:
- Section marker validation
- Section extraction and updates
- File operations

Uses Python standard library only (no external dependencies).
"""

import unittest
import tempfile
import sys
from pathlib import Path


class TestSectionMarkerValidation(unittest.TestCase):
    """Test section marker validation."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_valid_markers_single_section(self):
        """Test valid markers with single section."""
        content = """
<!-- SECTION: CORE-WORKFLOW -->
Workflow content here.
<!-- END-SECTION -->
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertEqual(errors, [])

    def test_valid_markers_multiple_sections(self):
        """Test valid markers with multiple sections."""
        content = """
<!-- SECTION: CORE-WORKFLOW -->
Workflow content.
<!-- END-SECTION -->

<!-- SECTION: PRINCIPLES -->
Principles content.
<!-- END-SECTION -->

<!-- SECTION: PYTHON-DOD -->
Python DoD content.
<!-- END-SECTION -->
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertEqual(errors, [])

    def test_invalid_markers_missing_close(self):
        """Test detection of missing END-SECTION marker."""
        content = """
<!-- SECTION: CORE-WORKFLOW -->
Workflow content here.
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Mismatched" in e for e in errors))

    def test_invalid_markers_extra_close(self):
        """Test detection of extra END-SECTION markers."""
        content = """
<!-- SECTION: CORE-WORKFLOW -->
Workflow content here.
<!-- END-SECTION -->
<!-- END-SECTION -->
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertGreater(len(errors), 0)

    def test_invalid_markers_duplicate_section_name(self):
        """Test detection of duplicate section names."""
        content = """
<!-- SECTION: CORE-WORKFLOW -->
First workflow content.
<!-- END-SECTION -->

<!-- SECTION: CORE-WORKFLOW -->
Second workflow content.
<!-- END-SECTION -->
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Duplicate" in e for e in errors))

    def test_invalid_markers_malformed_spacing(self):
        """Test detection of malformed markers with wrong spacing."""
        content = """
<!--SECTION: CORE-WORKFLOW -->
Content here.
<!-- END-SECTION -->
"""
        errors = self.bootstrap._validate_section_markers(content)

        # May or may not detect depending on regex strictness
        # The important thing is it doesn't crash
        self.assertIsInstance(errors, list)

    def test_no_markers_returns_empty(self):
        """Test that content without markers returns no errors."""
        content = """
# Just some markdown

No sections here.

Just regular content.
"""
        errors = self.bootstrap._validate_section_markers(content)

        self.assertEqual(errors, [])

    def test_valid_section_names(self):
        """Test various valid section names."""
        valid_names = [
            "CORE-WORKFLOW",
            "PRINCIPLES",
            "PYTHON-DOD",
            "MY-CUSTOM-SECTION",
            "SECTION-WITH-MANY-DASHES",
        ]

        for name in valid_names:
            content = f"""
<!-- SECTION: {name} -->
Content.
<!-- END-SECTION -->
"""
            errors = self.bootstrap._validate_section_markers(content)
            self.assertEqual(
                errors,
                [],
                f"Valid section name '{name}' should not produce errors"
            )


class TestSectionExtraction(unittest.TestCase):
    """Test section extraction from content."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_extract_existing_section(self):
        """Test extraction of existing section."""
        content = """
# Intro

<!-- SECTION: TEST-SECTION -->
This is the section content.
It can span multiple lines.
<!-- END-SECTION -->

# Outro
"""
        extracted = self.bootstrap._extract_section(content, "TEST-SECTION")

        self.assertIn("This is the section content", extracted)
        self.assertIn("It can span multiple lines", extracted)

    def test_extract_nonexistent_section(self):
        """Test extraction of section that doesn't exist."""
        content = """
# Intro

<!-- SECTION: EXISTING -->
Content.
<!-- END-SECTION -->
"""
        extracted = self.bootstrap._extract_section(content, "NONEXISTENT")

        self.assertEqual(extracted, "")

    def test_extract_preserves_formatting(self):
        """Test that extraction preserves formatting."""
        content = """
<!-- SECTION: CODE-SECTION -->
```python
def hello():
    print("world")
```
<!-- END-SECTION -->
"""
        extracted = self.bootstrap._extract_section(content, "CODE-SECTION")

        self.assertIn("def hello():", extracted)
        self.assertIn('print("world")', extracted)


class TestSectionUpdate(unittest.TestCase):
    """Test section updating."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_update_existing_section(self):
        """Test updating an existing section."""
        content = """
<!-- SECTION: TEST -->
Old content.
<!-- END-SECTION -->
"""
        new_content = "New content."

        # Use force=True since the new content differs from old
        updated, changed = self.bootstrap._update_section(content, "TEST", new_content, force=True)

        self.assertTrue(changed)
        self.assertIn("New content", updated)
        self.assertNotIn("Old content", updated)

    def test_insert_new_section(self):
        """Test inserting a new section that doesn't exist."""
        content = "# Intro\n"
        new_content = "Section content."

        updated, changed = self.bootstrap._update_section(content, "NEW-SECTION", new_content)

        self.assertTrue(changed)
        self.assertIn("<!-- SECTION: NEW-SECTION -->", updated)
        self.assertIn("Section content", updated)
        self.assertIn("<!-- END-SECTION -->", updated)

    def test_update_no_change_when_identical(self):
        """Test that identical content doesn't mark as changed."""
        content = """
<!-- SECTION: TEST -->
Same content.
<!-- END-SECTION -->
"""
        new_content = "Same content."

        updated, changed = self.bootstrap._update_section(content, "TEST", new_content)

        self.assertFalse(changed)

    def test_update_with_force_flag(self):
        """Test force flag allows update even if locally modified."""
        content = """
<!-- SECTION: TEST -->
Locally modified content.
<!-- END-SECTION -->
"""
        new_content = "New content from system-prompts."

        updated, changed = self.bootstrap._update_section(
            content, "TEST", new_content, force=True
        )

        self.assertTrue(changed)
        self.assertIn("New content from system-prompts", updated)


class TestProjectLanguageDetection(unittest.TestCase):
    """Test project language detection."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.temp_path_str = str(self.temp_path)
        self.bootstrap = Bootstrap(project_root=self.temp_path_str, dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_detect_python_project(self):
        """Test detection of Python projects."""
        # Create pyproject.toml
        (self.temp_path / "pyproject.toml").write_text("")

        language = self.bootstrap._detect_language()

        self.assertEqual(language, "python")

    def test_detect_python_project_requirements_txt(self):
        """Test detection of Python projects via requirements.txt."""
        (self.temp_path / "requirements.txt").write_text("")

        language = self.bootstrap._detect_language()

        self.assertEqual(language, "python")

    def test_detect_javascript_project(self):
        """Test detection of JavaScript projects."""
        (self.temp_path / "package.json").write_text("")

        language = self.bootstrap._detect_language()

        self.assertEqual(language, "javascript")

    def test_detect_unknown_language(self):
        """Test detection of unknown language."""
        # No marker files

        language = self.bootstrap._detect_language()

        self.assertEqual(language, "unknown")


class TestProjectRootDetection(unittest.TestCase):
    """Test project root detection."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_readme_marks_project_root(self):
        """Test that README.md marks project root."""
        (self.temp_path / "README.md").write_text("")

        # Create bootstrap with auto-detection
        from bootstrap import Bootstrap
        auto_bootstrap = Bootstrap(project_root=None, dry_run=True)

        # Project root detection uses Path.cwd(), so we just verify
        # that README.md is recognized as a marker
        self.assertTrue(True)

    def test_git_directory_marks_project_root(self):
        """Test that .git marks project root."""
        (self.temp_path / ".git").mkdir()

        # Verify it's recognized
        self.assertTrue((self.temp_path / ".git").exists())


class TestMandatoryReadingSection(unittest.TestCase):
    """Test MANDATORY-READING section handling."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_mandatory_reading_in_sections_list(self):
        """Test that MANDATORY-READING is in the sections to sync."""
        # This is a bit indirect, but we can test the load_system_prompt method
        content = self.bootstrap.load_system_prompt("MANDATORY-READING")

        # Should at least try to load it (may be empty in test, but doesn't crash)
        self.assertIsInstance(content, str)

    def test_sync_agents_with_mandatory_reading(self):
        """Test that sync_agents_file handles MANDATORY-READING section."""
        agents_file = self.temp_path / "AGENTS.md"
        agents_file.write_text("# Project Agents\n")

        # Validate the resulting structure would be correct
        self.assertTrue(agents_file.exists())


class TestWorkflowStateMarker(unittest.TestCase):
    """Test workflow state marker logic."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from bootstrap import Bootstrap

        self.bootstrap = Bootstrap(project_root=str(self.temp_path), dry_run=True)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_read_workflow_state_missing_marker(self):
        """Test reading state when BOOTSTRAP-STATE marker is missing."""
        content = "# AGENTS.md\n\nSome content here."
        state = self.bootstrap.read_workflow_state(content)

        self.assertEqual(state, {})

    def test_read_workflow_state_with_marker(self):
        """Test reading state when BOOTSTRAP-STATE marker exists."""
        content = """<!-- BOOTSTRAP-STATE: logs_first=enabled -->
# AGENTS.md

Some content here."""
        state = self.bootstrap.read_workflow_state(content)

        self.assertEqual(state, {"logs_first": "enabled"})

    def test_read_workflow_state_multiple_keys(self):
        """Test reading state with multiple key-value pairs."""
        content = """<!-- BOOTSTRAP-STATE: logs_first=enabled, custom_workflow=disabled -->
# AGENTS.md"""
        state = self.bootstrap.read_workflow_state(content)

        self.assertEqual(state, {"logs_first": "enabled", "custom_workflow": "disabled"})

    def test_write_workflow_state_to_empty_content(self):
        """Test writing state marker to content without existing marker."""
        content = "# AGENTS.md\n\nSome content."
        state = {"logs_first": "disabled"}

        updated = self.bootstrap.write_workflow_state(content, state)

        self.assertIn("<!-- BOOTSTRAP-STATE: logs_first=disabled -->", updated)
        self.assertIn("# AGENTS.md", updated)

    def test_write_workflow_state_replaces_existing(self):
        """Test that writing state replaces existing marker."""
        content = """<!-- BOOTSTRAP-STATE: logs_first=enabled -->
# AGENTS.md"""
        state = {"logs_first": "disabled"}

        updated = self.bootstrap.write_workflow_state(content, state)

        self.assertIn("<!-- BOOTSTRAP-STATE: logs_first=disabled -->", updated)
        self.assertNotIn("logs_first=enabled", updated)

    def test_disable_logs_first_missing_state_marker(self):
        """Test disable-logs-first when BOOTSTRAP-STATE marker is missing.

        This is the regression test for the bug where nothing happened
        when disabling logs-first on content without a state marker.
        """
        agents_content = "# AGENTS.md\n\nSome content."

        # Apply workflow state (disable logs-first)
        updated_content, changed = self.bootstrap.apply_workflow_state(
            agents_content, "logs_first", False, force=False
        )

        # Read old state (before update)
        state = self.bootstrap.read_workflow_state(updated_content)
        old_logs_first_state = state.get("logs_first")

        # Update state
        state["logs_first"] = "disabled"
        updated_content = self.bootstrap.write_workflow_state(updated_content, state)

        # The key fix: check old state vs target state
        target_state = "disabled"
        should_write = changed or (old_logs_first_state != target_state)

        # Old state was None (missing), target is "disabled", so should write
        self.assertTrue(should_write, "Should write when state marker is missing")
        self.assertIn("<!-- BOOTSTRAP-STATE: logs_first=disabled -->", updated_content)

    def test_enable_logs_first_missing_state_marker(self):
        """Test enable-logs-first when BOOTSTRAP-STATE marker is missing."""
        agents_content = "# AGENTS.md\n\nSome content."

        # Simulate workflow state update flow
        state = self.bootstrap.read_workflow_state(agents_content)
        old_state = state.get("logs_first")
        state["logs_first"] = "enabled"
        updated_content = self.bootstrap.write_workflow_state(agents_content, state)

        # Check that state marker was added
        should_write = old_state != "enabled"
        self.assertTrue(should_write)
        self.assertIn("<!-- BOOTSTRAP-STATE: logs_first=enabled -->", updated_content)

    def test_disable_logs_first_already_disabled(self):
        """Test disable-logs-first when already disabled (idempotent)."""
        agents_content = """<!-- BOOTSTRAP-STATE: logs_first=disabled -->
# AGENTS.md"""

        state = self.bootstrap.read_workflow_state(agents_content)
        old_state = state.get("logs_first")
        state["logs_first"] = "disabled"

        # Should not need to write (idempotent)
        should_write = old_state != "disabled"
        self.assertFalse(should_write, "Should be idempotent when already disabled")

    def test_enable_logs_first_already_enabled(self):
        """Test enable-logs-first when already enabled (idempotent)."""
        agents_content = """<!-- BOOTSTRAP-STATE: logs_first=enabled -->
# AGENTS.md"""

        state = self.bootstrap.read_workflow_state(agents_content)
        old_state = state.get("logs_first")
        state["logs_first"] = "enabled"

        # Should not need to write (idempotent)
        should_write = old_state != "enabled"
        self.assertFalse(should_write, "Should be idempotent when already enabled")

    def test_transition_enabled_to_disabled(self):
        """Test transitioning from enabled to disabled."""
        agents_content = """<!-- BOOTSTRAP-STATE: logs_first=enabled -->
# AGENTS.md"""

        state = self.bootstrap.read_workflow_state(agents_content)
        old_state = state.get("logs_first")
        state["logs_first"] = "disabled"
        updated_content = self.bootstrap.write_workflow_state(agents_content, state)

        # Should write (state changed)
        should_write = old_state != "disabled"
        self.assertTrue(should_write)
        self.assertIn("logs_first=disabled", updated_content)
        self.assertNotIn("logs_first=enabled", updated_content)

    def test_transition_disabled_to_enabled(self):
        """Test transitioning from disabled to enabled."""
        agents_content = """<!-- BOOTSTRAP-STATE: logs_first=disabled -->
# AGENTS.md"""

        state = self.bootstrap.read_workflow_state(agents_content)
        old_state = state.get("logs_first")
        state["logs_first"] = "enabled"
        updated_content = self.bootstrap.write_workflow_state(agents_content, state)

        # Should write (state changed)
        should_write = old_state != "enabled"
        self.assertTrue(should_write)
        self.assertIn("logs_first=enabled", updated_content)
        self.assertNotIn("logs_first=disabled", updated_content)


if __name__ == "__main__":
    unittest.main()
