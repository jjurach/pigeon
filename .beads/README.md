# Beads Configuration

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
