"""Routing processor for directing specs to target projects and creating beads."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from ..routing import ProjectRouter, BeadCreator

logger = logging.getLogger(__name__)


class RoutingProcessor:
    """Routes processed specs to target projects and creates tracking beads.

    This processor:
    1. Detects which project the spec is intended for (based on content)
    2. Copies the spec to the target project's inbox
    3. Archives the original spec in hentown's inbox-archive
    4. Creates a bead issue in the target project for tracking

    Unlike other processors, this doesn't transform the file - it routes it.
    """

    def __init__(self, hentown_root: Path):
        """Initialize routing processor.

        Args:
            hentown_root: Path to hentown repository root.
        """
        self.hentown_root = Path(hentown_root)
        self.router = ProjectRouter(self.hentown_root)
        self.bead_creator = BeadCreator(self.hentown_root)
        logger.debug("Initialized RoutingProcessor")

    def process(
        self,
        spec_file: Path,
        source: str = "unknown",
    ) -> Optional[Path]:
        """Route a processed spec to its target project.

        Args:
            spec_file: Path to processed spec file (in hentown/dev_notes/inbox/).
            source: Source of the spec (gdrive, slack, etc.).

        Returns:
            Path to the routed spec file in target project inbox, or None if failed.
        """
        if not spec_file.exists():
            logger.error(f"Spec file not found: {spec_file}")
            return None

        try:
            # Detect target project
            project_name = self.router.detect_project(spec_file)
            logger.info(f"Routing {spec_file.name} -> project: {project_name or 'hentown'}")

            # Get target project paths
            if project_name and project_name in self.router.cache:
                target_project = self.router.cache[project_name]
            else:
                target_project = self.hentown_root

            target_inbox = self.router.get_inbox_path(project_name)
            target_archive = self.router.get_archive_path(project_name)

            # Copy spec to target inbox
            target_spec_path = target_inbox / spec_file.name
            if target_spec_path.exists():
                # Avoid overwriting, add counter if needed
                counter = 1
                stem = spec_file.stem
                suffix = spec_file.suffix
                while target_spec_path.exists():
                    target_spec_path = target_inbox / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.copy2(spec_file, target_spec_path)
            logger.info(f"Copied spec to {target_spec_path}")

            # Archive original in hentown
            hentown_archive = self.router.get_archive_path(None)
            archived_path = hentown_archive / spec_file.name
            if archived_path.exists():
                counter = 1
                stem = spec_file.stem
                suffix = spec_file.suffix
                while archived_path.exists():
                    archived_path = hentown_archive / f"{stem}_{counter}{suffix}"
                    counter += 1

            shutil.move(str(spec_file), str(archived_path))
            logger.info(f"Archived original to {archived_path}")

            # Create bead in target project
            bead_id = self._create_bead_for_spec(
                target_project,
                target_spec_path,
                source,
                project_name,
            )

            if bead_id:
                logger.info(f"Created bead {bead_id} for routed spec")

            return target_spec_path

        except Exception as e:
            logger.error(f"Failed to route spec {spec_file}: {e}", exc_info=True)
            return None

    def _create_bead_for_spec(
        self,
        project_path: Path,
        spec_file: Path,
        source: str,
        project_name: Optional[str],
    ) -> Optional[str]:
        """Create a bead issue for the routed spec.

        Args:
            project_path: Path to target project.
            spec_file: Path to spec file in target inbox.
            source: Source (gdrive, slack, etc.).
            project_name: Target project name.

        Returns:
            Bead issue ID, or None if creation failed or skipped.
        """
        if not (project_path / ".beads").exists():
            logger.debug(f"Project {project_path.name} has no .beads - skipping bead creation")
            return None

        # Generate title
        title = f"Process inbox item: {spec_file.stem}"

        # Generate description from first line of spec
        try:
            with open(spec_file, "r") as f:
                first_line = f.readline().strip()
            description = first_line[:100] if first_line else f"Auto-generated from pigeon ({source})"
        except Exception:
            description = f"Auto-generated from pigeon ({source})"

        # Create bead
        bead_id = self.bead_creator.create(
            project_path=project_path,
            spec_file=spec_file,
            title=title,
            description=description,
        )

        return bead_id
