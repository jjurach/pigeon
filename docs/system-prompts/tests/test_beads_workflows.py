#!/usr/bin/env python3
"""
Tests for beads workflows

These tests verify the plan-and-dispatch workflow using beads.

NOTE: These tests require beads CLI to be installed:
    npm install -g @steveyegge/beads

Run tests:
    python3 -m unittest docs/system-prompts/tests/test_beads_workflows.py

Or:
    cd docs/system-prompts/tests
    python3 -m unittest test_beads_workflows.py
"""

import unittest
import subprocess
import tempfile
import shutil
import json
import re
from pathlib import Path


class TestBeadsWorkflows(unittest.TestCase):
    """Test beads workflows"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for each test
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()

        # Change to test directory
        import os
        os.chdir(self.test_dir)

        # Initialize git (required by beads)
        subprocess.run(['git', 'init'], capture_output=True, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], capture_output=True)

    def tearDown(self):
        """Clean up test environment"""
        import os
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def check_bd_available(self):
        """Check if bd CLI is available"""
        try:
            subprocess.run(['bd', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def extract_bead_id(self, output: str) -> str:
        """Extract bead ID from bd command output"""
        match = re.search(r'(bd-[a-z0-9]+)', output)
        if match:
            return match.group(1)
        return None

    def get_bead_status(self, bead_id: str) -> str:
        """Get bead status"""
        try:
            result = subprocess.run(
                ['bd', 'show', bead_id, '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            bead = json.loads(result.stdout)
            return bead.get('status', 'unknown')
        except Exception:
            return 'unknown'

    def test_init_beads_database(self):
        """Test: Initialize beads database"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Run bd init
        result = subprocess.run(['bd', 'init'], capture_output=True, text=True)

        # Verify .beads/ directory created
        self.assertTrue(Path('.beads').exists(), ".beads/ directory should exist")
        self.assertTrue(Path('.beads').is_dir(), ".beads/ should be a directory")

        # Verify bd ready works
        result = subprocess.run(['bd', 'ready'], capture_output=True, check=True)
        self.assertEqual(result.returncode, 0, "bd ready should work after init")

    def test_create_approval_bead_with_dependencies(self):
        """Test: Create approval bead that blocks implementation beads"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Initialize beads
        subprocess.run(['bd', 'init'], capture_output=True, check=True)

        # Create approval bead
        result = subprocess.run(
            ['bd', 'create', 'Approve: Test Plan', '--label', 'approval'],
            capture_output=True,
            text=True,
            check=True
        )
        approval_id = self.extract_bead_id(result.stdout)
        self.assertIsNotNone(approval_id, "Should extract approval bead ID")

        # Create implementation beads
        impl_ids = []
        for i in range(3):
            result = subprocess.run(
                ['bd', 'create', f'Implement Task {i+1}', '--label', 'implementation'],
                capture_output=True,
                text=True,
                check=True
            )
            impl_id = self.extract_bead_id(result.stdout)
            self.assertIsNotNone(impl_id, f"Should extract impl bead {i+1} ID")
            impl_ids.append(impl_id)

        # Add dependencies (tasks blocked by approval)
        for impl_id in impl_ids:
            subprocess.run(
                ['bd', 'dep', 'add', impl_id, approval_id],
                capture_output=True,
                check=True
            )

        # Verify implementation beads are "not ready" (blocked)
        for impl_id in impl_ids:
            status = self.get_bead_status(impl_id)
            self.assertEqual(status, 'not-ready', f"{impl_id} should be not-ready (blocked)")

        # Close approval bead
        subprocess.run(['bd', 'update', approval_id, '--close'], capture_output=True, check=True)

        # Verify approval bead is closed
        approval_status = self.get_bead_status(approval_id)
        self.assertEqual(approval_status, 'closed', "Approval bead should be closed")

        # Verify implementation beads are now "ready"
        for impl_id in impl_ids:
            status = self.get_bead_status(impl_id)
            self.assertEqual(status, 'ready', f"{impl_id} should be ready after approval closed")

    def test_worker_claim_and_close(self):
        """Test: Worker claims and closes bead"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Initialize beads
        subprocess.run(['bd', 'init'], capture_output=True, check=True)

        # Create ready bead
        result = subprocess.run(
            ['bd', 'create', 'Test Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        bead_id = self.extract_bead_id(result.stdout)
        self.assertIsNotNone(bead_id, "Should extract bead ID")

        # Verify bead is ready
        status = self.get_bead_status(bead_id)
        self.assertEqual(status, 'ready', "Bead should be ready")

        # Worker claims bead
        subprocess.run(['bd', 'update', bead_id, '--claim'], capture_output=True, check=True)

        # Verify bead is in-progress
        status = self.get_bead_status(bead_id)
        self.assertEqual(status, 'in-progress', "Bead should be in-progress after claim")

        # Worker closes bead
        subprocess.run(['bd', 'update', bead_id, '--close'], capture_output=True, check=True)

        # Verify bead is closed
        status = self.get_bead_status(bead_id)
        self.assertEqual(status, 'closed', "Bead should be closed")

    def test_failure_bead_creation(self):
        """Test: Worker creates failure bead on error"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Initialize beads
        subprocess.run(['bd', 'init'], capture_output=True, check=True)

        # Create work bead
        result = subprocess.run(
            ['bd', 'create', 'Test Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        work_id = self.extract_bead_id(result.stdout)
        self.assertIsNotNone(work_id, "Should extract work bead ID")

        # Worker claims work bead
        subprocess.run(['bd', 'update', work_id, '--claim'], capture_output=True, check=True)

        # Worker encounters failure, creates failure bead
        failure_body = f"""Original Task: {work_id}

Error Details:
Test error message

Recommendation:
Fix the error"""

        result = subprocess.run(
            ['bd', 'create', f'FAILURE: Test error in {work_id}', '--label', 'failure',
             '--body', failure_body],
            capture_output=True,
            text=True,
            check=True
        )
        failure_id = self.extract_bead_id(result.stdout)
        self.assertIsNotNone(failure_id, "Should extract failure bead ID")

        # Block work bead with failure bead
        subprocess.run(['bd', 'dep', 'add', work_id, failure_id], capture_output=True, check=True)

        # Worker unclaims work bead
        subprocess.run(['bd', 'update', work_id, '--unclaim'], capture_output=True, check=True)

        # Verify work bead is not-ready (blocked by failure)
        status = self.get_bead_status(work_id)
        self.assertEqual(status, 'not-ready', "Work bead should be blocked by failure")

        # Verify failure bead is ready
        failure_status = self.get_bead_status(failure_id)
        self.assertIn(failure_status, ['ready', 'not-ready'],
                      "Failure bead should exist with valid status")

    def test_planning_summary_output(self):
        """Test: planning-summary.py shows correct status"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Initialize beads
        subprocess.run(['bd', 'init'], capture_output=True, check=True)

        # Create beads in various states
        # 1. Closed bead
        result = subprocess.run(
            ['bd', 'create', 'Closed Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        closed_id = self.extract_bead_id(result.stdout)
        subprocess.run(['bd', 'update', closed_id, '--close'], capture_output=True, check=True)

        # 2. In-progress bead
        result = subprocess.run(
            ['bd', 'create', 'In Progress Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        in_progress_id = self.extract_bead_id(result.stdout)
        subprocess.run(['bd', 'update', in_progress_id, '--claim'], capture_output=True, check=True)

        # 3. Ready bead
        result = subprocess.run(
            ['bd', 'create', 'Ready Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        ready_id = self.extract_bead_id(result.stdout)

        # 4. Blocked bead
        result = subprocess.run(
            ['bd', 'create', 'Blocker', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        blocker_id = self.extract_bead_id(result.stdout)

        result = subprocess.run(
            ['bd', 'create', 'Blocked Task', '--label', 'implementation'],
            capture_output=True,
            text=True,
            check=True
        )
        blocked_id = self.extract_bead_id(result.stdout)
        subprocess.run(['bd', 'dep', 'add', blocked_id, blocker_id], capture_output=True, check=True)

        # Run planning-summary.py with JSON output
        summary_script = self.original_dir / 'docs' / 'system-prompts' / 'planning-summary.py'

        if not summary_script.exists():
            self.skipTest("planning-summary.py not found")

        result = subprocess.run(
            ['python3', str(summary_script), '--json'],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON output
        summary = json.loads(result.stdout)

        # Verify summary counts
        self.assertGreaterEqual(summary['summary']['closed'], 1, "Should have at least 1 closed bead")
        self.assertGreaterEqual(summary['summary']['in_progress'], 1, "Should have at least 1 in-progress bead")
        self.assertGreaterEqual(summary['summary']['ready'], 1, "Should have at least 1 ready bead")
        self.assertGreaterEqual(summary['summary']['blocked'], 1, "Should have at least 1 blocked bead")

    def test_sequential_dependencies(self):
        """Test: Sequential task dependencies (Phase 1 -> Phase 2 -> Phase 3)"""
        if not self.check_bd_available():
            self.skipTest("bd CLI not available")

        # Initialize beads
        subprocess.run(['bd', 'init'], capture_output=True, check=True)

        # Create 3 phases
        phase_ids = []
        for i in range(1, 4):
            result = subprocess.run(
                ['bd', 'create', f'Phase {i}', '--label', 'implementation'],
                capture_output=True,
                text=True,
                check=True
            )
            phase_id = self.extract_bead_id(result.stdout)
            self.assertIsNotNone(phase_id, f"Should extract phase {i} ID")
            phase_ids.append(phase_id)

        # Add sequential dependencies: Phase 2 blocks on Phase 1, Phase 3 blocks on Phase 2
        subprocess.run(['bd', 'dep', 'add', phase_ids[1], phase_ids[0]], capture_output=True, check=True)
        subprocess.run(['bd', 'dep', 'add', phase_ids[2], phase_ids[1]], capture_output=True, check=True)

        # Verify: Phase 1 ready, Phase 2 and 3 blocked
        self.assertEqual(self.get_bead_status(phase_ids[0]), 'ready', "Phase 1 should be ready")
        self.assertEqual(self.get_bead_status(phase_ids[1]), 'not-ready', "Phase 2 should be blocked")
        self.assertEqual(self.get_bead_status(phase_ids[2]), 'not-ready', "Phase 3 should be blocked")

        # Close Phase 1
        subprocess.run(['bd', 'update', phase_ids[0], '--close'], capture_output=True, check=True)

        # Verify: Phase 1 closed, Phase 2 ready, Phase 3 still blocked
        self.assertEqual(self.get_bead_status(phase_ids[0]), 'closed', "Phase 1 should be closed")
        self.assertEqual(self.get_bead_status(phase_ids[1]), 'ready', "Phase 2 should be ready after Phase 1 closed")
        self.assertEqual(self.get_bead_status(phase_ids[2]), 'not-ready', "Phase 3 should still be blocked")

        # Close Phase 2
        subprocess.run(['bd', 'update', phase_ids[1], '--close'], capture_output=True, check=True)

        # Verify: Phase 3 now ready
        self.assertEqual(self.get_bead_status(phase_ids[2]), 'ready', "Phase 3 should be ready after Phase 2 closed")


if __name__ == '__main__':
    # Check if bd is available before running tests
    try:
        subprocess.run(['bd', '--version'], capture_output=True, check=True)
        print("Beads CLI detected, running tests...\n")
        unittest.main()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: Beads CLI (bd) not found!")
        print("Install beads: npm install -g @steveyegge/beads")
        print("\nTests will be skipped.")
        sys.exit(0)
