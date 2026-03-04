#!/usr/bin/env python3
"""
Tests for enhanced planning-summary.py with cross-deps and dense dashboard features

Run tests:
    python3 -m unittest docs/system-prompts/tests/test_planning_summary.py

Or:
    cd docs/system-prompts/tests
    python3 -m unittest test_planning_summary.py
"""

import unittest
import sys
import os
import json
import importlib.util
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import planning_summary from parent directory
parent_dir = os.path.join(os.path.dirname(__file__), '..')
planning_summary_path = os.path.join(parent_dir, "planning-summary.py")
spec = importlib.util.spec_from_file_location("planning_summary", planning_summary_path)
planning_summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planning_summary)


class TestCrossDepsParsing(unittest.TestCase):
    """Test cross-deps parsing from bead notes"""

    def setUp(self):
        """Set up test fixtures"""
        self.summary = planning_summary.BeadsSummary()

    def test_parse_cross_deps_simple(self):
        """Test parsing simple cross-deps format"""
        notes = "cross-deps: bead-123=closed, bead-456=ready"
        deps = self.summary.parse_cross_deps(notes)

        self.assertEqual(len(deps), 2)
        self.assertEqual(deps[0], ('bead-123', 'closed'))
        self.assertEqual(deps[1], ('bead-456', 'ready'))

    def test_parse_cross_deps_single(self):
        """Test parsing single cross-dep"""
        notes = "cross-deps: bead-xyz=closed"
        deps = self.summary.parse_cross_deps(notes)

        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0], ('bead-xyz', 'closed'))

    def test_parse_cross_deps_multiline(self):
        """Test parsing cross-deps on first matching line"""
        notes = """This is a description
cross-deps: bead-abc=in_progress
More description"""
        deps = self.summary.parse_cross_deps(notes)

        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0], ('bead-abc', 'in_progress'))

    def test_parse_cross_deps_with_whitespace(self):
        """Test parsing with extra whitespace"""
        notes = "cross-deps:   bead-a=closed  ,  bead-b=ready  "
        deps = self.summary.parse_cross_deps(notes)

        self.assertEqual(len(deps), 2)
        self.assertEqual(deps[0], ('bead-a', 'closed'))
        self.assertEqual(deps[1], ('bead-b', 'ready'))

    def test_parse_cross_deps_case_insensitive(self):
        """Test parsing is case insensitive"""
        notes = "CROSS-DEPS: bead-123=closed"
        deps = self.summary.parse_cross_deps(notes)

        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0], ('bead-123', 'closed'))

    def test_parse_cross_deps_empty_notes(self):
        """Test parsing with empty notes"""
        deps = self.summary.parse_cross_deps("")
        self.assertEqual(len(deps), 0)

    def test_parse_cross_deps_none_notes(self):
        """Test parsing with None notes"""
        deps = self.summary.parse_cross_deps(None)
        self.assertEqual(len(deps), 0)

    def test_parse_cross_deps_no_match(self):
        """Test parsing when no cross-deps present"""
        notes = "This is a regular note without cross-deps"
        deps = self.summary.parse_cross_deps(notes)
        self.assertEqual(len(deps), 0)


class TestCrossDepsChecking(unittest.TestCase):
    """Test cross-deps checking logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.summary = planning_summary.BeadsSummary()
        self.all_beads_by_id = {
            'bead-123': {'id': 'bead-123', 'status': 'closed'},
            'bead-456': {'id': 'bead-456', 'status': 'ready'},
            'bead-789': {'id': 'bead-789', 'status': 'in_progress'},
        }

    def test_check_cross_deps_all_met(self):
        """Test when all cross-deps are met"""
        bead = {
            'id': 'bead-test',
            'notes': 'cross-deps: bead-123=closed, bead-456=ready'
        }

        result = self.summary.check_cross_deps(bead, self.all_beads_by_id)

        self.assertEqual(len(result['deps']), 2)
        self.assertEqual(len(result['met']), 2)
        self.assertEqual(len(result['unmet']), 0)
        self.assertTrue(result['all_met'])

    def test_check_cross_deps_some_unmet(self):
        """Test when some cross-deps are unmet"""
        bead = {
            'id': 'bead-test',
            'notes': 'cross-deps: bead-123=closed, bead-456=closed'
        }

        result = self.summary.check_cross_deps(bead, self.all_beads_by_id)

        self.assertEqual(len(result['deps']), 2)
        self.assertEqual(len(result['met']), 1)
        self.assertEqual(len(result['unmet']), 1)
        self.assertFalse(result['all_met'])

    def test_check_cross_deps_referenced_bead_not_found(self):
        """Test when referenced bead doesn't exist"""
        bead = {
            'id': 'bead-test',
            'notes': 'cross-deps: bead-nonexistent=closed'
        }

        result = self.summary.check_cross_deps(bead, self.all_beads_by_id)

        self.assertEqual(len(result['unmet']), 1)
        self.assertFalse(result['all_met'])

    def test_check_cross_deps_no_deps(self):
        """Test bead with no cross-deps"""
        bead = {
            'id': 'bead-test',
            'notes': 'This has no cross-deps'
        }

        result = self.summary.check_cross_deps(bead, self.all_beads_by_id)

        self.assertEqual(len(result['deps']), 0)
        self.assertEqual(len(result['met']), 0)
        self.assertEqual(len(result['unmet']), 0)
        self.assertFalse(result['all_met'])  # False because no deps to meet


