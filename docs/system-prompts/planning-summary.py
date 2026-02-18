#!/usr/bin/env python3
"""
Planning Summary - Display execution status for beads task tracking

This script provides a comprehensive view of task execution status by reading from .beads/issues.jsonl

ARCHITECTURE:
- Primary: Uses 'bd list --json' command if beads CLI is available
- Fallback: Reads directly from .beads/issues.jsonl if bd CLI fails
- This ensures it works in any environment (with or without beads CLI)

USAGE:
    # Basic (show all categories)
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

EXECUTION FOR AGENTS:
    # From project root, no venv needed (fallback reads .beads/issues.jsonl directly)
    python3 docs/system-prompts/planning-summary.py

    # For full functionality with bd CLI, activate venv first
    source venv/bin/activate && python3 docs/system-prompts/planning-summary.py
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any


class BeadsSummary:
    def __init__(self):
        self.all_beads = []
        self.closed = []
        self.in_progress = []
        self.ready = []
        self.blocked = []
        self.failures = []

    def load_beads(self) -> bool:
        """Load all beads from database - tries bd CLI first, falls back to .beads/issues.jsonl"""
        # Try bd CLI first
        try:
            result = subprocess.run(
                ['bd', 'list', '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            self.all_beads = json.loads(result.stdout)
            return True
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            # Fallback: read directly from .beads/issues.jsonl
            try:
                with open('.beads/issues.jsonl', 'r') as f:
                    self.all_beads = []
                    for line in f:
                        if line.strip():
                            self.all_beads.append(json.loads(line))
                return True
            except (FileNotFoundError, json.JSONDecodeError) as fallback_error:
                print(f"✗ Failed to load beads: {e}")
                print(f"✗ Fallback also failed: {fallback_error}")
                print("\nEnsure:")
                print("  1. Beads is initialized: ls .beads/")
                print("  2. Either: bd CLI is available (which bd)")
                print("     Or: .beads/issues.jsonl file exists")
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
            # bd format: closed, in-progress, ready, not-ready
            # JSONL format: open (which can be blocked/ready depending on dependencies)
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

    def print_summary(self, verbose=False, status_filter=None, label_filter=None, limit=5):
        """Print summary of beads"""
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
                time_ago = self.format_time_ago(bead.get('claimed_at'))
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
                body = bead.get('body', '')
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
                body = bead.get('body', '')
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


def main():
    parser = argparse.ArgumentParser(description='Display beads execution status')
    parser.add_argument('--status', type=str, choices=['closed', 'in-progress', 'ready', 'blocked'],
                        help='Filter by status')
    parser.add_argument('--label', type=str, help='Filter by label')
    parser.add_argument('--verbose', action='store_true', help='Show full descriptions')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of closed beads shown (default: 5)')

    args = parser.parse_args()

    summary = BeadsSummary()

    # Load beads
    if not summary.load_beads():
        sys.exit(1)

    # Categorize beads
    summary.categorize_beads()

    # Output
    if args.json:
        summary.output_json()
    else:
        summary.print_summary(
            verbose=args.verbose,
            status_filter=args.status,
            label_filter=args.label,
            limit=args.limit
        )


if __name__ == '__main__':
    main()
