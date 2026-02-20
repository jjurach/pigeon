"""Git submodule discovery and enumeration for Pigeon routing."""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SubmoduleDiscoverer:
    """Discovers and caches git submodule metadata."""

    def __init__(self, root_path: Path):
        """Initialize submodule discoverer.

        Args:
            root_path: Path to git repository root (usually hentown).
        """
        self.root_path = Path(root_path)
        self.cache: Dict[str, Dict] = {}
        self._discover()

    def _discover(self) -> None:
        """Discover all configured submodules from .gitmodules file.

        Parses .gitmodules and checks which submodules have:
        - Directory initialized
        - .beads/ directory for bead support
        - dev_notes/inbox/ directory for item routing
        """
        gitmodules_path = self.root_path / ".gitmodules"

        if not gitmodules_path.exists():
            logger.warning(f"No .gitmodules file found at {gitmodules_path}")
            return

        try:
            with open(gitmodules_path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read .gitmodules: {e}")
            return

        # Parse each [submodule "name"] block, filtering comments
        lines = []
        for line in content.splitlines(keepends=True):
            if not line.lstrip().startswith('#'):
                lines.append(line)
        clean_content = ''.join(lines)

        block_pattern = re.compile(
            r'^\[submodule\s+"([^"]+)"\]\s*\n((?:[ \t]+\S.*\n?)*)',
            re.MULTILINE
        )

        for match in block_pattern.finditer(clean_content):
            submodule_name = match.group(1)
            block_body = match.group(2)

            path_match = re.search(r'path\s*=\s*(.+)', block_body)
            url_match = re.search(r'url\s*=\s*(.+)', block_body)

            if not path_match:
                continue

            submodule_path = Path(path_match.group(1).strip())
            absolute_path = self.root_path / submodule_path
            url = url_match.group(1).strip() if url_match else None

            # Check if submodule is initialized
            if not absolute_path.is_dir():
                logger.debug(f"Submodule '{submodule_name}' not initialized: {submodule_path}")
                continue

            # Check for .beads and dev_notes/inbox support
            has_beads = (absolute_path / ".beads").is_dir()
            has_inbox = (absolute_path / "dev_notes" / "inbox").is_dir()

            metadata = {
                'name': submodule_name,
                'path': str(submodule_path),
                'absolute_path': str(absolute_path),
                'url': url,
                'has_beads': has_beads,
                'has_inbox': has_inbox,
            }

            self.cache[submodule_name] = metadata
            logger.debug(
                f"Discovered submodule: {submodule_name} "
                f"(beads={has_beads}, inbox={has_inbox})"
            )

        logger.info(f"Discovered {len(self.cache)} submodules")

    def get_submodules(self, with_beads: bool = True) -> List[Dict]:
        """Get list of discovered submodules.

        Args:
            with_beads: If True, only return submodules with .beads/ directory.

        Returns:
            List of submodule metadata dictionaries.
        """
        if not with_beads:
            return list(self.cache.values())

        return [s for s in self.cache.values() if s['has_beads']]

    def find_submodule_for_project(self, project_name: str) -> Optional[Dict]:
        """Find submodule matching project name.

        Args:
            project_name: Name of project to find.

        Returns:
            Submodule metadata dict, or None if not found.
        """
        if project_name in self.cache:
            return self.cache[project_name]
        return None

    def list_project_names(self, with_beads: bool = True) -> List[str]:
        """List all project names.

        Args:
            with_beads: If True, only return projects with .beads/ directory.

        Returns:
            Sorted list of project names.
        """
        if with_beads:
            return sorted([s['name'] for s in self.cache.values() if s['has_beads']])
        return sorted(self.cache.keys())
