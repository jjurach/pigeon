#!/usr/bin/env python3
"""
Planning Summary - Display execution status for beads task tracking

This script provides a comprehensive view of task execution status across the root project and all
git submodules that have a .beads/ directory. By default, it auto-discovers and includes
beads from all initialized submodules alongside the root project.

ARCHITECTURE:
- Primary: Uses 'bd list --all --json' command if beads CLI is available (root and submodules)
- Fallback: Reads directly from .beads/issues.jsonl if bd CLI fails or Dolt is unreachable
- Submodules: Runs 'bd list --all --json' with cwd=<submodule_root>; falls back to JSONL
- This ensures it works in any environment (with or without beads CLI / Dolt server)

MULTI-PROJECT SUPPORT:
- Automatically discovers git submodules from .gitmodules
- Includes beads from any submodule that has a .beads/ directory
- Each project is displayed with a labeled header section
- Aggregate statistics shown at the end
- Submodules without .beads/ are silently skipped
- Errors in individual submodules are isolated (other projects still display)

USAGE:
    # Basic (show all categories - includes submodules by default)
    python3 docs/system-prompts/planning-summary.py

    # Filter by status (closed, ready, in-progress, blocked)
    python3 docs/system-prompts/planning-summary.py --status ready

    # Filter by label (implementation, approval, failure, etc)
    python3 docs/system-prompts/planning-summary.py --label approval

    # Verbose output with full descriptions
    python3 docs/system-prompts/planning-summary.py --verbose

    # JSON output for parsing
    python3 docs/system-prompts/planning-summary.py --json

    # Limit number of closed beads shown (default: 5)
    python3 docs/system-prompts/planning-summary.py --limit 10

    # Show only root project (no submodules)
    python3 docs/system-prompts/planning-summary.py --no-submodules

    # Show only specific submodules (comma-separated names)
    python3 docs/system-prompts/planning-summary.py --submodules cackle,pigeon

    # Find the single next ready bead by cross-project priority ordering
    python3 docs/system-prompts/planning-summary.py --next-bead

EXECUTION FOR AGENTS:
    # From project root, no venv needed (fallback reads .beads/issues.jsonl directly)
    python3 docs/system-prompts/planning-summary.py

    # For full functionality with bd CLI, activate venv first
    source venv/bin/activate && python3 docs/system-prompts/planning-summary.py
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any


class BeadsSummary:
    def __init__(self, project_name: str = "root", beads_path: str = ".beads"):
        self.project_name = project_name
        self.beads_path = beads_path
        self.all_beads = []
        self.closed = []
        self.in_progress = []
        self.ready = []
        self.blocked = []
        self.failures = []

    def load_beads(self) -> bool:
        """Load all beads from database - tries bd CLI first, falls back to {beads_path}/issues.jsonl"""
        jsonl_path = f"{self.beads_path}/issues.jsonl"
        # Try bd CLI first (works for root .beads/ or submodules with cwd)
        if self.beads_path == ".beads":
            # Root project - run bd list from current directory
            try:
                result = subprocess.run(
                    ['bd', 'list', '--all', '--json'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.all_beads = json.loads(result.stdout)
                return True
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                pass  # Fall through to JSONL fallback
        else:
            # Submodule - extract the root directory and run bd list from there
            # beads_path looks like "modules/hatchery/.beads"
            submodule_root = os.path.dirname(self.beads_path)
            try:
                result = subprocess.run(
                    ['bd', 'list', '--all', '--json'],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=submodule_root
                )
                self.all_beads = json.loads(result.stdout)
                return True
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
                pass  # Fall through to JSONL fallback

        # Fallback: read directly from issues.jsonl
        try:
            with open(jsonl_path, 'r') as f:
                self.all_beads = []
                skipped = 0
                for lineno, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        self.all_beads.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Warning: [{self.project_name}] Skipping corrupt line {lineno} in {jsonl_path}: {e}", file=sys.stderr)
                        skipped += 1
                if skipped:
                    print(f"Warning: [{self.project_name}] Skipped {skipped} corrupt line(s) in {jsonl_path}", file=sys.stderr)
            return True
        except PermissionError as e:
            print(f"✗ [{self.project_name}] Permission denied reading {jsonl_path}: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print(f"✗ [{self.project_name}] Beads file not found: {jsonl_path}", file=sys.stderr)
            print(f"  Ensure beads is initialized: ls {self.beads_path}/", file=sys.stderr)
            return False

    def categorize_beads(self):
        """Categorize beads by status and type (handles both bd CLI and JSONL formats)"""
        # Create a lookup map for bead status
        status_map = {b['id']: b.get('status', 'unknown') for b in self.all_beads}

        for bead in self.all_beads:
            status = bead.get('status', 'unknown')
            labels = bead.get('labels', [])
            dependencies = bead.get('dependencies', [])

            # Handle both bd CLI format and JSONL format
            # bd status values: open, in_progress, blocked, deferred, closed
            # JSONL format: same values; 'open' beads may be ready or dep-blocked
            # Legacy compatibility: also handle old 'in-progress', 'ready', 'not-ready' values
            if status == 'closed':
                self.closed.append(bead)
            elif status in ('in-progress', 'in_progress'):
                self.in_progress.append(bead)
            elif status == 'ready':
                self.ready.append(bead)
            elif status in ('not-ready', 'open', 'unknown'):
                # Check blockers
                is_blocked = False
                blockers = []
                for dep in dependencies:
                    # Ignore parent-child for blocking logic unless we want epics to block children
                    # In this project, children are tasks within the epic, they shouldn't be 'blocked' by the epic itself
                    if dep.get('type') == 'parent-child':
                        continue
                    
                    dep_id = dep.get('depends_on_id')
                    dep_status = status_map.get(dep_id, 'unknown')
                    if dep_status != 'closed':
                        is_blocked = True
                        blockers.append(dep_id)
                
                if is_blocked:
                    bead['blocked_by'] = blockers # Ensure blocked_by is available for display
                    self.blocked.append(bead)
                else:
                    self.ready.append(bead)
            else:
                self.ready.append(bead)

            if 'failure' in labels:
                self.failures.append(bead)

    def filter_by_status(self, status: str):
        """Filter beads by status"""
        if status == 'closed':
            return self.closed
        elif status == 'in-progress':
            return self.in_progress
        elif status == 'ready':
            return self.ready
        elif status == 'blocked':
            return self.blocked
        else:
            return []

    def filter_by_label(self, label: str):
        """Filter beads by label"""
        return [b for b in self.all_beads if label in b.get('labels', [])]

    def format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as relative time (e.g., '2h ago', '1d ago')"""
        if not timestamp:
            return "unknown"

        try:
            # Parse ISO timestamp
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(ts.tzinfo)
            delta = now - ts
            seconds = delta.total_seconds()

            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes}m ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours}h ago"
            elif seconds < 2592000:  # 30 days
                days = int(seconds / 86400)
                return f"{days}d ago"
            else:
                months = int(seconds / 2592000)
                return f"{months}mo ago"
        except Exception:
            return "unknown"

    def print_summary(self, verbose=False, status_filter=None, label_filter=None, limit=5, project_header=None):
        """Print summary of beads"""
        if project_header:
            print(f"\n{'='*60}")
            print(f"  {project_header}")
            print(f"{'='*60}")
        else:
            print("Beads Status Summary")
            print("="*60)

        # Apply filters
        if status_filter:
            filtered = self.filter_by_status(status_filter)
            self.print_bead_list(filtered, status_filter.title(), verbose, limit=0)  # Show all when filtering
        elif label_filter:
            filtered = self.filter_by_label(label_filter)
            self.print_bead_list(filtered, f"Label: {label_filter}", verbose, limit=0)
        else:
            # Show all categories
            self.print_recently_closed(verbose, limit)
            self.print_in_progress(verbose)
            self.print_ready(verbose)
            self.print_blocked(verbose)
            self.print_failures(verbose)
            self.print_statistics()

    def print_bead_list(self, beads: List[Dict], title: str, verbose: bool, limit: int = 0):
        """Print a list of beads"""
        if not beads:
            return

        print(f"\n{title} ({len(beads)}):")

        display_beads = beads[:limit] if limit > 0 else beads

        for bead in display_beads:
            bead_id = bead['id']
            title = bead['title']
            labels = bead.get('labels', [])

            # Format based on status
            status = bead.get('status', 'unknown')
            is_ready = bead in self.ready

            if status == 'closed':
                icon = '✓'
                time_ago = self.format_time_ago(bead.get('closed_at'))
                suffix = f"(closed {time_ago})"
            elif status in ('in-progress', 'in_progress'):
                icon = '→'
                time_ago = self.format_time_ago(bead.get('claimed_at') or bead.get('updated_at'))
                suffix = f"(claimed {time_ago})"
            elif is_ready:
                icon = '○'
                label_str = ', '.join(labels)
                suffix = f"[{label_str}]" if label_str else "(open)"
            elif status == 'not-ready' or bead in self.blocked:
                icon = '✗'
                blockers = bead.get('blocked_by', [])
                blocker_str = ', '.join(blockers[:2])
                if len(blockers) > 2:
                    blocker_str += f" (+{len(blockers)-2} more)"
                suffix = f"(blocked by: {blocker_str})"
            else:
                icon = '?'
                suffix = f"({status})"

            if 'failure' in labels:
                icon = '❌'

            # Print bead
            if verbose:
                print(f"  {icon} {bead_id}  {title}")
                print(f"     Labels: {', '.join(labels)}")
                print(f"     {suffix}")
                body = bead.get('description', '')
                if body:
                    # Print first 3 lines of description
                    lines = body.split('\n')[:3]
                    for line in lines:
                        if line.strip():
                            print(f"     {line}")
                print()
            else:
                # Compact format
                title_truncated = title[:40] if len(title) > 40 else title
                print(f"  {icon} {bead_id:<12} {title_truncated:<40} {suffix}")

    def print_recently_closed(self, verbose: bool, limit: int):
        """Print recently closed beads"""
        # Sort by closed time (most recent first)
        sorted_closed = sorted(
            [b for b in self.closed if b.get('closed_at')],
            key=lambda b: b['closed_at'],
            reverse=True
        )
        self.print_bead_list(sorted_closed, f"Recently Closed (last {limit})", verbose, limit)

    def print_in_progress(self, verbose: bool):
        """Print in-progress beads"""
        if not self.in_progress:
            return
        self.print_bead_list(self.in_progress, "Currently In Progress", verbose)

    def print_ready(self, verbose: bool):
        """Print ready beads"""
        if not self.ready:
            return
        self.print_bead_list(self.ready, "Ready to Work", verbose)

    def print_blocked(self, verbose: bool):
        """Print blocked beads"""
        if not self.blocked:
            return
        self.print_bead_list(self.blocked, "Blocked", verbose)

    def print_failures(self, verbose: bool):
        """Print failure beads"""
        if not self.failures:
            return

        print(f"\nFailures ({len(self.failures)}):")
        for bead in self.failures:
            bead_id = bead['id']
            title = bead['title']
            time_ago = self.format_time_ago(bead.get('created_at'))

            print(f"  ❌ {bead_id}  {title}")
            if verbose:
                print(f"     Created: {time_ago}")
                body = bead.get('description', '')
                if 'Original bead:' in body:
                    # Extract original bead reference
                    for line in body.split('\n'):
                        if 'Original bead:' in line or 'Original Task:' in line:
                            print(f"     {line.strip()}")
                            break
                print()
            else:
                print(f"     (created {time_ago}, requires human review)")

    def print_statistics(self):
        """Print overall statistics"""
        total = len(self.all_beads)
        if total == 0:
            print("\nNo beads found.")
            return

        closed_count = len(self.closed)
        in_progress_count = len(self.in_progress)
        ready_count = len(self.ready)
        blocked_count = len(self.blocked)

        closed_pct = int(closed_count / total * 100)

        print(f"\n{'─'*60}\n")
        print(f"Total Beads: {total}")
        print(f"  Closed:      {closed_count} ({int(closed_count/total*100)}%)")
        print(f"  In Progress: {in_progress_count} ({int(in_progress_count/total*100)}%)")
        print(f"  Ready:       {ready_count} ({int(ready_count/total*100)}%)")
        print(f"  Blocked:     {blocked_count} ({int(blocked_count/total*100)}%)")

        if self.failures:
            print(f"  Failed:      {len(self.failures)} ({int(len(self.failures)/total*100)}%)")

        # Progress bar
        progress_bar = '█' * (closed_pct // 5) + '░' * (20 - closed_pct // 5)
        print(f"\nProgress: {progress_bar} {closed_pct}% complete")

    def output_json(self):
        """Output as JSON"""
        output = {
            'summary': {
                'total': len(self.all_beads),
                'closed': len(self.closed),
                'in_progress': len(self.in_progress),
                'ready': len(self.ready),
                'blocked': len(self.blocked),
                'failed': len(self.failures),
                'completion_percentage': int(len(self.closed) / len(self.all_beads) * 100) if self.all_beads else 0
            },
            'recently_closed': sorted(
                [b for b in self.closed if b.get('closed_at')],
                key=lambda b: b['closed_at'],
                reverse=True
            )[:5],
            'in_progress': self.in_progress,
            'ready': self.ready,
            'blocked': self.blocked,
            'failures': self.failures
        }
        print(json.dumps(output, indent=2))


def discover_submodules(root_path: str = ".") -> List[Dict[str, str]]:
    """Parse .gitmodules to discover all configured submodules.

    Returns a list of dicts with keys: name, path, url.
    Skips commented-out entries. Returns empty list if no .gitmodules exists.
    """
    gitmodules_path = f"{root_path}/.gitmodules"
    submodules = []

    try:
        with open(gitmodules_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return []

    import re
    # Parse each [submodule "name"] block
    block_pattern = re.compile(
        r'^\[submodule\s+"([^"]+)"\]\s*\n((?:[ \t]+\S.*\n?)*)',
        re.MULTILINE
    )
    # Lines beginning with # are comments - filter them out first
    lines = []
    for line in content.splitlines(keepends=True):
        if not line.lstrip().startswith('#'):
            lines.append(line)
    clean_content = ''.join(lines)

    for match in block_pattern.finditer(clean_content):
        name = match.group(1)
        block_body = match.group(2)
        path_match = re.search(r'path\s*=\s*(.+)', block_body)
        url_match = re.search(r'url\s*=\s*(.+)', block_body)
        if path_match:
            submodule_path = path_match.group(1).strip()
            url = url_match.group(1).strip() if url_match else ''
            submodules.append({'name': name, 'path': submodule_path, 'url': url})

    return submodules


def find_beads_in_submodules(root_path: str = ".") -> List[Dict[str, str]]:
    """Discover submodules that have an initialized .beads/ directory.

    Returns a list of dicts with keys: name, path, beads_path.
    Logs a warning for uninitialized submodules (directory missing).
    Returns empty list if no submodules are configured.
    """
    import os
    submodules = discover_submodules(root_path)
    results = []

    for sub in submodules:
        sub_abs = os.path.join(root_path, sub['path'])
        beads_abs = os.path.join(sub_abs, '.beads')

        if not os.path.isdir(sub_abs):
            # Uninitialized submodule - warn and skip
            print(f"Warning: submodule '{sub['name']}' directory not found (uninitialized?): {sub['path']}", file=sys.stderr)
            continue

        if os.path.isdir(beads_abs):
            results.append({
                'name': sub['name'],
                'path': sub['path'],
                'beads_path': os.path.join(sub['path'], '.beads'),
            })

    return results


def process_all_projects(root_path: str = ".") -> List[Dict[str, Any]]:
    """Process root project plus all submodules with .beads/ directories.

    For each project, creates a BeadsSummary instance, loads beads, and categorizes them.
    Failures in individual projects are isolated - one project's error does not stop others.
    Emits a performance warning if processing more than 10 submodules.

    Returns a list of dicts with keys:
        - name: project name (str)
        - path: project path relative to root_path (str, "." for root)
        - summary: BeadsSummary instance (or None if loading failed)
        - error: error message string if loading failed, else None
    """
    import time
    results = []
    start_time = time.monotonic()

    # Detect root project name
    root_abs = os.path.abspath(root_path)
    root_name = os.path.basename(root_abs)

    # Process root project first
    root_summary = BeadsSummary(project_name=root_name, beads_path=".beads")
    try:
        if root_summary.load_beads():
            root_summary.categorize_beads()
            results.append({'name': root_name, 'path': '.', 'summary': root_summary, 'error': None})
        else:
            results.append({'name': root_name, 'path': '.', 'summary': None, 'error': 'Failed to load beads'})
    except Exception as e:
        print(f"Error processing root project: {e}", file=sys.stderr)
        results.append({'name': root_name, 'path': '.', 'summary': None, 'error': str(e)})

    # Process each submodule with a .beads/ directory
    submodule_beads = find_beads_in_submodules(root_path)
    for sub in submodule_beads:
        name = sub['name']
        path = sub['path']
        beads_path = sub['beads_path']
        sub_summary = BeadsSummary(project_name=name, beads_path=beads_path)
        try:
            if sub_summary.load_beads():
                sub_summary.categorize_beads()
                results.append({'name': name, 'path': path, 'summary': sub_summary, 'error': None})
            else:
                results.append({'name': name, 'path': path, 'summary': None, 'error': 'Failed to load beads'})
        except Exception as e:
            print(f"Error processing submodule '{name}': {e}", file=sys.stderr)
            results.append({'name': name, 'path': path, 'summary': None, 'error': str(e)})

    elapsed = time.monotonic() - start_time
    submodule_count = len(submodule_beads)
    if submodule_count >= 10 and elapsed > 5:
        print(f"Warning: Processing {submodule_count} submodules took {elapsed:.1f}s (> 5s threshold)", file=sys.stderr)

    return results


def print_project_section_header(name: str, path: str, is_root: bool = False):
    """Print a formatted project header with ASCII separation."""
    if is_root:
        # Root project header with special styling
        print(f"\n┌{'─'*70}┐")
        print(f"│ 🏠 {name:<67} │")
        print(f"│    {path:<67} │")
        print(f"└{'─'*70}┘")
    else:
        # Submodule header
        print(f"\n├─ 📦 {name}")
        print(f"│  path: {path}")


def print_dashboard(projects: List[Dict[str, Any]]):
    """Print a compact dashboard showing module status."""
    print(f"\n{'='*100}")
    print("  DASHBOARD - MODULE STATUS SUMMARY")
    print(f"{'='*100}\n")

    # Build module status lines
    module_lines = []
    totals = {'total': 0, 'closed': 0, 'in_progress': 0, 'ready': 0, 'blocked': 0}

    for project in projects:
        name = project['name']
        summary = project['summary']
        error = project['error']

        if error or summary is None:
            status_str = "✗ ERROR"
            ready_str = ""
            blocked_str = ""
        else:
            total = len(summary.all_beads)
            closed = len(summary.closed)
            ready = len(summary.ready)
            blocked = len(summary.blocked)
            in_progress = len(summary.in_progress)

            # Calculate status indicator
            if blocked > 0:
                status_str = f"⚠ BLOCKED ({blocked})"
            elif in_progress > 0:
                status_str = f"→ IN-PROGRESS ({in_progress})"
            elif ready > 0:
                status_str = f"○ READY ({ready})"
            else:
                status_str = "✓ CLEAR"

            # Build compact status line
            ready_str = f"Ready: {ready}" if ready > 0 else ""
            blocked_str = f"Blocked: {blocked}" if blocked > 0 else ""

            totals['total'] += total
            totals['closed'] += closed
            totals['in_progress'] += in_progress
            totals['ready'] += ready
            totals['blocked'] += blocked

        # Format module line (80-100 columns)
        module_name = f"  {name:<25}"
        status_section = f"{status_str:<25}"
        details = f"{ready_str:<20} {blocked_str:<20}"
        module_line = f"{module_name} {status_section} {details}"
        module_lines.append(module_line[:100])  # Ensure max 100 columns

    # Print module lines
    for line in module_lines:
        print(line)

    # Print separator and aggregate statistics
    print(f"\n{'-'*100}\n")

    if totals['total'] > 0:
        closed_pct = int(totals['closed'] / totals['total'] * 100)

        # Summary statistics
        print(f"  AGGREGATE STATS:")
        print(f"    Total Beads:    {totals['total']:<6}  |  Closed: {totals['closed']:<6} ({closed_pct}%)")
        print(f"    In-Progress:    {totals['in_progress']:<6}  |  Ready:  {totals['ready']:<6}")
        print(f"    Blocked:        {totals['blocked']:<6}  |")

        # Progress bar
        progress_bar = '█' * (closed_pct // 5) + '░' * (20 - closed_pct // 5)
        print(f"\n  Progress: [{progress_bar}] {closed_pct}% complete\n")
    else:
        print("  No beads found across any projects.\n")


def print_multi_project_summary(projects: List[Dict[str, Any]], verbose=False, status_filter=None, label_filter=None, limit=5):
    """Print unified multi-project summary with per-project sections and aggregate stats."""
    totals = {'total': 0, 'closed': 0, 'in_progress': 0, 'ready': 0, 'blocked': 0}

    # Track if this is multi-project view
    is_multi_project = len(projects) > 1

    for idx, project in enumerate(projects):
        name = project['name']
        path = project['path']
        summary = project['summary']
        error = project['error']

        if error or summary is None:
            if is_multi_project:
                print_project_section_header(name, path, is_root=(path == '.'))
                print(f"\n  ✗ Error: {error}\n")
            else:
                print(f"\n{'='*60}")
                print(f"  {name}  (path: {path})")
                print(f"{'='*60}")
                print(f"  ✗ Error: {error}")
            continue

        if is_multi_project:
            # Use formatted header for multi-project view
            print_project_section_header(name, path, is_root=(path == '.'))
            summary.print_summary(
                verbose=verbose,
                status_filter=status_filter,
                label_filter=label_filter,
                limit=limit,
                project_header=None,  # Header already printed above
            )
        else:
            # Single project, use original header
            header = f"{name}  (path: {path})"
            summary.print_summary(
                verbose=verbose,
                status_filter=status_filter,
                label_filter=label_filter,
                limit=limit,
                project_header=header,
            )

        totals['total'] += len(summary.all_beads)
        totals['closed'] += len(summary.closed)
        totals['in_progress'] += len(summary.in_progress)
        totals['ready'] += len(summary.ready)
        totals['blocked'] += len(summary.blocked)

    # Print dashboard at the end for multi-project view
    if is_multi_project:
        print_dashboard(projects)


def find_next_bead(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find all ready beads across projects, sorted by cross-project priority.

    Sort key (ascending = higher priority first):
      1. priority integer (0=P0 most urgent, 4=P4 lowest)
      2. project tier (0=root project, 1=submodule)
      3. project path lexicographic ("modules/chatterbox" < "modules/second_voice")
      4. bead id lexicographic ("bead-abc" < "bead-def")

    This implements the canonical bead ordering policy:
    see docs/system-prompts/guides/bead-ordering.md

    Returns:
        List of candidate dicts sorted highest-priority first. Each dict has:
          bead, project_name, project_path, project_tier
    """
    candidates = []

    for project in projects:
        summary = project['summary']
        if summary is None:
            continue

        path = project['path']
        name = project['name']
        is_root = (path == '.')
        project_tier = 0 if is_root else 1

        for bead in summary.ready:
            priority = bead.get('priority', 4)
            if not isinstance(priority, int):
                try:
                    priority = int(priority)
                except (ValueError, TypeError):
                    priority = 4

            candidates.append({
                'bead': bead,
                'project_name': name,
                'project_path': path,
                'project_tier': project_tier,
                '_sort_key': (priority, project_tier, path, bead['id']),
            })

    candidates.sort(key=lambda c: c['_sort_key'])
    return candidates


def print_next_bead(projects: List[Dict[str, Any]]):
    """Print the highest-priority ready bead across all projects with context."""
    ranked = find_next_bead(projects)

    if not ranked:
        print("No ready beads found across all projects.")
        return

    top = ranked[0]
    bead = top['bead']
    bead_id = bead['id']
    priority = bead.get('priority', '?')
    priority_label = f"P{priority}" if isinstance(priority, int) else str(priority)
    title = bead.get('title', '(no title)')
    path = top['project_path']
    name = top['project_name']
    is_root = top['project_tier'] == 0
    project_label = f"{name} (root)" if is_root else f"{path}"

    if is_root:
        claim_cmd = f"bd update {bead_id} --status=in_progress"
    else:
        claim_cmd = f"cd {path} && bd update {bead_id} --status=in_progress"

    print("Next ready bead (cross-project priority order):")
    print()
    print(f"  [{priority_label}] {bead_id}")
    print(f"  Project: {project_label}")
    print(f"  Title:   {title}")
    print(f"  Claim:   {claim_cmd}")

    if len(ranked) > 1:
        print()
        print(f"{'─' * 60}")
        print(f"All ready beads ({len(ranked)}):")
        for i, entry in enumerate(ranked, 1):
            b = entry['bead']
            bid = b['id']
            p = b.get('priority', '?')
            plabel = f"P{p}" if isinstance(p, int) else str(p)
            t = b.get('title', '(no title)')
            t_trunc = t[:45] + '\u2026' if len(t) > 45 else t
            proj_path = entry['project_path']
            proj_short = '.' if proj_path == '.' else proj_path
            print(f"  {i:2}. [{plabel}] {bid:<16} {proj_short:<28} {t_trunc}")


def main():
    parser = argparse.ArgumentParser(description='Display beads execution status')
    parser.add_argument('--status', type=str, choices=['closed', 'in-progress', 'ready', 'blocked'],
                        help='Filter by status')
    parser.add_argument('--label', type=str, help='Filter by label')
    parser.add_argument('--verbose', action='store_true', help='Show full descriptions')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of closed beads shown (default: 5)')
    parser.add_argument('--no-submodules', action='store_true', help='Only show root project (no submodules)')
    parser.add_argument('--submodules', type=str, metavar='NAME1,NAME2',
                        help='Comma-separated list of submodule names to include')
    parser.add_argument('--next-bead', action='store_true',
                        help='Show the single highest-priority ready bead across all projects (see bead-ordering.md)')

    args = parser.parse_args()

    if args.next_bead:
        # Always considers all submodules regardless of --no-submodules
        projects = process_all_projects(".")
        print_next_bead(projects)
        return

    if args.no_submodules:
        # Single-project mode (original behavior)
        summary = BeadsSummary()
        if not summary.load_beads():
            sys.exit(1)
        summary.categorize_beads()
        if args.json:
            summary.output_json()
        else:
            summary.print_summary(
                verbose=args.verbose,
                status_filter=args.status,
                label_filter=args.label,
                limit=args.limit,
            )
        return

    # Multi-project mode: process all projects
    projects = process_all_projects(".")

    # Apply --submodules filter if specified
    if args.submodules:
        names = {n.strip() for n in args.submodules.split(',')}
        projects = [p for p in projects if p['path'] == '.' or p['name'] in names]

    if args.json:
        output = {'projects': []}
        for p in projects:
            s = p['summary']
            output['projects'].append({
                'name': p['name'],
                'path': p['path'],
                'error': p['error'],
                'summary': {
                    'total': len(s.all_beads) if s else 0,
                    'closed': len(s.closed) if s else 0,
                    'in_progress': len(s.in_progress) if s else 0,
                    'ready': len(s.ready) if s else 0,
                    'blocked': len(s.blocked) if s else 0,
                } if s else None,
                'ready': s.ready if s else [],
                'blocked': s.blocked if s else [],
                'in_progress': s.in_progress if s else [],
            })
        print(json.dumps(output, indent=2))
    else:
        print_multi_project_summary(
            projects,
            verbose=args.verbose,
            status_filter=args.status,
            label_filter=args.label,
            limit=args.limit,
        )


if __name__ == '__main__':
    main()
