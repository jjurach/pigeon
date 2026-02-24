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

    def archive_message(
        self,
        message_file: Path,
        archive_dir: Optional[Path] = None,
        reason: str = "unparseable",
    ) -> Optional[Path]:
        """Archive a message file for manual review.

        Args:
            message_file: Path to message file to archive.
            archive_dir: Optional archive directory. If not provided, creates
                         a default archive directory relative to message_file.
            reason: Reason for archiving (unparseable, no-project, etc).

        Returns:
            Path to archived file, or None on error.
        """
        if not message_file.exists():
            logger.warning(f"Cannot archive: message file not found: {message_file}")
            return None

        try:
            # Determine archive directory
            if archive_dir is None:
                # Use hentown inbox-archive by default
                archive_dir = self.hentown_root / "dev_notes" / "inbox-archive"

            archive_dir.mkdir(parents=True, exist_ok=True)

            # Create archived filename with reason prefix
            original_name = message_file.name
            archive_name = f"[{reason}]_{original_name}"
            archive_path = archive_dir / archive_name

            # Copy file to archive
            archive_path.write_text(message_file.read_text())
            logger.info(f"Archived message: {original_name} → {archive_path} (reason: {reason})")

            # Delete original if archiving succeeded
            try:
                message_file.unlink()
                logger.debug(f"Deleted original message file: {message_file}")
            except Exception as e:
                logger.warning(f"Could not delete original message file {message_file}: {e}")

            return archive_path

        except Exception as e:
            logger.error(f"Failed to archive message {message_file}: {e}", exc_info=True)
            return None

    def route_and_create_beads(
        self,
        message_file: Path,
        archive_unparseable: bool = True,
    ) -> Dict[str, bool]:
        """Route a message to target projects and create beads.

        High-level workflow: detect projects, create beads in each project,
        handle errors gracefully.

        Args:
            message_file: Path to message file.
            archive_unparseable: If True, archive messages that cannot be parsed.

        Returns:
            Dict mapping project names to success/failure status.
        """
        results = {}

        # Validate file exists
        if not message_file.exists():
            logger.error(f"Message file not found: {message_file}")
            return results

        logger.info(f"Processing message: {message_file.name}")

        try:
            # Detect target projects
            projects = self.detect_projects(message_file)

            if not projects:
                logger.warning(f"No target projects detected for {message_file.name}")
                if archive_unparseable:
                    self.archive_message(message_file, reason="no-project-detected")
                return results

            logger.info(f"Detected {len(projects)} target project(s): {projects}")

            # Create beads in each project
            for project in projects:
                try:
                    logger.info(f"Creating bead in project: {project}")
                    bead_id = self.create_bead(message_file, project)

                    if bead_id:
                        logger.info(f"Successfully created bead {bead_id} in {project}")
                        results[project] = True
                    else:
                        logger.warning(f"Failed to create bead in {project}")
                        results[project] = False

                except Exception as e:
                    logger.error(f"Error creating bead in {project}: {e}", exc_info=True)
                    results[project] = False

            # Archive if all failed
            if not any(results.values()) and archive_unparseable:
                self.archive_message(message_file, reason="bead-creation-failed")

            return results

        except Exception as e:
            logger.error(
                f"Error processing message {message_file.name}: {e}",
                exc_info=True,
            )
            if archive_unparseable:
                self.archive_message(message_file, reason="processing-error")
            return results

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
            logger.error(f"Cannot create bead: message file not found: {message_file}")
            return None

        project_path = self._project_cache.get(project_name)
        if not project_path:
            logger.error(f"Cannot create bead: project not found: {project_name}")
            return None

        if not (project_path / ".beads").exists():
            logger.debug(f"Cannot create bead: project {project_name} has no .beads directory")
            return None

        try:
            logger.debug(f"Parsing message file: {message_file}")

            # Parse the message file
            try:
                metadata, content, title = self._parse_message_file(message_file)
            except Exception as e:
                logger.error(f"Failed to parse message file {message_file}: {e}")
                raise

            if not title or not title.strip():
                logger.warning(f"Message file {message_file} has empty title")
                title = f"Message from {metadata.get('user', 'unknown')}"

            logger.debug(f"Extracted title: {title}")

            # Extract bead creation parameters
            description = content.strip()
            if not description:
                logger.warning(f"Message file {message_file} has empty description")
                description = metadata.get("original_message", "No description provided")

            priority = self._extract_priority(metadata, description)
            issue_type = self._extract_type(metadata, description)
            slack_user_id = metadata.get("slack_user_id", "")
            slack_timestamp = metadata.get("timestamp", "")
            original_message = metadata.get("original_message", "")

            logger.debug(
                f"Extracted metadata: priority={priority}, type={issue_type}, "
                f"user={slack_user_id}"
            )

            # Build description with metadata
            full_description = self._build_bead_description(
                description=description,
                slack_user_id=slack_user_id,
                slack_timestamp=slack_timestamp,
                original_message=original_message,
            )

            # Create the bead
            logger.debug(f"Creating bead issue in {project_name}")
            result = self._create_bead_issue(
                project_path=project_path,
                title=title,
                description=full_description,
                priority=priority,
                issue_type=issue_type,
            )

            if result:
                logger.info(f"Successfully created bead in {project_name}: {result}")
            else:
                logger.error(f"Beads CLI returned no result for {project_name}")

            return result

        except Exception as e:
            logger.error(
                f"Failed to create bead in {project_name} from {message_file.name}: {e}",
                exc_info=True,
            )
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
            # Validate inputs
            if not title or not title.strip():
                logger.error("Cannot create bead: title is empty")
                return None

            if not issue_type in ["task", "feature", "bug"]:
                logger.warning(f"Invalid issue type: {issue_type}, defaulting to task")
                issue_type = "task"

            if not priority in ["P0", "P1", "P2", "P3", "P4"]:
                logger.warning(f"Invalid priority: {priority}, defaulting to P3")
                priority = "P3"

            cmd = [
                "bd",
                "create",
                f"--title={title}",
                f"--description={description}",
                f"--type={issue_type}",
                f"--priority={priority}",
            ]

            logger.debug(f"Creating bead in {project_path.name}: bd create ...")

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
                logger.debug(f"Beads CLI output: {output[:200]}")

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
                                logger.info(f"Beads CLI: created issue {part}")
                                return part

                logger.info(f"Bead created in {project_path.name} (exact ID not found in output)")
                return "created"

            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Beads CLI error (exit code {result.returncode}): {error_msg}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Bead creation timed out (beads CLI did not respond within 10s)")
            return None
        except FileNotFoundError:
            logger.error("Beads CLI not found in PATH - is beads installed?")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating bead: {e}", exc_info=True)
            return None