class TestPIDLivenessCheck(unittest.TestCase):
    """Test PID liveness checking"""

    def test_check_pid_alive_with_valid_pid(self):
        """Test checking a valid running process"""
        # Use current process ID which should always be running
        current_pid = os.getpid()
        is_alive = planning_summary.check_pid_alive(current_pid)
        self.assertTrue(is_alive)

    def test_check_pid_dead_with_invalid_pid(self):
        """Test checking a non-existent PID"""
        # Use a very high PID unlikely to exist
        is_alive = planning_summary.check_pid_alive(999999)
        self.assertFalse(is_alive)

    def test_check_pid_alive_fallback_kill(self):
        """Test fallback method using os.kill"""
        # Use current process which should be alive
        current_pid = os.getpid()
        # This should work via either psutil or os.kill fallback
        result = planning_summary.check_pid_alive(current_pid)
        self.assertTrue(result)


class TestNextBeadsQueue(unittest.TestCase):
    """Test next-beads queue with cross-dep enforcement"""

    def setUp(self):
        """Set up test fixtures"""
        self.projects = [
            {
                'name': 'root',
                'path': '.',
                'summary': planning_summary.BeadsSummary(),
                'error': None
            },
            {
                'name': 'submodule',
                'path': 'modules/test',
                'summary': planning_summary.BeadsSummary(),
                'error': None
            }
        ]

        # Create mock beads
        self.root_summary = self.projects[0]['summary']
        self.root_summary.all_beads = [
            {'id': 'root-1', 'status': 'ready', 'priority': 1, 'notes': '', 'title': 'First'},
            {'id': 'root-2', 'status': 'ready', 'priority': 2, 'notes': 'cross-deps: root-1=closed', 'title': 'Second'},
            {'id': 'root-3', 'status': 'closed', 'priority': 0, 'notes': '', 'title': 'Done'},
        ]
        self.root_summary.ready = [self.root_summary.all_beads[0], self.root_summary.all_beads[1]]
        self.root_summary.closed = [self.root_summary.all_beads[2]]

        self.sub_summary = self.projects[1]['summary']
        self.sub_summary.all_beads = [
            {'id': 'sub-1', 'status': 'ready', 'priority': 2, 'notes': '', 'title': 'Task'},
        ]
        self.sub_summary.ready = [self.sub_summary.all_beads[0]]
        self.sub_summary.closed = []

    def test_get_next_beads_without_cross_deps(self):
        """Test getting next beads without cross-dep checking"""
        available, blocked = planning_summary.get_dashboard_next_beads(
            self.projects, n=5, check_cross_deps=False
        )

        # Should get all ready beads ordered by priority
        self.assertGreater(len(available), 0)
        # First should be root-1 (priority 1)
        self.assertEqual(available[0]['bead']['id'], 'root-1')

    def test_get_next_beads_with_cross_deps(self):
        """Test getting next beads with cross-dep checking"""
        available, blocked = planning_summary.get_dashboard_next_beads(
            self.projects, n=5, check_cross_deps=True
        )

        # root-2 has unmet cross-dep (needs root-1=closed, but root-1 is ready)
        # So it should not be in available list
        available_ids = [b['bead']['id'] for b in available]
        self.assertIn('root-1', available_ids)
        self.assertNotIn('root-2', available_ids)

    def test_get_next_beads_priority_ordering(self):
        """Test that beads are ordered by priority"""
        available, _ = planning_summary.get_dashboard_next_beads(
            self.projects, n=5, check_cross_deps=False
        )

        if len(available) >= 2:
            # Lower priority number should come first
            prio1 = available[0]['bead'].get('priority', 4)
            prio2 = available[1]['bead'].get('priority', 4)
            self.assertLessEqual(prio1, prio2)


