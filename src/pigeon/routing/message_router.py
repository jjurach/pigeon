"""Routes messages to target projects by examining beads databases."""

import json
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict

from .submodules import SubmoduleDiscoverer

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes inbox messages to target projects based on beads database context."""

    def __init__(self, hentown_root: Path):
        """Initialize the message router.

        Args:
            hentown_root: Path to hentown repository root.
        """
        self.hentown_root = Path(hentown_root)
        self.modules_dir = self.hentown_root / "modules"
        self._discoverer = SubmoduleDiscoverer(self.hentown_root)
        self._projects = self._discoverer.get_submodules(with_beads=True)
        self._project_cache: Dict[str, Path] = {
            p["name"]: Path(p["absolute_path"]) for p in self._projects
        }

        # Fallback: also check modules directory directly (for non-submodule projects)
        if self.modules_dir.exists():
            for subdir in self.modules_dir.iterdir():
                if subdir.is_dir() and (subdir / ".beads").exists():
                    project_name = subdir.name
                    if project_name not in self._project_cache:
                        self._project_cache[project_name] = subdir
                        logger.debug(f"Discovered project from modules dir: {project_name}")

        logger.info(f"MessageRouter initialized with {len(self._project_cache)} projects")

    def detect_projects(self, message_file: Path) -> List[str]:
        """Detect target projects for a message by examining beads databases.

        Attempts multiple detection strategies:
        1. Parse explicit project metadata from message content
        2. Query beads databases to find relevant projects
        3. Fall back to hentown if no projects detected

        Args:
            message_file: Path to message file (markdown).

        Returns:
            List of project names that should receive this message.
        """
        if not message_file.exists():
            logger.warning(f"Message file not found: {message_file}")
            return []

        try:
            content = message_file.read_text()
        except Exception as e:
            logger.error(f"Failed to read message file {message_file}: {e}")
            return []

        # Strategy 1: Check for explicit project metadata
        projects = self._detect_from_metadata(content)
        if projects:
            logger.info(f"Detected projects from metadata: {projects}")
            return projects

        # Strategy 2: Query beads databases for context relevance
        projects = self._detect_from_beads_context(content)
        if projects:
            logger.info(f"Detected projects from beads context: {projects}")
            return projects

        # Strategy 3: Default to hentown if no projects detected
        logger.info("No target project detected, defaulting to hentown")
        return []

    def _detect_from_metadata(self, content: str) -> List[str]:
        """Detect projects from explicit metadata in message content.

        Looks for patterns like:
        - "Project: project-name"
        - "@project-name"
        - "Target: project-name"

        Args:
            content: Message content.

        Returns:
            List of detected project names.
        """
        import re

        detected = []

        # Pattern 1: "Project: name" or "project: name"
        match = re.search(r"^[Pp]roject:\s*([a-z0-9\-]+)", content, re.MULTILINE)
        if match:
            project_name = match.group(1)
            if project_name in self._project_cache:
                detected.append(project_name)
                logger.debug(f"Detected project from 'Project:' tag: {project_name}")
            else:
                logger.warning(f"Project mentioned but not found: {project_name}")

        # Pattern 2: "@project-name"
        for match in re.finditer(r"@([a-z0-9\-]+)", content):
            project_name = match.group(1)
            if project_name in self._project_cache:
                if project_name not in detected:
                    detected.append(project_name)
                    logger.debug(f"Detected project from '@' mention: {project_name}")

        # Pattern 3: "Target: name" or "Targets: names"
        match = re.search(r"^[Tt]argets?:\s*(.+)$", content, re.MULTILINE)
        if match:
            targets = match.group(1)
            for target in targets.split(","):
                project_name = target.strip().lower()
                if project_name in self._project_cache:
                    if project_name not in detected:
                        detected.append(project_name)
                        logger.debug(f"Detected project from 'Target:' tag: {project_name}")

        return detected

    def _detect_from_beads_context(self, content: str) -> List[str]:
        """Detect projects by querying their beads databases for relevance.

        For each project with a .beads/ directory, checks if the message
        content relates to existing issues or project context.

        Args:
            content: Message content.

        Returns:
            List of detected project names.
        """
        detected = []

        # Extract potential keywords from content
        keywords = self._extract_keywords(content)
        if not keywords:
            logger.debug("No keywords extracted from message content")
            return []

        logger.debug(f"Extracted keywords: {keywords}")

        # Check each project's beads database
        for project_name, project_path in self._project_cache.items():
            if not (project_path / ".beads").exists():
                continue

            # Query beads database for matching issues
            if self._query_project_context(project_path, keywords):
                detected.append(project_name)
                logger.debug(f"Message relevant to project: {project_name}")

        return detected

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from message content for beads database queries.

        Extracts first line (likely title) and any @mentions or explicit keywords.

        Args:
            content: Message content.

        Returns:
            List of keywords.
        """
        keywords = []

        # Extract first line as primary keyword
        lines = content.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # Remove markdown markers
            first_line = first_line.lstrip("#").strip()
            if first_line and len(first_line) > 3:
                keywords.append(first_line)

        # Extract @mentions (likely referring to projects)
        import re

        for match in re.finditer(r"@([a-z0-9\-]+)", content):
            keywords.append(match.group(1))

        return keywords[:5]  # Limit to 5 keywords for efficiency

    def _query_project_context(self, project_path: Path, keywords: List[str]) -> bool:
        """Query a project's beads database to check if it's relevant.

        Uses beads CLI to search for issues matching the keywords.

        Args:
            project_path: Path to project directory.
            keywords: List of keywords to search for.

        Returns:
            True if the project appears relevant, False otherwise.
        """
        if not keywords:
            return False

        try:
            # Build search query from keywords
            search_query = " OR ".join(keywords[:3])  # Limit to 3 keywords for efficiency

            # Use beads CLI to search issues (if available)
            result = subprocess.run(
                ["bd", "list", f"--filter={search_query}"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                logger.debug(f"Found matching issues in {project_path.name}")
                return True

            logger.debug(f"No matching issues in {project_path.name} for keywords: {search_query}")
            return False

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Beads CLI not available or search timed out
            logger.debug(f"Could not query beads database in {project_path.name}")
            return False
        except Exception as e:
            logger.error(f"Error querying beads database in {project_path.name}: {e}")
            return False

    def get_project_path(self, project_name: str) -> Optional[Path]:
        """Get the filesystem path for a project.

        Args:
            project_name: Name of the project.

        Returns:
            Path to project directory, or None if not found.
        """
        return self._project_cache.get(project_name)

    def list_projects(self) -> List[str]:
        """List all available projects with beads support.

        Returns:
            Sorted list of project names.
        """
        return sorted(self._project_cache.keys())
