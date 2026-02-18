#!/usr/bin/env python3
"""
Document Integrity Scanner

Automated verification of documentation correctness and consistency.
See docs/system-prompts/processes/document-integrity-scan.md for detailed process.

Checks:
1. Referential Correctness - All links point to existing files
2. Architectural Constraints - system-prompts doesn't reference back to project files
3. Reference Formatting - All file references use hyperlinks or backticks (not plain text)
4. Tool Entry Points - Entry files (CLAUDE.md, AIDER.md, etc.) are anemic format
5. Naming Conventions - Files follow established patterns
6. Directory Structure - Tool guides in correct locations
7. Coverage - All documentation relationships captured

Usage:
    python3 docscan.py                              # Run full scan
    python3 docscan.py --check broken-links         # Only broken links
    python3 docscan.py --check reference-formatting # Only reference formatting
    python3 docscan.py --check tool-entries         # Only tool entry points
    python3 docscan.py --check back-references      # Only back-references
    python3 docscan.py --verbose                    # Verbose output
    python3 docscan.py --strict                     # Fail on warnings
"""

import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

# Configuration
CONDITIONAL_MARKERS = {
    "(if present)",
    "(if exists)",
    "(optional)",
    "if this file exists",
    "if you have",
    "if your project",
}

# Safe targets from system-prompts (entry points that always exist in AGENTS.md projects)
ENTRY_POINTS = {
    "AGENTS.md",
    ".claude/CLAUDE.md",
    ".clinerules",
    ".aider.md",
    ".gemini/GEMINI.md",
}

# Directories to exclude from plain-text reference checks (transient/working documents)
TRANSIENT_DIRS = {
    "dev_notes",
    "tmp",
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
}

# Allowlisted back-references (intentional project integration links)
ALLOWED_BACK_REFERENCES = {
    "docs/system-prompts/README.md": {
        "../definition-of-done.md",
        "../workflows.md",
        "../architecture.md",
        "../implementation-reference.md",
    },
    "docs/system-prompts/mandatory-reading.md": {
        "../definition-of-done.md",
        "../mandatory.md",
        "../architecture.md",
        "../implementation-reference.md",
        "../workflows.md",
    },
    "docs/system-prompts/tips/README.md": {
        "../../definition-of-done.md",
    },
    "docs/system-prompts/tools/claude-code.md": {
        "../../definition-of-done.md",
        "../../mandatory.md",
        "../../../.claude/CLAUDE.md",
    },
    "docs/system-prompts/tools/cline.md": {
        "../../definition-of-done.md",
        "../../mandatory.md",
    },
    "docs/system-prompts/tools/gemini.md": {
        "../../definition-of-done.md",
        "../../mandatory.md",
        "../../../.gemini/GEMINI.md",
    },
    "docs/system-prompts/tools/aider.md": {
        "../../definition-of-done.md",
        "../../mandatory.md",
    },
    "docs/system-prompts/processes/close-project.md": {
        "../../definition-of-done.md",
    },
}

# Entry file line count threshold (relaxed from 20 to account for enhanced templates)
ENTRY_FILE_MAX_LINES = 40