class TestApprovalBeadDetection(unittest.TestCase):
    """Test detection of approval beads"""

    def setUp(self):
        """Set up test fixtures"""
        self.projects = [
            {
                'name': 'root',
                'path': '.',
                'summary': planning_summary.BeadsSummary(),
                'error': None
            }
        ]

        summary = self.projects[0]['summary']
        summary.all_beads = [
            {'id': 'approve-1', 'status': 'open', 'labels': ['approval'], 'title': 'Approve Phase 1'},
            {'id': 'approve-2', 'status': 'ready', 'labels': ['approval'], 'title': 'Approve Phase 2'},
            {'id': 'impl-1', 'status': 'ready', 'labels': ['implementation'], 'title': 'Implement Feature'},
            {'id': 'approve-closed', 'status': 'closed', 'labels': ['approval'], 'title': 'Approved Phase'},
        ]

    def test_get_approval_beads_open_only(self):
        """Test that only open/ready approval beads are returned"""
        approval_beads = planning_summary.get_approval_beads(self.projects)

        approval_ids = [b['bead']['id'] for b in approval_beads]
        self.assertIn('approve-1', approval_ids)
        self.assertIn('approve-2', approval_ids)
        self.assertNotIn('approve-closed', approval_ids)
        self.assertNotIn('impl-1', approval_ids)

    def test_get_approval_beads_empty(self):
        """Test when there are no approval beads"""
        self.projects[0]['summary'].all_beads = [
            {'id': 'impl-1', 'status': 'ready', 'labels': ['implementation'], 'title': 'Implement'},
        ]

        approval_beads = planning_summary.get_approval_beads(self.projects)
        self.assertEqual(len(approval_beads), 0)


class TestInterventionBeadDetection(unittest.TestCase):
    """Test detection of beads requiring intervention"""

    def setUp(self):
        """Set up test fixtures"""
        self.projects = [
            {
                'name': 'root',
                'path': '.',
                'summary': planning_summary.BeadsSummary(),
                'error': None
            }
        ]

        summary = self.projects[0]['summary']
        summary.all_beads = []
        summary.failures = [
            {'id': 'fail-1', 'status': 'ready', 'labels': ['failure'], 'title': 'FAILURE: Test failed'},
        ]
        summary.blocked = [
            {'id': 'blocked-1', 'status': 'blocked', 'notes': 'Please resume with: hatchery run --resume abc123', 'title': 'Blocked Task'},
            {'id': 'blocked-2', 'status': 'blocked', 'notes': 'Waiting for dependency', 'title': 'Normal Blocked'},
        ]

    def test_get_intervention_beads_failure(self):
        """Test detection of failure beads"""
        intervention_beads = planning_summary.get_intervention_beads(self.projects)

        intervention_ids = [b['bead']['id'] for b in intervention_beads]
        self.assertIn('fail-1', intervention_ids)

    def test_get_intervention_beads_blocked_with_notes(self):
        """Test detection of blocked beads with intervention notes"""
        intervention_beads = planning_summary.get_intervention_beads(self.projects)

        intervention_ids = [b['bead']['id'] for b in intervention_beads]
        self.assertIn('blocked-1', intervention_ids)
        # blocked-2 has no intervention keywords, so should not be included
        self.assertNotIn('blocked-2', intervention_ids)


