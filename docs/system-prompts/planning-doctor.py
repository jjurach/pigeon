#!/usr/bin/env python3
"""
Planning Doctor - Detect and fix problems in beads database

This script detects common issues in beads task tracking and offers fixes.

Usage:
    python3 docs/system-prompts/planning-doctor.py              # Check only
    python3 docs/system-prompts/planning-doctor.py --fix         # Auto-fix safe issues
    python3 docs/system-prompts/planning-doctor.py --json        # JSON output
    python3 docs/system-prompts/planning-doctor.py --check orphaned  # Specific check
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set


class BeadsDoctor:
    def __init__(self, auto_fix=False, stale_threshold_hours=24):
        self.auto_fix = auto_fix
        self.stale_threshold_hours = stale_threshold_hours
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        self.all_beads = []

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

    def get_bead_details(self, bead_id: str) -> Dict[str, Any]:
        """Get detailed information about a bead"""
        try:
            result = subprocess.run(
                ['bd', 'show', bead_id, '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except Exception:
            return {}

    def check_orphaned_beads(self) -> int:
        """Check for beads blocked by non-existent beads"""
        print("[1/5] Checking for orphaned beads...")

        orphaned_count = 0
        bead_ids = {bead['id'] for bead in self.all_beads}

        for bead in self.all_beads:
            blocked_by = bead.get('blocked_by', [])

            for blocker_id in blocked_by:
                if blocker_id not in bead_ids:
                    orphaned_count += 1
                    issue = {
                        'type': 'orphaned',
                        'bead_id': bead['id'],
                        'bead_title': bead['title'],
                        'blocker_id': blocker_id
                    }
                    self.issues.append(issue)

                    if self.auto_fix:
                        # Auto-fix: remove orphaned dependency
                        try:
                            subprocess.run(
                                ['bd', 'dep', 'remove', bead['id'], blocker_id],
                                capture_output=True,
                                check=True
                            )
                            self.fixes_applied.append(f"Removed orphaned dependency: {bead['id']} -> {blocker_id}")
                        except subprocess.CalledProcessError:
                            pass

        if orphaned_count == 0:
            print("✓ No orphaned beads found")
        else:
            print(f"✗ Found {orphaned_count} orphaned dependencies")

        return orphaned_count

    def check_circular_dependencies(self) -> int:
        """Check for circular dependencies"""
        print("[2/5] Checking for circular dependencies...")

        circular_count = 0
        visited = set()
        recursion_stack = set()

        def has_cycle(bead_id: str, path: List[str]) -> bool:
            """DFS to detect cycles"""
            if bead_id in recursion_stack:
                # Found cycle
                cycle_start = path.index(bead_id)
                cycle = path[cycle_start:] + [bead_id]
                self.issues.append({
                    'type': 'circular',
                    'cycle': cycle
                })
                return True

            if bead_id in visited:
                return False

            visited.add(bead_id)
            recursion_stack.add(bead_id)

            # Get bead's blockers
            bead = next((b for b in self.all_beads if b['id'] == bead_id), None)
            if bead:
                for blocker_id in bead.get('blocked_by', []):
                    if has_cycle(blocker_id, path + [bead_id]):
                        return True

            recursion_stack.remove(bead_id)
            return False

        # Check each bead for cycles
        for bead in self.all_beads:
            if bead['id'] not in visited:
                if has_cycle(bead['id'], []):
                    circular_count += 1

        if circular_count == 0:
            print("✓ No circular dependencies found")
        else:
            print(f"✗ Found {circular_count} circular dependencies")

        return circular_count

    def check_stale_in_progress(self) -> int:
        """Check for stale in-progress beads"""
        print("[3/5] Checking for stale in-progress beads...")

        stale_count = 0
        threshold = timedelta(hours=self.stale_threshold_hours)

        for bead in self.all_beads:
            if bead.get('status') == 'in-progress':
                claimed_at = bead.get('claimed_at')
                if claimed_at:
                    try:
                        claimed_time = datetime.fromisoformat(claimed_at.replace('Z', '+00:00'))
                        age = datetime.now(claimed_time.tzinfo) - claimed_time

                        if age > threshold:
                            stale_count += 1
                            self.warnings.append({
                                'type': 'stale',
                                'bead_id': bead['id'],
                                'bead_title': bead['title'],
                                'age_hours': int(age.total_seconds() / 3600),
                                'assignee': bead.get('assignee', 'unknown')
                            })
                    except (ValueError, TypeError):
                        pass

        if stale_count == 0:
            print(f"✓ No stale in-progress beads (threshold: {self.stale_threshold_hours}h)")
        else:
            print(f"⚠ Found {stale_count} stale in-progress beads")

        return stale_count

    def check_missing_labels(self) -> int:
        """Check for beads without labels"""
        print("[4/5] Checking for missing labels...")

        missing_count = 0

        for bead in self.all_beads:
            labels = bead.get('labels', [])
            if not labels or labels == ['todo'] or labels == ['task']:
                missing_count += 1

                # Suggest label based on title
                suggested = self.suggest_label(bead['title'])

                warning = {
                    'type': 'missing_label',
                    'bead_id': bead['id'],
                    'bead_title': bead['title'],
                    'suggested_label': suggested
                }
                self.warnings.append(warning)

                if self.auto_fix:
                    # Ask for confirmation before applying
                    print(f"\n  Fix: {bead['id']} \"{bead['title']}\"")
                    print(f"  Suggested label: {suggested}")
                    response = input("  Apply fix? [y/N]: ")

                    if response.lower() == 'y':
                        try:
                            subprocess.run(
                                ['bd', 'update', bead['id'], '--label', suggested],
                                capture_output=True,
                                check=True
                            )
                            self.fixes_applied.append(f"Applied label '{suggested}' to {bead['id']}")
                            print(f"  ✓ Applied label '{suggested}' to {bead['id']}")
                        except subprocess.CalledProcessError:
                            print(f"  ✗ Failed to apply label")
                    else:
                        print(f"  ⊘ Skipped {bead['id']}")

        if missing_count == 0:
            print("✓ All beads have labels")
        else:
            print(f"⚠ Found {missing_count} beads without labels")

        return missing_count

    def suggest_label(self, title: str) -> str:
        """Suggest label based on bead title"""
        title_lower = title.lower()

        if 'approve' in title_lower or 'approval' in title_lower:
            return 'approval'
        elif 'implement' in title_lower or 'add' in title_lower or 'create' in title_lower:
            return 'implementation'
        elif 'document' in title_lower or 'docs' in title_lower:
            return 'documentation'
        elif 'test' in title_lower or 'verify' in title_lower:
            return 'verification'
        elif 'research' in title_lower or 'investigate' in title_lower:
            return 'research'
        elif 'milestone' in title_lower or 'epic' in title_lower:
            return 'milestone'
        elif 'fail' in title_lower or 'error' in title_lower:
            return 'failure'
        else:
            return 'implementation'  # Default

    def check_malformed_descriptions(self) -> int:
        """Check for malformed bead descriptions"""
        print("[5/5] Checking for malformed descriptions...")

        malformed_count = 0

        for bead in self.all_beads:
            # Handle both 'body' and 'description' keys
            body = bead.get('body', bead.get('description', ''))
            labels = bead.get('labels', [])

            # Check approval beads
            if 'approval' in labels and 'Plan:' not in body:
                malformed_count += 1
                self.warnings.append({
                    'type': 'malformed_approval',
                    'bead_id': bead['id'],
                    'bead_title': bead['title'],
                    'issue': 'Approval bead missing plan reference'
                })

            # Check failure beads
            if 'failure' in labels and 'Error Details:' not in body:
                malformed_count += 1
                self.warnings.append({
                    'type': 'malformed_failure',
                    'bead_id': bead['id'],
                    'bead_title': bead['title'],
                    'issue': 'Failure bead missing error details'
                })

            # Check for very short descriptions
            if len(body) < 20 and bead.get('status') != 'closed':
                malformed_count += 1
                self.warnings.append({
                    'type': 'short_description',
                    'bead_id': bead['id'],
                    'bead_title': bead['title'],
                    'issue': f'Very short description ({len(body)} chars)'
                })

        if malformed_count == 0:
            print("✓ All bead descriptions well-formed")
        else:
            print(f"⚠ Found {malformed_count} beads with malformed descriptions")

        return malformed_count

    def print_issues(self):
        """Print all issues found"""
        if not self.issues and not self.warnings:
            return

        print(f"\n{'='*60}")
        print("Issues Found")
        print(f"{'='*60}\n")

        # Print critical issues
        if self.issues:
            issue_num = 1

            # Group by type
            orphaned = [i for i in self.issues if i['type'] == 'orphaned']
            circular = [i for i in self.issues if i['type'] == 'circular']

            if orphaned:
                print(f"{issue_num}. Orphaned Dependencies ({len(orphaned)}):")
                for issue in orphaned:
                    print(f"   - {issue['bead_id']}: blocked by non-existent {issue['blocker_id']}")
                print("\n   Fix:")
                print("   bd dep remove <bead-id> <blocker-id>")
                print()
                issue_num += 1

            if circular:
                print(f"{issue_num}. Circular Dependencies ({len(circular)}):")
                for issue in circular:
                    cycle_str = ' -> '.join(issue['cycle'])
                    print(f"   - {cycle_str}")
                print("\n   Manual fix required:")
                print("   bd dep remove <child-id> <parent-id>")
                print()
                issue_num += 1

        # Print warnings
        if self.warnings:
            stale = [w for w in self.warnings if w['type'] == 'stale']
            missing_labels = [w for w in self.warnings if w['type'] == 'missing_label']
            malformed = [w for w in self.warnings if w['type'].startswith('malformed') or w['type'] == 'short_description']

            if stale:
                print(f"{len(self.issues) + 1}. Stale In-Progress Beads ({len(stale)}):")
                for warning in stale:
                    print(f"   - {warning['bead_id']}: in-progress for {warning['age_hours']}h (by {warning['assignee']})")
                print("\n   Review and either:")
                print("   - Close: bd update <id> --close")
                print("   - Unclaim: bd update <id> --unclaim")
                print()

            if missing_labels:
                print(f"{len(self.issues) + len(stale) + 1}. Missing Labels ({len(missing_labels)}):")
                for warning in missing_labels:
                    print(f"   - {warning['bead_id']}: \"{warning['bead_title']}\"")
                    print(f"     Suggested: bd update {warning['bead_id']} --label {warning['suggested_label']}")
                print()

            if malformed:
                print(f"{len(self.issues) + len(stale) + len(missing_labels) + 1}. Malformed Descriptions ({len(malformed)}):")
                for warning in malformed:
                    print(f"   - {warning['bead_id']}: {warning['issue']}")
                print("\n   Review and update descriptions manually")
                print()

    def print_summary(self):
        """Print summary of health check"""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        auto_fixable = sum(1 for i in self.issues if i['type'] == 'orphaned')

        print(f"{'='*60}")
        print("Summary")
        print(f"{'='*60}\n")

        if total_issues == 0 and total_warnings == 0:
            print("✅ No issues found - beads database is healthy!")
        else:
            print(f"Issues: {total_issues}")
            print(f"Warnings: {total_warnings}")

            if self.auto_fix:
                print(f"Fixes applied: {len(self.fixes_applied)}")
                for fix in self.fixes_applied:
                    print(f"  ✓ {fix}")
            else:
                print(f"Auto-fixable: {auto_fixable}")
                print(f"Manual fix required: {total_issues - auto_fixable + total_warnings}")
                print("\nRun with --fix to automatically fix safe issues")

    def output_json(self):
        """Output results as JSON"""
        output = {
            'issues': self.issues,
            'warnings': self.warnings,
            'fixes_applied': self.fixes_applied,
            'summary': {
                'total_issues': len(self.issues),
                'total_warnings': len(self.warnings),
                'critical_issues': len([i for i in self.issues if i['type'] == 'circular']),
                'auto_fixable': len([i for i in self.issues if i['type'] == 'orphaned'])
            }
        }
        print(json.dumps(output, indent=2))

    def run_checks(self, specific_check=None):
        """Run all health checks"""
        print("Beads Health Check")
        print(f"{'='*60}\n")

        if specific_check:
            if specific_check == 'orphaned':
                self.check_orphaned_beads()
            elif specific_check == 'circular':
                self.check_circular_dependencies()
            elif specific_check == 'stale':
                self.check_stale_in_progress()
            elif specific_check == 'labels':
                self.check_missing_labels()
            elif specific_check == 'descriptions':
                self.check_malformed_descriptions()
            else:
                print(f"Unknown check: {specific_check}")
                return False
        else:
            # Run all checks
            self.check_orphaned_beads()
            self.check_circular_dependencies()
            self.check_stale_in_progress()
            self.check_missing_labels()
            self.check_malformed_descriptions()

        return True


def main():
    parser = argparse.ArgumentParser(description='Detect and fix problems in beads database')
    parser.add_argument('--fix', action='store_true', help='Automatically fix safe issues')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--check', type=str, help='Run specific check only')
    parser.add_argument('--stale-threshold', type=int, default=24, help='Stale threshold in hours (default: 24)')
    parser.add_argument('--check-only', action='store_true', help='Check only, no output unless issues found')

    args = parser.parse_args()

    doctor = BeadsDoctor(auto_fix=args.fix, stale_threshold_hours=args.stale_threshold)

    # Load beads
    if not doctor.load_beads():
        sys.exit(1)

    # Run checks
    if not doctor.run_checks(specific_check=args.check):
        sys.exit(1)

    # Output results
    if args.json:
        doctor.output_json()
    else:
        if not args.check_only or (doctor.issues or doctor.warnings):
            doctor.print_issues()
            doctor.print_summary()

    # Exit code
    if doctor.issues:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
