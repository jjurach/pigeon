#!/usr/bin/env python3
"""
Planning Init - Initialize beads in a project

This script initializes beads task tracking with project-specific setup.

Usage:
    python3 docs/system-prompts/planning-init.py
"""

import os
import sys
import subprocess
from pathlib import Path


def check_prerequisites():
    """Check that prerequisites are met"""
    print("Checking prerequisites...")

    # Check if bd CLI is installed
    try:
        result = subprocess.run(['bd', '--version'], capture_output=True, text=True, check=True)
        print(f"✓ Beads CLI installed: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Beads CLI not installed")
        print("\nInstall beads:")
        print("  npm install -g @steveyegge/beads")
        return False

    # Check if git is initialized
    try:
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        print("✓ Git initialized")
    except subprocess.CalledProcessError:
        print("✗ Git not initialized")
        print("\nInitialize git:")
        print("  git init")
        return False

    return True


def check_if_already_initialized():
    """Check if beads is already initialized"""
    beads_dir = Path('.beads')

    if beads_dir.exists() and beads_dir.is_dir():
        print(f"\n{'='*60}")
        print("Beads already initialized!")
        print(f"{'='*60}")
        print("\nBeads database exists at: .beads/")
        print("\nTo re-initialize (WARNING: destroys existing beads):")
        print("  rm -rf .beads/")
        print("  python3 docs/system-prompts/planning-init.py")
        print("\nTo view current beads:")
        print("  bd ready")
        print("  python3 docs/system-prompts/planning-summary.py")
        return True

    return False


def initialize_beads():
    """Initialize beads database"""
    print("\nInitializing beads database...")

    try:
        result = subprocess.run(['bd', 'init'], capture_output=True, text=True, check=True)
        print("✓ Beads initialized")

        # Verify initialization
        if Path('.beads').exists():
            print("✓ .beads/ directory created")
        else:
            print("✗ .beads/ directory not found")
            return False

        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to initialize beads: {e}")
        print(e.stderr)
        return False


def create_label_documentation():
    """Create .beads/README.md documenting label conventions"""
    print("\nCreating label documentation...")

    readme_content = """# Beads Configuration

This project uses beads for task tracking with the plan-and-dispatch workflow.

## Bead Labels

This project uses the following bead label conventions:

### Core Labels

- **approval** - Blocks implementation until human reviews and approves plan
  - Created by planner
  - References project plan file
  - Implementation beads are `blocked_by` approval bead
  - Human closes approval bead when plan is approved

- **implementation** - Standard implementation work
  - Created by planner based on project plan phases
  - May have dependencies on other implementation beads
  - Worker claims, implements, and closes

- **milestone** - Groups related work (epic-level)
  - Uses hierarchical IDs (bd-a1b2 with subtasks bd-a1b2.1, bd-a1b2.2)
  - Closed when all subtasks complete

- **planning** - Converts inbox items into executable plans
  - Created when processing dev_notes/inbox
  - Closes when spec, plan, and beads created

- **research** - Investigation/discovery work (no code changes)
  - Closes when findings documented

- **verification** - Quality gates (e.g., "All tests pass")
  - Blocks deployment or release beads
  - Closes when verification criteria met

- **documentation** - Documentation work
  - Often `blocked_by` implementation beads
  - Closes when docs updated

- **worker-session** - Audit trail of worker agent sessions
  - Created by orchestrator (not manually)
  - Links to work beads via `relates_to`
  - Closes when worker session ends

- **failure** - Tracks worker failures requiring human intervention
  - Created by workers on non-trivial errors
  - Blocks original work bead until resolved
  - Human closes after fixing issue

## Workflow

See [Plan-and-Dispatch Workflow](../docs/system-prompts/workflows/plan-and-dispatch.md) for complete workflow documentation.

## Commands

```bash
# View ready beads
bd ready

# View all beads by status
python3 docs/system-prompts/planning-summary.py

# Detect issues
python3 docs/system-prompts/planning-doctor.py

# Create bead
bd create "Task title" --label <type>

# Show bead details
bd show <bead-id>

# Claim bead for work
bd update <bead-id> --claim

# Close bead
bd update <bead-id> --close

# Add dependency (child blocked by parent)
bd dep add <child-id> <parent-id>
```

## External Orchestrator

This project may use an external orchestrator to dispatch ready beads to worker agents.

See [External Orchestrator](../docs/system-prompts/workflows/external-orchestrator.md) for architecture details.
"""

    readme_path = Path('.beads/README.md')
    try:
        readme_path.write_text(readme_content)
        print(f"✓ Created {readme_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {readme_path}: {e}")
        return False


def verify_initialization():
    """Verify beads is working correctly"""
    print("\nVerifying initialization...")

    # Test: can we run bd ready?
    try:
        subprocess.run(['bd', 'ready'], capture_output=True, check=True)
        print("✓ bd ready command works")
    except subprocess.CalledProcessError:
        print("✗ bd ready command failed")
        return False

    # Test: can we create a test bead?
    try:
        result = subprocess.run(
            ['bd', 'create', 'TEST', '--label', 'test'],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract bead ID from output
        import re
        match = re.search(r'(bd-[a-z0-9]+)', result.stdout)
        if match:
            test_id = match.group(1)
            print(f"✓ Can create beads (created {test_id})")

            # Clean up test bead
            subprocess.run(['bd', 'update', test_id, '--close'], capture_output=True)
            return True
        else:
            print("⚠ Created bead but couldn't parse ID")
            return True  # Still consider success
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create test bead: {e}")
        return False


def print_next_steps():
    """Print next steps for user"""
    print(f"\n{'='*60}")
    print("Initialization Successful!")
    print(f"{'='*60}")
    print("\nBeads is now configured and ready to use.")
    print("\nNext steps:")
    print("  1. See docs/system-prompts/workflows/plan-and-dispatch.md for workflow")
    print("  2. Process inbox items with plan-and-dispatch workflow")
    print("  3. Use 'python3 docs/system-prompts/planning-summary.py' to view status")
    print("\nQuick start:")
    print("  bd create \"Task title\" --label implementation")
    print("  bd ready")
    print("  bd show <bead-id>")


def main():
    """Main execution"""
    print("Planning Init - Initialize Beads Task Tracking")
    print(f"{'='*60}\n")

    # Step 1: Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Step 2: Check if already initialized
    if check_if_already_initialized():
        sys.exit(0)

    # Step 3: Initialize beads
    if not initialize_beads():
        sys.exit(1)

    # Step 4: Create label documentation
    if not create_label_documentation():
        print("⚠ Label documentation not created (optional)")

    # Step 5: Verify initialization
    if not verify_initialization():
        print("\n⚠ Verification failed but beads may still work")
        print("Try running: bd ready")
        sys.exit(1)

    # Step 6: Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()