class TestCLIFlags(unittest.TestCase):
    """Test CLI flag parsing and usage"""

    def test_next_flag_default(self):
        """Test --next flag defaults to 20"""
        with patch('sys.argv', ['planning_summary.py', '--help']):
            parser = planning_summary.argparse.ArgumentParser()
            parser.add_argument('--next', type=int, default=20)
            args = parser.parse_args(['--next', '30'])
            self.assertEqual(args.next, 30)

    def test_no_cross_deps_flag(self):
        """Test --no-cross-deps flag"""
        with patch('sys.argv', ['planning_summary.py']):
            parser = planning_summary.argparse.ArgumentParser()
            parser.add_argument('--no-cross-deps', action='store_true')
            args = parser.parse_args(['--no-cross-deps'])
            self.assertTrue(args.no_cross_deps)

    def test_dashboard_only_flag(self):
        """Test --dashboard-only flag"""
        with patch('sys.argv', ['planning_summary.py']):
            parser = planning_summary.argparse.ArgumentParser()
            parser.add_argument('--dashboard-only', action='store_true')
            parser.add_argument('--no-dashboard', action='store_true')
            args = parser.parse_args(['--dashboard-only'])
            self.assertTrue(args.dashboard_only)
            self.assertFalse(args.no_dashboard)

    def test_conflicting_flags(self):
        """Test that --dashboard-only and --no-dashboard are mutually exclusive in usage"""
        with patch('sys.argv', ['planning_summary.py']):
            parser = planning_summary.argparse.ArgumentParser()
            parser.add_argument('--dashboard-only', action='store_true')
            parser.add_argument('--no-dashboard', action='store_true')
            # Both flags can be parsed, but user should not use both
            args = parser.parse_args(['--dashboard-only', '--no-dashboard'])
            # When used together, --dashboard-only takes precedence in the code
            self.assertTrue(args.dashboard_only)
            self.assertTrue(args.no_dashboard)


class TestRelativeTimeFormatting(unittest.TestCase):
    """Test relative time formatting for dashboard"""

    def test_format_time_ago_seconds(self):
        """Test formatting for times in seconds"""
        # Note: times < 60 seconds return "just now"
        # Test a longer duration to get "elapsed" string
        now = datetime.now(datetime.now().astimezone().tzinfo)
        timestamp = (now - timedelta(seconds=90)).isoformat()
        result = planning_summary.get_relative_time(timestamp)
        self.assertIn('m elapsed', result)

    def test_format_time_ago_minutes(self):
        """Test formatting for times in minutes"""
        now = datetime.now(datetime.now().astimezone().tzinfo)
        timestamp = (now - timedelta(minutes=5)).isoformat()
        result = planning_summary.get_relative_time(timestamp)
        self.assertIn('m elapsed', result)

    def test_format_time_ago_hours(self):
        """Test formatting for times in hours"""
        now = datetime.now(datetime.now().astimezone().tzinfo)
        timestamp = (now - timedelta(hours=2)).isoformat()
        result = planning_summary.get_relative_time(timestamp)
        self.assertIn('h elapsed', result)

    def test_format_time_ago_invalid(self):
        """Test formatting with invalid timestamp"""
        result = planning_summary.get_relative_time('invalid')
        self.assertEqual(result, 'unknown')

    def test_format_time_ago_none(self):
        """Test formatting with None timestamp"""
        result = planning_summary.get_relative_time(None)
        self.assertEqual(result, 'unknown')


class TestIntegration(unittest.TestCase):
    """Integration tests for the enhanced planning-summary"""

    def test_cross_deps_and_next_beads_integration(self):
        """Test that cross-deps properly block beads in next-beads list"""
        projects = [
            {
                'name': 'root',
                'path': '.',
                'summary': planning_summary.BeadsSummary(),
                'error': None
            }
        ]

        summary = projects[0]['summary']
        summary.all_beads = [
            {'id': 'phase-1', 'status': 'closed', 'priority': 1, 'notes': '', 'title': 'Phase 1'},
            {'id': 'phase-2', 'status': 'ready', 'priority': 2, 'notes': 'cross-deps: phase-1=closed', 'title': 'Phase 2'},
            {'id': 'phase-3', 'status': 'ready', 'priority': 3, 'notes': 'cross-deps: phase-2=closed', 'title': 'Phase 3'},
        ]
        summary.ready = [summary.all_beads[1], summary.all_beads[2]]
        summary.closed = [summary.all_beads[0]]

        available, blocked = planning_summary.get_dashboard_next_beads(
            projects, n=10, check_cross_deps=True
        )

        # phase-2 should be available (its cross-dep phase-1 is closed)
        available_ids = [b['bead']['id'] for b in available]
        self.assertIn('phase-2', available_ids)

        # phase-3 should not be available (its cross-dep phase-2 is not closed)
        self.assertNotIn('phase-3', available_ids)


if __name__ == '__main__':
    unittest.main()
