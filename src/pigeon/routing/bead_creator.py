"""Creates bead issues for processed specs."""

import logging
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BeadCreator:
    """Creates bead issues in target projects."""

    def __init__(self, hentown_root: Path):
        """Initialize bead creator.

        Args:
            hentown_root: Path to hentown repository root.
        """
        self.hentown_root = hentown_root
        self._check_beads_available()

    def _check_beads_available(self) -> bool:
        """Check if beads CLI is available."""
        try:
            subprocess.run(
                ["bd", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            logger.info("Beads CLI available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Beads CLI not available - bead creation will be skipped")
            return False

    def create(
        self,
        project_path: Path,
        spec_file: Path,
        title: str,
        description: Optional[str] = None,
    ) -> Optional[str]:
        """Create a bead issue for a processed spec.

        Args:
            project_path: Path to target project.
            spec_file: Path to processed spec file.
            title: Issue title.
            description: Optional issue description.

        Returns:
            Bead issue ID if successful, None otherwise.
        """
        if not (project_path / ".beads").exists():
            logger.debug(f"Project {project_path.name} has no .beads directory - skipping bead creation")
            return None

        if not spec_file.exists():
            logger.error(f"Spec file not found: {spec_file}")
            return None

        try:
            # Try to create bead issue
            # Note: This requires beads CLI to be installed and configured
            cmd = [
                "bd",
                "create",
                f"--title={title}",
                f"--description={description or 'Auto-generated from pigeon'}",
                "--type=task",
                "--priority=2",
            ]

            logger.debug(f"Creating bead in {project_path}: {' '.join(cmd)}")

            # Change to project directory for bead creation
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Extract bead ID from output (format: "✓ Created issue: XXXXX")
                output = result.stdout + result.stderr
                lines = output.split("\n")
                for line in lines:
                    if "Created issue" in line or "✓" in line:
                        # Try to extract bead ID
                        parts = line.split()
                        for part in parts:
                            if part.startswith("hentown-") or part.startswith("pigeon-"):
                                logger.info(f"Created bead: {part}")
                                return part

                logger.info(f"Bead created in {project_path.name} (exact ID unknown)")
                return "created"

            else:
                logger.error(f"Failed to create bead: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Bead creation timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to create bead: {e}", exc_info=True)
            return None

    def create_from_spec(
        self,
        spec_file: Path,
        project_path: Path,
    ) -> Optional[str]:
        """Create a bead from a processed spec file.

        Args:
            spec_file: Path to processed spec file.
            project_path: Path to target project.

        Returns:
            Bead issue ID if successful, None otherwise.
        """
        # Generate title from spec filename
        title = f"Process: {spec_file.stem}"

        # Read first line of spec as description
        try:
            with open(spec_file, "r") as f:
                first_line = f.readline().strip()
            description = first_line[:100] if first_line else "Auto-generated from pigeon"
        except Exception:
            description = "Auto-generated from pigeon"

        return self.create(
            project_path=project_path,
            spec_file=spec_file,
            title=title,
            description=description,
        )