class DocumentScanner:
    """Scan documentation for integrity issues."""

    def __init__(self, project_root: Path, options: argparse.Namespace):
        self.project_root = project_root
        self.options = options
        self.violations = []
        self._anchor_cache = {}  # Cache of file -> valid anchors

    def _extract_anchors_from_file(self, file_path: Path) -> set:
        """Extract all valid anchors from a markdown file.

        Detects:
        1. Auto-generated anchors from headings (# Heading -> #heading)
        2. Explicit anchors (# Heading {#custom-id})
        3. HTML anchors (<a id="anchor"></a>)
        """
        if file_path in self._anchor_cache:
            return self._anchor_cache[file_path]

        anchors = set()

        if not file_path.exists():
            self._anchor_cache[file_path] = anchors
            return anchors

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern 1: Explicit anchors in headings: # Heading {#custom-id}
            explicit_pattern = re.compile(r"^#+\s+.+\{#([^}]+)\}", re.MULTILINE)
            for match in explicit_pattern.finditer(content):
                anchors.add(match.group(1))

            # Pattern 2: HTML anchors: <a id="anchor"></a>
            html_pattern = re.compile(r'<a\s+id=["\']([^"\']+)["\']', re.IGNORECASE)
            for match in html_pattern.finditer(content):
                anchors.add(match.group(1))

            # Pattern 3: Auto-generated anchors from headings (# Heading -> #heading)
            # GitHub's auto-anchor generation rules:
            # 1. Convert to lowercase
            # 2. Remove punctuation except dashes
            # 3. Replace spaces with dashes
            # 4. Collapse multiple dashes
            heading_pattern = re.compile(r"^(#+)\s+([^\n{]+)", re.MULTILINE)
            for match in heading_pattern.finditer(content):
                heading_text = match.group(2).strip()

                # Check if there's an explicit anchor for this heading
                heading_start = match.start()
                heading_end = match.end()
                # Look ahead for explicit anchor on same line
                line_end = content.find('\n', heading_end)
                if line_end == -1:
                    line_end = len(content)
                rest_of_line = content[heading_end:line_end]

                if '{#' in rest_of_line:
                    # Already captured as explicit anchor
                    continue

                # Generate anchor from heading text
                # Remove markdown formatting first (like bold, italics, code)
                cleaned = re.sub(r'[*_`]', '', heading_text)
                # Remove special characters except dashes
                anchor = re.sub(r'[^\w\s-]', '', cleaned.lower())
                # Replace spaces with dashes
                anchor = re.sub(r'\s+', '-', anchor)
                # Collapse multiple dashes
                anchor = re.sub(r'-+', '-', anchor)
                # Strip leading/trailing dashes
                anchor = anchor.strip('-')

                if anchor:
                    anchors.add(anchor)

        except Exception as e:
            if self.options.verbose:
                print(f"    Warning: Could not parse anchors from {file_path}: {e}")

        self._anchor_cache[file_path] = anchors
        return anchors

    def _resolve_link_target(self, link_target: str, from_file: Path) -> Tuple[Path, str]:
        """Split a link target into file path and anchor.

        Returns (file_path, anchor) where anchor may be empty string.
        Resolves relative paths based on from_file location.
        """
        # Split on # to separate file path from anchor
        if '#' in link_target:
            file_part, anchor_part = link_target.split('#', 1)
        else:
            file_part = link_target
            anchor_part = ""

        # Resolve file path
        if file_part.startswith("/"):
            target_file = self.project_root / file_part.lstrip("/")
        elif file_part:
            target_file = (from_file.parent / file_part).resolve()
        else:
            # Just an anchor (e.g., "#section") - refers to current file
            target_file = from_file

        return target_file, anchor_part

    def run(self) -> int:
        """Execute scan and return exit code."""
        print("=" * 80)
        print("DOCUMENT INTEGRITY SCAN")
        print("=" * 80)

        if not self.options.check or "broken-links" in self.options.check:
            self._check_broken_links()

        if not self.options.check or "back-references" in self.options.check:
            self._check_back_references()

        if not self.options.check or "reference-formatting" in self.options.check:
            self._check_reference_formatting()

        if not self.options.check or "tool-entries" in self.options.check:
            self._check_tool_entry_points()

        if not self.options.check or "tool-organization" in self.options.check:
            self._check_tool_organization()

        if not self.options.check or "naming" in self.options.check:
            self._check_naming_conventions()

        if not self.options.check or "coverage" in self.options.check:
            self._check_reference_coverage()

        # Print results
        self._print_results()

        # Determine exit code
        if self.violations:
            error_count = sum(1 for v in self.violations if v["severity"] == "error")
            warning_count = sum(1 for v in self.violations if v["severity"] == "warning")

            if self.options.strict and warning_count > 0:
                return 1
            if error_count > 0:
                return 1

        print("\n" + "=" * 80)
        print("SCAN COMPLETE")
        print("=" * 80)
        return 0

    def _check_broken_links(self):
        """Check Layer 1: Ensure all links point to existing files and anchors.

        Now properly handles links with anchors (e.g., docs/file.md#section).
        """
        print("\n### Checking for Broken Links...")

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        all_md_files = list(self.project_root.rglob("*.md"))

        for md_file in all_md_files:
            if ".git" in str(md_file):
                continue

            relative_path = str(md_file.relative_to(self.project_root))
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove code blocks before scanning (backtick-delimited)
            content_without_code = re.sub(r"```[\s\S]*?```", "", content)
            content_without_code = re.sub(r"`[^`]+`", "", content_without_code)

            for match in link_pattern.finditer(content_without_code):
                link_text = match.group(1)
                link_target = match.group(2)

                # Skip external URLs and mailto
                if link_target.startswith(("http://", "https://", "mailto:")):
                    continue

                # Handle pure anchors: [Section](#section-id) refers to same file
                if link_target.startswith("#"):
                    # Validate anchor exists in current file
                    anchor = link_target[1:]  # Remove leading #
                    valid_anchors = self._extract_anchors_from_file(md_file)
                    if anchor not in valid_anchors:
                        context_start = max(0, match.start() - 100)
                        context_end = min(len(content_without_code), match.end() + 100)
                        context = content_without_code[context_start:context_end]
                        is_conditional = any(
                            marker.lower() in context.lower()
                            for marker in CONDITIONAL_MARKERS
                        )
                        if not is_conditional:
                            self.violations.append(
                                {
                                    "file": relative_path,
                                    "type": "broken-link",
                                    "severity": "error",
                                    "message": f"Broken link: {link_target} (anchor not found in file)",
                                    "target": f"{relative_path}{link_target}",
                                }
                            )
                            if self.options.verbose:
                                print(f"  ❌ {relative_path}: {link_target} (anchor not found)")
                    continue

                # Resolve link target (file path and optional anchor)
                target_file, anchor = self._resolve_link_target(link_target, md_file)

                # Skip placeholder-like targets (single word, not a path)
                # Check the FILE part only, not including anchor
                file_part = link_target.split("#")[0] if "#" in link_target else link_target
                if "/" not in file_part and not file_part.endswith(".md"):
                    continue

                # Check if target file exists
                if not target_file.exists():
                    # Check if this link is marked as conditional (optional)
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(content_without_code), match.end() + 100)
                    context = content_without_code[context_start:context_end]

                    is_conditional = any(
                        marker.lower() in context.lower()
                        for marker in CONDITIONAL_MARKERS
                    )

                    # Skip if marked as conditional/optional
                    if is_conditional:
                        continue
                    self.violations.append(
                        {
                            "file": relative_path,
                            "type": "broken-link",
                            "severity": "error",
                            "message": f"Broken link: {link_target} (file not found)",
                            "target": str(target_file.relative_to(self.project_root)) if target_file.is_absolute() else str(target_file),
                        }
                    )
                    if self.options.verbose:
                        print(f"  ❌ {relative_path}: {link_target}")
                    continue

                # File exists - now check anchor if provided
                if anchor:
                    valid_anchors = self._extract_anchors_from_file(target_file)
                    if anchor not in valid_anchors:
                        context_start = max(0, match.start() - 100)
                        context_end = min(len(content_without_code), match.end() + 100)
                        context = content_without_code[context_start:context_end]
                        is_conditional = any(
                            marker.lower() in context.lower()
                            for marker in CONDITIONAL_MARKERS
                        )
                        if not is_conditional:
                            self.violations.append(
                                {
                                    "file": relative_path,
                                    "type": "broken-link",
                                    "severity": "error",
                                    "message": f"Broken link: {link_target} (anchor '{anchor}' not found)",
                                    "target": str(target_file.relative_to(self.project_root)),
                                }
                            )
                            if self.options.verbose:
                                print(f"  ❌ {relative_path}: {link_target} (anchor '{anchor}' not found)")

    def _check_back_references(self):
        """Check Layer 2: System-prompts shouldn't reference outside without marking."""
        print("\n### Checking for Problematic Back-References...")

        system_prompts_dir = self.project_root / "docs" / "system-prompts"
        if not system_prompts_dir.exists():
            return

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for md_file in system_prompts_dir.rglob("*.md"):
            relative_path = str(md_file.relative_to(self.project_root))
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove code blocks before scanning to avoid false positives in templates/examples
            content_without_code = re.sub(r"```[\s\S]*?```", "", content)
            content_without_code = re.sub(r"`[^`]+`", "", content_without_code)

            for match in link_pattern.finditer(content_without_code):
                link_text = match.group(1)
                link_target = match.group(2)

                # Skip safe references
                if link_target.startswith(("http://", "https://", "#")):
                    continue
                if any(entry in link_target for entry in ENTRY_POINTS):
                    continue
                
                # Check actual resolved path
                try:
                    # Handle relative paths
                    if link_target.startswith("/"):
                        # Absolute from project root (convention)
                        target_path = self.project_root / link_target.lstrip("/")
                    else:
                        target_path = (md_file.parent / link_target).resolve()
                    
                    # Check if target is inside system-prompts
                    # We use strict=False because target might not exist (that's a broken link check)
                    try:
                        target_path.relative_to(system_prompts_dir)
                        # It is inside system-prompts, so it's safe
                        continue
                    except ValueError:
                        # It is outside system-prompts
                        pass
                except Exception:
                    # If path resolution fails, fall back to string check or assume unsafe
                    if "system-prompts" in link_target:
                        continue

                if not link_target.endswith(".md"):
                    continue

                # Check if this is an allowlisted back-reference (intentional project integration)
                if relative_path in ALLOWED_BACK_REFERENCES:
                    if link_target in ALLOWED_BACK_REFERENCES[relative_path]:
                        continue

                # Check if marked as conditional
                # We need to find the match in the ORIGINAL content to check surrounding text
                # This is tricky because we stripped code.
                # Alternative: Check if the link exists in the stripped content (it does),
                # then find its location in the stripped content.
                # But 'content' has code, 'content_without_code' doesn't. Indices don't match.
                # Simplified approach: If found in content_without_code, we search for the target string in original content
                # and check markers around it. This might have false positives if same link appears twice (once in code, once out).
                # Better: iterate matches in content_without_code, and use a context window from there?
                # No, content_without_code shrinks.

                # reliable context check:
                # We know the link is problematic. We need to check if it's conditional.
                # We search for the specific link text in the original content (outside code blocks logic is implied by previous step)
                # We'll just check if *any* occurrence of this link in the file is marked conditional?
                # Or simply: if the link is found in the "clean" content, we flag it.
                # We just need to check if "conditional markers" are near the link in the clean content.

                context_start = max(0, match.start() - 200)
                context_end = min(len(content_without_code), match.end() + 200)
                context = content_without_code[context_start:context_end]

                is_conditional = any(
                    marker.lower() in context.lower()
                    for marker in CONDITIONAL_MARKERS
                )

                if not is_conditional:
                    self.violations.append(
                        {
                            "file": relative_path,
                            "type": "back-reference",
                            "severity": "warning",
                            "message": f"Back-reference to project file without conditional marking: {link_target}",
                        }
                    )
                    if self.options.verbose:
                        print(f"  ⚠️  {relative_path}: {link_target} (not marked conditional)")

    def _check_reference_formatting(self):
        """Check Layer 3: All file references use hyperlinks or backticks (not plain text)."""
        print("\n### Checking Reference Formatting...")

        # Patterns to detect file references
        hyperlink_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
        backtick_pattern = re.compile(r"`([^`]+\.md)`")

        # Pattern for potential plain-text references (words containing .md or path-like structures)
        # This includes: docs/file.md, AGENTS.md, ./file.md, ../file.md, etc.
        plaintext_pattern = re.compile(
            r"(?:^|[^`\[])(?:(?:docs/|\.{0,2}/)?(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+\.md|(?:AGENTS|\.claude/CLAUDE|CLINE|AIDER|\.gemini/GEMINI)\.md)(?:[^)\]`]|$)"
        )

        all_md_files = list(self.project_root.rglob("*.md"))

        for md_file in all_md_files:
            if ".git" in str(md_file):
                continue

            relative_path = str(md_file.relative_to(self.project_root))

            # Skip transient directories (working documents, not canonical)
            if any(transient in relative_path for transient in TRANSIENT_DIRS):
                continue

            # Skip entry point files (meta-documents that reference themselves and other docs)
            if md_file.name in ENTRY_POINTS:
                continue

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Build a set of all properly formatted references in this file
            hyperlink_targets = set()
            backtick_targets = set()

            for match in hyperlink_pattern.finditer(content):
                hyperlink_targets.add(match.group(2))

            for match in backtick_pattern.finditer(content):
                backtick_targets.add(match.group(1))

            # Now look for plain-text file references that are NOT in hyperlinks or backticks
            # Split by backtick sections and hyperlinks to avoid false positives

            # Remove code blocks and inline code first to avoid false positives
            content_for_check = re.sub(r"```[\s\S]*?```", "", content)

            # Process line by line to find plain-text refs
            for line_num, line in enumerate(content_for_check.split("\n"), 1):
                # Skip lines that are entirely in code/links
                if line.strip().startswith("`") or line.strip().startswith("["):
                    continue

                # Remove hyperlinks and backticks from this line for analysis
                line_to_check = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", "", line)
                line_to_check = re.sub(r"`[^`]+`", "", line_to_check)

                # Look for markdown file references
                # Pattern: word characters with dots (like AGENTS.md) or paths (docs/file.md)
                potential_refs = re.findall(
                    r"(?:(?:docs|\.)/)?(?:[a-zA-Z0-9_-]+/)*[a-zA-Z0-9_-]+\.md|(?:AGENTS|CLAUDE|CLINE|AIDER|GEMINI)\.md",
                    line_to_check
                )

                for ref in potential_refs:
                    # Skip if it's in a valid format
                    if ref in hyperlink_targets or ref in backtick_targets:
                        continue

                    # Skip special root files that are often referenced in plain text
                    ignored_files = {
                        "README.md", "AGENTS.md", "CLAUDE.md", "AIDER.md",
                        "GEMINI.md", "CLINE.md", "TOOL-X.md", ".aider.md", ".clinerules"
                    }
                    if ref in ignored_files or ref.split("/")[-1] in ignored_files:
                        continue

                    # Skip common false positives (file paths in explanations that shouldn't be links)
                    if "filename" in line.lower() or "example" in line.lower():
                        continue

                    # Check if the file actually exists
                    if not ref.endswith(".md"):
                        continue

                    # This looks like a plain-text file reference
                    self.violations.append(
                        {
                            "file": relative_path,
                            "type": "reference-formatting",
                            "severity": "warning",
                            "message": f"Plain-text file reference '{ref}' should use backticks or hyperlink format",
                            "line": line_num,
                        }
                    )
                    if self.options.verbose:
                        print(f"  ⚠️  {relative_path}:{line_num}: '{ref}' (plain text, not formatted)")

    def _check_tool_entry_points(self) -> int:
        """Layer 4: Validate tool entry point files (CLAUDE.md, .aider.md, etc.)."""
        print("\n[Layer 4: Tool Entry Points]")

        # Map entry files to their corresponding guides
        tool_files = {
            ".claude/CLAUDE.md": "claude-code.md",
            ".aider.md": "aider.md",
            ".clinerules": "cline.md",
            ".gemini/GEMINI.md": "gemini.md",
        }

        errors = 0
        for entry_file, guide_file in tool_files.items():
            path = self.project_root / entry_file
            if not path.exists():
                # Codex doesn't have a dedicated entry file anymore
                if entry_file == "CODEX.md":
                    continue
                print(f"  ✗ {entry_file} missing")
                errors += 1
                continue

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            issues = []
            lines = content.strip().split("\n")

            # 1. Anemic format check (line count)
            if len(lines) > 25:
                issues.append(f"Too long ({len(lines)} lines, max 25)")

            # 2. Required links check
            required_links = [
                "AGENTS.md",
                "docs/definition-of-done.md",
                f"docs/system-prompts/tools/{guide_file}",
                "docs/workflows.md",
            ]

            for link in required_links:
                if link not in content:
                    issues.append(f"Missing link: {link}")

            if issues:
                print(f"  ✗ {entry_file}:")
                for issue in issues:
                    print(f"    - {issue}")
                errors += 1
            else:
                print(f"  ✓ {entry_file} (Valid)")

        return errors

    def _check_tool_organization(self):
        """Check Layer 3: Tool guides in correct locations."""
        print("\n### Checking Tool Guide Organization...")

        # Check generic vs project-specific
        tools_dir = self.project_root / "docs" / "system-prompts" / "tools"
        tool_specific_dir = self.project_root / "docs" / "tool-specific-guides"

        if tools_dir.exists():
            for guide_file in tools_dir.glob("*.md"):
                if guide_file.name == "README.md":
                    continue

                with open(guide_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Generic guides shouldn't heavily reference project implementation
                # (some mentions in examples are OK, but shouldn't be main focus)
                # Check for patterns that suggest project-specific content:
                # - References to src/ directories with specific module names
                # - References to specific Python files
                # - Module-specific configuration files
                project_src_refs = len(re.findall(r"src/\w+/", content))
                specific_file_refs = len(re.findall(r"\w+\.py", content))

                # If there are many specific references, it might be project-specific
                # This is a heuristic - adjust thresholds as needed
                if project_src_refs > 5 or specific_file_refs > 10:
                    self.violations.append(
                        {
                            "file": str(guide_file.relative_to(self.project_root)),
                            "type": "tool-organization",
                            "severity": "warning",
                            "message": "Generic tool guide may contain project-specific references",
                        }
                    )

        if tool_specific_dir.exists():
            for guide_file in tool_specific_dir.glob("*.md"):
                with open(guide_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if it's actually generic (shouldn't be here)
                # Generic guides explain tool + AGENTS.md but don't explain project integration
                # Project-specific guides should reference:
                # - Specific source code paths (src/module_name/)
                # - Specific Python module files
                # - Project-specific configuration files
                has_project_specifics = (
                    bool(re.search(r"src/\w+/\w+", content))  # Specific module paths
                    or bool(re.search(r"`\w+/\w+\.py`", content))  # Specific Python files
                    or "project architecture" in content.lower()
                    or "project-specific" in content.lower()
                )

                if not has_project_specifics and guide_file.name != "README.md":
                    self.violations.append(
                        {
                            "file": str(guide_file.relative_to(self.project_root)),
                            "type": "tool-organization",
                            "severity": "warning",
                            "message": "Project-specific guide appears to be generic (should be in system-prompts/tools/)",
                        }
                    )

    def _check_naming_conventions(self):
        """Check Layer 4: Files follow naming conventions."""
        print("\n### Checking Naming Conventions...")

        docs_dir = self.project_root / "docs"
        if not docs_dir.exists():
            return

        kebab_pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")

        for md_file in docs_dir.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            filename = md_file.name
            relative_path = str(md_file.relative_to(self.project_root))

            # Skip system-prompts/tools/ (already documented separately)
            if "system-prompts/tools" in relative_path:
                continue

            # Skip dev_notes/ (uses timestamp format)
            if "dev_notes" in relative_path:
                continue

            # Check lowercase-kebab convention
            if not kebab_pattern.match(filename):
                # Allow some exceptions
                if filename not in ["README.md"]:
                    self.violations.append(
                        {
                            "file": relative_path,
                            "type": "naming",
                            "severity": "warning",
                            "message": f"File doesn't follow lowercase-kebab.md convention: {filename}",
                        }
                    )

    def _check_reference_coverage(self):
        """Check Layer 5: All tool guides are referenced appropriately."""
        print("\n### Checking Reference Coverage...")

        # Find all generic tool guides (project-specific ones don't need to be in README)
        tools_dir = self.project_root / "docs" / "system-prompts" / "tools"

        guides_found = {}

        if tools_dir.exists():
            for guide_file in sorted(tools_dir.glob("*.md")):
                if guide_file.name == "README.md":
                    continue
                guides_found[guide_file.name] = str(guide_file.relative_to(self.project_root))

        # Check if guides are referenced from README.md
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            with open(readme_file, "r", encoding="utf-8") as f:
                readme_content = f.read()

            for guide_name, guide_path in guides_found.items():
                base_name = guide_name.replace(".md", "")
                if base_name not in readme_content:
                    self.violations.append(
                        {
                            "file": "README.md",
                            "type": "coverage",
                            "severity": "warning",
                            "message": f"Generic tool guide '{guide_name}' not referenced in README.md",
                        }
                    )

    def _print_results(self):
        """Print scan results."""
        if not self.violations:
            print("\n✅ All checks passed!")
            return

        print("\n### VIOLATIONS FOUND\n")

        # Group by severity
        errors = [v for v in self.violations if v["severity"] == "error"]
        warnings = [v for v in self.violations if v["severity"] == "warning"]

        if errors:
            print(f"❌ Errors ({len(errors)}):")
            for violation in errors:
                print(f"  {violation['file']}")
                print(f"    → {violation['message']}")
                if "target" in violation:
                    print(f"       Target: {violation['target']}")
                print()

        if warnings:
            print(f"⚠️  Warnings ({len(warnings)}):")
            for violation in warnings:
                print(f"  {violation['file']}")
                print(f"    → {violation['message']}")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Document Integrity Scanner",
        epilog="See docs/system-prompts/processes/document-integrity-scan.md for details.",
    )

    parser.add_argument(
        "--check",
        action="append",
        choices=["broken-links", "back-references", "reference-formatting", "tool-entries", "tool-organization", "naming", "coverage"],
        help="Run specific checks (default: run all)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output showing all checks"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (not just errors)",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    # Find project root if running from subdirectory
    if not (args.project_root / "AGENTS.md").exists():
        # Try parent directories
        for parent in args.project_root.parents:
            if (parent / "AGENTS.md").exists():
                args.project_root = parent
                break

    scanner = DocumentScanner(args.project_root, args)
    exit_code = scanner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
