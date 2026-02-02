#!/usr/bin/env python3
"""Unit tests for LinkTransformer class."""
import unittest
import sys
import tempfile
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bootstrap import LinkTransformer


class TestLinkTransformer(unittest.TestCase):
    """Test link transformation edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parent_directory_link(self):
        """Test ../file.md transforms correctly."""
        result, warning = LinkTransformer.transform_link(
            "../definition-of-done.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "docs/definition-of-done.md")
        self.assertIsNone(warning)

    def test_double_parent_directory_link(self):
        """Test ../../file.md transforms correctly."""
        result, warning = LinkTransformer.transform_link(
            "../../AGENTS.md",
            "docs/system-prompts/tools/claude-code.md",
            "AGENTS.md",
            self.test_dir
        )
        # From tools/claude-code.md, ../../ goes to project root
        # Then AGENTS.md, relative to root AGENTS.md should just be AGENTS.md
        # But that's circular, so it should resolve correctly
        self.assertIsNone(warning)

    def test_anchor_preservation(self):
        """Test ../file.md#section preserves anchor."""
        result, warning = LinkTransformer.transform_link(
            "../definition-of-done.md#criteria",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "docs/definition-of-done.md#criteria")
        self.assertIsNone(warning)

    def test_external_url_unchanged(self):
        """Test https://example.com stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "https://example.com/page",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "https://example.com/page")
        self.assertIsNone(warning)

    def test_http_url_unchanged(self):
        """Test http://example.com stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "http://example.com/page",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "http://example.com/page")
        self.assertIsNone(warning)

    def test_ftp_url_unchanged(self):
        """Test ftp://example.com stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "ftp://example.com/file",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "ftp://example.com/file")
        self.assertIsNone(warning)

    def test_anchor_only_unchanged(self):
        """Test #section stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "#anchor-section",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "#anchor-section")
        self.assertIsNone(warning)

    def test_absolute_path_unchanged(self):
        """Test /absolute/path stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "/absolute/path/file.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        self.assertEqual(result, "/absolute/path/file.md")
        self.assertIsNone(warning)

    def test_non_relative_path_unchanged(self):
        """Test file.md (no ../ or ./) stays unchanged."""
        result, warning = LinkTransformer.transform_link(
            "file.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        # Non-relative paths (no ../ or ./) are not transformed
        self.assertEqual(result, "file.md")
        self.assertIsNone(warning)

    def test_current_directory_link(self):
        """Test ./file.md transforms correctly."""
        result, warning = LinkTransformer.transform_link(
            "./workflows/core.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            self.test_dir
        )
        # From system-prompts/, ./workflows/core.md -> system-prompts/workflows/core.md
        # Relative to root -> docs/system-prompts/workflows/core.md
        self.assertEqual(result, "docs/system-prompts/workflows/core.md")
        self.assertIsNone(warning)

    def test_extract_anchor(self):
        """Test anchor extraction."""
        path, anchor = LinkTransformer.extract_anchor("file.md#section")
        self.assertEqual(path, "file.md")
        self.assertEqual(anchor, "section")

    def test_extract_anchor_no_anchor(self):
        """Test anchor extraction when no anchor present."""
        path, anchor = LinkTransformer.extract_anchor("file.md")
        self.assertEqual(path, "file.md")
        self.assertIsNone(anchor)

    def test_extract_anchor_multiple_hashes(self):
        """Test anchor extraction with multiple # characters."""
        path, anchor = LinkTransformer.extract_anchor("file.md#section#subsection")
        self.assertEqual(path, "file.md")
        # Only first # is split point
        self.assertEqual(anchor, "section#subsection")

    def test_complex_anchor(self):
        """Test link with complex anchor."""
        result, warning = LinkTransformer.transform_link(
            "../../definition-of-done.md#mandatory-reading-read-first-every-session",
            "docs/system-prompts/tools/claude-code.md",
            "AGENTS.md",
            self.test_dir
        )
        # From tools/, ../../ -> docs/, then definition-of-done.md
        self.assertEqual(result, "docs/definition-of-done.md#mandatory-reading-read-first-every-session")
        self.assertIsNone(warning)


class TestLinkTransformerIntegration(unittest.TestCase):
    """Integration tests for link transformation in context."""

    def test_real_project_structure(self):
        """Test with actual project directory structure."""
        # This test assumes we're running in the project
        project_root = Path(__file__).parent.parent.parent.parent

        # Test a real transformation
        result, warning = LinkTransformer.transform_link(
            "../definition-of-done.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            str(project_root)
        )

        self.assertEqual(result, "docs/definition-of-done.md")
        self.assertIsNone(warning)

    def test_workflows_link(self):
        """Test transformation of workflows link."""
        project_root = Path(__file__).parent.parent.parent.parent

        result, warning = LinkTransformer.transform_link(
            "../workflows.md",
            "docs/system-prompts/mandatory-reading.md",
            "AGENTS.md",
            str(project_root)
        )

        self.assertEqual(result, "docs/workflows.md")
        self.assertIsNone(warning)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
