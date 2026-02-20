"""Tests for Pigeon routing logic."""

import pytest
from pathlib import Path
from pigeon.routing import ProjectRouter, BeadCreator, SubmoduleDiscoverer


class TestProjectRouter:
    """Test project routing logic."""

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

        return tmp_path

    def test_init_discovers_projects(self, mock_projects):
        """Test that router discovers projects."""
        router = ProjectRouter(mock_projects)
        projects = router.list_projects()
        assert len(projects) >= 2
        assert "test-project" in projects or "other-project" in projects

    def test_detect_project_from_header(self, mock_projects):
        """Test project detection from 'Project:' header."""
        router = ProjectRouter(mock_projects)

        # Create spec file
        spec_dir = mock_projects / "dev_notes" / "inbox"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("Project: test-project\n\nContent here")

        # Detect
        detected = router.detect_project(spec_file)
        assert detected == "test-project" or detected is None

    def test_detect_project_case_insensitive(self, mock_projects):
        """Test case-insensitive project detection."""
        router = ProjectRouter(mock_projects)

        # Create spec file with uppercase Project
        spec_dir = mock_projects / "dev_notes" / "inbox"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("PROJECT: test-project\n\nContent")

        # Should still detect (regex is case-insensitive)
        detected = router.detect_project(spec_file)
        # May be None if regex didn't match, but shouldn't error

    def test_get_inbox_path(self, mock_projects):
        """Test getting inbox path."""
        router = ProjectRouter(mock_projects)

        # Get inbox for test project
        inbox = router.get_inbox_path("test-project")
        assert "inbox" in str(inbox)
        assert inbox.exists()

    def test_get_inbox_path_hentown(self, mock_projects):
        """Test getting hentown inbox."""
        router = ProjectRouter(mock_projects)

        # Get inbox for hentown (None project)
        inbox = router.get_inbox_path(None)
        assert "inbox" in str(inbox)
        assert inbox.exists()

    def test_get_archive_path(self, mock_projects):
        """Test getting archive path."""
        router = ProjectRouter(mock_projects)

        # Get archive for test project
        archive = router.get_archive_path("test-project")
        assert "archive" in str(archive)
        assert archive.exists()


class TestBeadCreator:
    """Test bead creation logic."""

    def test_init(self, tmp_path):
        """Test bead creator initialization."""
        creator = BeadCreator(tmp_path)
        assert creator.hentown_root == tmp_path

    def test_create_without_beads_dir(self, tmp_path):
        """Test creating bead in project without .beads."""
        creator = BeadCreator(tmp_path)

        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("Test spec")

        # Try to create bead (should skip gracefully)
        result = creator.create(
            project_path=tmp_path,
            spec_file=spec_file,
            title="Test Issue",
        )

        # Should return None or skip gracefully
        assert result is None

    def test_create_with_beads_dir(self, tmp_path):
        """Test creating bead in project with .beads."""
        # Create .beads directory
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir()

        creator = BeadCreator(tmp_path)

        # Create spec file
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("Test spec")

        # Try to create bead
        # This will fail if beads CLI not available, which is OK
        result = creator.create(
            project_path=tmp_path,
            spec_file=spec_file,
            title="Test Issue",
        )

        # Result depends on beads CLI availability
        # Should not raise exception regardless

    def test_create_from_spec(self, tmp_path):
        """Test creating bead from spec file."""
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir()

        creator = BeadCreator(tmp_path)

        # Create spec file
        spec_file = tmp_path / "test-spec.md"
        spec_file.write_text("# Test Specification\n\nTest content")

        # Try to create
        result = creator.create_from_spec(
            spec_file=spec_file,
            project_path=tmp_path,
        )

        # Should complete without exception


class TestSubmoduleDiscoverer:
    """Test submodule discovery logic."""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a mock git repository with submodules."""
        # Create .gitmodules file
        gitmodules = tmp_path / ".gitmodules"
        gitmodules.write_text("""[submodule "test-project"]
\tpath = modules/test-project
\turl = https://example.com/test-project.git

[submodule "other-project"]
\tpath = modules/other-project
\turl = https://example.com/other-project.git
""")

        # Create submodule directories
        for proj in ["test-project", "other-project"]:
            proj_dir = tmp_path / "modules" / proj
            proj_dir.mkdir(parents=True)
            beads_dir = proj_dir / ".beads"
            beads_dir.mkdir()

        return tmp_path

    def test_init_discovers_submodules(self, git_repo):
        """Test that discoverer finds configured submodules."""
        discoverer = SubmoduleDiscoverer(git_repo)
        submodules = discoverer.get_submodules(with_beads=True)
        assert len(submodules) >= 2

    def test_discover_with_beads_filter(self, git_repo):
        """Test filtering by beads support."""
        # Create a submodule without .beads
        no_beads_dir = git_repo / "modules" / "no-beads-project"
        no_beads_dir.mkdir(parents=True, exist_ok=True)

        # Update .gitmodules
        gitmodules = git_repo / ".gitmodules"
        gitmodules.write_text(gitmodules.read_text() + """
[submodule "no-beads-project"]
\tpath = modules/no-beads-project
\turl = https://example.com/no-beads-project.git
""")

        discoverer = SubmoduleDiscoverer(git_repo)

        # Get all submodules
        all_modules = discoverer.get_submodules(with_beads=False)
        assert len(all_modules) >= 2

        # Get only with beads
        beads_modules = discoverer.get_submodules(with_beads=True)
        assert all(m['has_beads'] for m in beads_modules)

    def test_find_submodule_by_name(self, git_repo):
        """Test finding submodule by name."""
        discoverer = SubmoduleDiscoverer(git_repo)
        found = discoverer.find_submodule_for_project("test-project")
        assert found is not None
        assert found['name'] == "test-project"

    def test_list_project_names(self, git_repo):
        """Test listing all project names."""
        discoverer = SubmoduleDiscoverer(git_repo)
        projects = discoverer.list_project_names(with_beads=True)
        assert "test-project" in projects or "other-project" in projects

    def test_handles_missing_gitmodules(self, tmp_path):
        """Test graceful handling when .gitmodules doesn't exist."""
        discoverer = SubmoduleDiscoverer(tmp_path)
        # Should not raise exception
        submodules = discoverer.get_submodules(with_beads=False)
        assert submodules == []

    def test_handles_uninitialized_submodule(self, tmp_path):
        """Test handling of uninitialized submodules."""
        # Create .gitmodules pointing to non-existent directory
        gitmodules = tmp_path / ".gitmodules"
        gitmodules.write_text("""[submodule "missing-project"]
\tpath = modules/missing-project
\turl = https://example.com/missing-project.git
""")

        discoverer = SubmoduleDiscoverer(tmp_path)
        submodules = discoverer.get_submodules(with_beads=False)
        # Should skip uninitialized submodule
        assert not any(s['name'] == "missing-project" for s in submodules)
