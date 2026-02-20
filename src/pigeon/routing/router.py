"""Project detection and routing logic for Pigeon."""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict

from .submodules import SubmoduleDiscoverer

logger = logging.getLogger(__name__)


class ProjectRouter:
    """Routes processed specs to target projects based on content."""

    def __init__(self, hentown_root: Path):
        """Initialize router.

        Args:
            hentown_root: Path to hentown repository root.
        """
        self.hentown_root = Path(hentown_root)
        self.modules_dir = self.hentown_root / "modules"
        self.cache: Dict[str, Path] = {}
        self._discoverer = SubmoduleDiscoverer(self.hentown_root)
        self._discover_projects()

    def _discover_projects(self) -> None:
        """Discover available projects with beads support.

        Uses git submodule discovery to find projects.
        Falls back to directory scanning if submodule discovery fails.
        """
        # First try submodule discovery
        submodules = self._discoverer.get_submodules(with_beads=True)
        for submodule in submodules:
            project_path = Path(submodule['absolute_path'])
            if project_path.exists():
                self.cache[submodule['name']] = project_path
                logger.debug(f"Discovered project from submodule: {submodule['name']}")

        # Fallback: also check modules directory directly (for non-submodule projects)
        if self.modules_dir.exists():
            for subdir in self.modules_dir.iterdir():
                if subdir.is_dir() and (subdir / ".beads").exists():
                    project_name = subdir.name
                    if project_name not in self.cache:  # Don't override submodule discovery
                        self.cache[project_name] = subdir
                        logger.debug(f"Discovered project from modules dir: {project_name}")

        logger.info(f"Discovered {len(self.cache)} projects with beads support")

    def detect_project(self, file_path: Path) -> Optional[str]:
        """Detect target project from spec file content.

        Looks for patterns like:
        - "Project: project-name"
        - "@project-name"
        - First submodule mentioned in content

        Args:
            file_path: Path to processed spec file.

        Returns:
            Project name if detected, None otherwise.
        """
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "r") as f:
                content = f.read(500)  # Read first 500 chars

            # Pattern 1: "Project: name"
            match = re.search(r"[Pp]roject:\s*([a-z0-9\-]+)", content)
            if match:
                project_name = match.group(1)
                if project_name in self.cache:
                    logger.info(f"Detected project from 'Project:' tag: {project_name}")
                    return project_name
                else:
                    logger.warning(f"Project not found: {project_name}")

            # Pattern 2: "@project-name"
            match = re.search(r"@([a-z0-9\-]+)", content)
            if match:
                project_name = match.group(1)
                if project_name in self.cache:
                    logger.info(f"Detected project from '@' mention: {project_name}")
                    return project_name

            # Pattern 3: Check if file path contains project name
            for proj_name in self.cache.keys():
                if proj_name in file_path.name:
                    logger.info(f"Detected project from filename: {proj_name}")
                    return proj_name

            logger.info(f"No project detected in {file_path.name}")
            return None

        except Exception as e:
            logger.error(f"Error detecting project from {file_path}: {e}")
            return None

    def get_inbox_path(self, project_name: Optional[str]) -> Path:
        """Get inbox directory for a project.

        Args:
            project_name: Name of project, or None for hentown.

        Returns:
            Path to project's inbox directory.
        """
        if project_name and project_name in self.cache:
            project_path = self.cache[project_name]
        else:
            project_path = self.hentown_root

        inbox_path = project_path / "dev_notes" / "inbox"
        inbox_path.mkdir(parents=True, exist_ok=True)
        return inbox_path

    def get_archive_path(self, project_name: Optional[str]) -> Path:
        """Get archive directory for a project.

        Args:
            project_name: Name of project, or None for hentown.

        Returns:
            Path to project's archive directory.
        """
        if project_name and project_name in self.cache:
            project_path = self.cache[project_name]
        else:
            project_path = self.hentown_root

        archive_path = project_path / "dev_notes" / "inbox-archive"
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def list_projects(self) -> List[str]:
        """List all available projects.

        Returns:
            List of project names.
        """
        return sorted(self.cache.keys())
