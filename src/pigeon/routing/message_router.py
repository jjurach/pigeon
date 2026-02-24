"""Routes messages to target projects by examining beads databases."""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple

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

    def create_bead(
        self,
        message_file: Path,
        project_name: str,
    ) -> Optional[str]:
        """Create a bead issue in a project from a message file.

        Parses the message file to extract metadata and creates a bead issue
        with preserved metadata (slack_user_id, slack_timestamp, original_message).

        Args:
            message_file: Path to message file (markdown with frontmatter).
            project_name: Target project name.

        Returns:
            Bead issue ID if successful, None otherwise.
        """
        if not message_file.exists():
            logger.error(f"Message file not found: {message_file}")
            return None

        project_path = self._project_cache.get(project_name)
        if not project_path:
            logger.error(f"Project not found: {project_name}")
            return None

        if not (project_path / ".beads").exists():
            logger.debug(f"Project {project_name} has no .beads directory")
            return None

        try:
            # Parse the message file
            metadata, content, title = self._parse_message_file(message_file)

            # Extract bead creation parameters
            description = content.strip()
            priority = self._extract_priority(metadata, description)
            issue_type = self._extract_type(metadata, description)
            slack_user_id = metadata.get("slack_user_id", "")
            slack_timestamp = metadata.get("timestamp", "")
            original_message = metadata.get("original_message", "")

            # Build description with metadata
            full_description = self._build_bead_description(
                description=description,
                slack_user_id=slack_user_id,
                slack_timestamp=slack_timestamp,
                original_message=original_message,
            )

            # Create the bead
            return self._create_bead_issue(
                project_path=project_path,
                title=title,
                description=full_description,
                priority=priority,
                issue_type=issue_type,
            )

        except Exception as e:
            logger.error(f"Failed to create bead in {project_name}: {e}", exc_info=True)
            return None

    def _parse_message_file(self, message_file: Path) -> Tuple[Dict[str, str], str, str]:
        """Parse a message file with YAML frontmatter.

        Args:
            message_file: Path to message file.

        Returns:
            Tuple of (metadata_dict, content, title).
        """
        content = message_file.read_text()

        # Extract YAML frontmatter
        metadata = {}
        lines = content.split("\n")

        if lines and lines[0].strip() == "---":
            end_idx = None
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break

            if end_idx:
                # Parse YAML frontmatter
                for line in lines[1:end_idx]:
                    if ": " in line:
                        key, val = line.split(": ", 1)
                        metadata[key.strip()] = val.strip().strip("'\"")

                # Content is after the closing ---
                content_lines = lines[end_idx + 1 :]
                content = "\n".join(content_lines).strip()

        # Extract title from first line of content
        title_lines = [l.strip() for l in content.split("\n") if l.strip()]
        if title_lines:
            title = title_lines[0]
            # Remove markdown headers
            title = re.sub(r"^#+\s*", "", title)
        else:
            title = f"Message from {metadata.get('user', 'unknown')}"

        return metadata, content, title

    def _extract_priority(self, metadata: Dict[str, str], content: str) -> str:
        """Extract priority from metadata or content.

        Looks for:
        - Priority field in metadata
        - P0-P4 or priority: N pattern in content
        - Default to P3

        Args:
            metadata: Parsed metadata dict.
            content: Message content.

        Returns:
            Priority string (P0-P4).
        """
        # Check metadata first
        if "priority" in metadata:
            priority = metadata["priority"].upper()
            if priority in ["P0", "P1", "P2", "P3", "P4"]:
                return priority

        # Look for priority pattern in content
        match = re.search(r"\b(P[0-4])\b", content)
        if match:
            return match.group(1)

        # Default
        return "P3"

    def _extract_type(self, metadata: Dict[str, str], content: str) -> str:
        """Extract issue type from metadata or content.

        Looks for:
        - Type field in metadata
        - Keywords like "feature", "bug", "task" in content
        - Default to "task"

        Args:
            metadata: Parsed metadata dict.
            content: Message content.

        Returns:
            Issue type (task, feature, bug).
        """
        # Check metadata
        if "type" in metadata:
            issue_type = metadata["type"].lower()
            if issue_type in ["task", "feature", "bug"]:
                return issue_type

        # Look for keywords in content
        content_lower = content.lower()
        if re.search(r"\b(feature|enhancement)\b", content_lower):
            return "feature"
        if re.search(r"\b(bug|fix)\b", content_lower):
            return "bug"

        return "task"

    def _build_bead_description(
        self,
        description: str,
        slack_user_id: str,
        slack_timestamp: str,
        original_message: str,
    ) -> str:
        """Build the full bead description with metadata.

        Args:
            description: Message content/description.
            slack_user_id: Slack user ID of sender.
            slack_timestamp: Slack message timestamp.
            original_message: Original Slack message text.

        Returns:
            Full description with metadata appended.
        """
        lines = [description.strip()]

        # Add metadata footer
        lines.append("")
        lines.append("---")
        lines.append("**Metadata:**")

        if slack_user_id:
            lines.append(f"- Slack User: `{slack_user_id}`")
        if slack_timestamp:
            lines.append(f"- Timestamp: {slack_timestamp}")
        if original_message:
            # Escape and truncate if very long
            msg = original_message.strip("'\"")
            if len(msg) > 200:
                msg = msg[:200] + "..."
            lines.append(f"- Original Message: `{msg}`")

        return "\n".join(lines)

    def _create_bead_issue(
        self,
        project_path: Path,
        title: str,
        description: str,
        priority: str,
        issue_type: str,
    ) -> Optional[str]:
        """Create a bead issue using the beads CLI.

        Args:
            project_path: Path to project with .beads.
            title: Issue title.
            description: Issue description.
            priority: Priority level (P0-P4).
            issue_type: Issue type (task, feature, bug).

        Returns:
            Bead issue ID if successful, None otherwise.
        """
        try:
            cmd = [
                "bd",
                "create",
                f"--title={title}",
                f"--description={description}",
                f"--type={issue_type}",
                f"--priority={priority}",
            ]

            logger.debug(f"Creating bead in {project_path.name}: {' '.join(cmd[:2])}...")

            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Extract bead ID from output
                output = result.stdout + result.stderr
                for line in output.split("\n"):
                    # Look for "✓ Created issue: XXXXX" or similar
                    if "Created issue" in line or "✓" in line:
                        parts = line.split()
                        for part in parts:
                            if "-" in part and (
                                part.startswith("hentown-")
                                or part.startswith("pigeon-")
                                or any(part.startswith(p + "-") for p in self._project_cache.keys())
                            ):
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
        except FileNotFoundError:
            logger.error("Beads CLI not found")
            return None
        except Exception as e:
            logger.error(f"Failed to create bead: {e}", exc_info=True)
            return None
