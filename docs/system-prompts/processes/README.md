# System Processes & Tools

This directory contains processes and tools for maintaining, validating, and improving the system-prompts infrastructure, as well as reusable workflows for agent decision-making and human interaction.

Unlike **workflows/** (which describe how agents execute tasks), **processes/** contains:

- **Decision-making workflows** - Clarify questions, research, structured analysis
- **Automated scanning and validation tools**
- **Development environment setup and verification**
- **Quality assurance and integrity checking**
- **Documentation maintenance processes**

## Available Processes

### Bead Iteration (Interim Workflow)

**File:** [iterate-next-bead.md](./iterate-next-bead.md)

**Description:** Interim workflow for claiming, executing, and completing beads until the hatchery daemon is implemented. Provides multi-terminal coordination, stall detection, and safe bead progression.

**When to apply:**
- **Always** when working on hentown beads (interim until hatchery daemon Phase 3+)
- Automatically invoked when iterating on any bead-tracked work

**What it does:**
1. Inspects running agents using planning-running.py
2. Detects and recovers stalled beads (30-min timeout, PID-based health check)
3. Prevents multi-terminal collisions (refuses to grab beads owned by other live processes)
4. Determines if bead is interactive (research/decision) or non-interactive (task/feature)
5. Provides decision trees for all scenarios (all blocked, dead processes, interactive beads)
6. Guides execution, testing, and proper closure

**Key safeguards:**
- ✓ No duplicate work across terminals
- ✓ Automatic recovery of crashed agents
- ✓ Interactive bead awareness
- ✓ Multi-terminal safe PID-based coordination

**Related:** [planning-running.py](../planning-running.py) - Agent process inspector

---

### Clarify Questions

**File:** [clarify-questions.md](./clarify-questions.md)

**Description:** Research system state, identify improvement opportunities, synthesize 5 clarifying questions, and gather human input before major planning decisions.

**When to apply:**
- **Auto-trigger** on major epics, multi-phase implementations, cross-module integrations
- **Manual** on user request: "Apply clarify-questions.md to [scope]"

**What it does:**
1. Agent researches recent commits, closed beads, dev_notes
2. Synthesizes 5 questions across architecture, standards, documentation, maintainability, cross-module impact
3. Presents questions in structured markdown with context and options
4. Creates human gate (48h timeout) that blocks until answered
5. On resume: presents questions interactively (one-at-a-time)
6. Adjusts related beads based on answers

**Related:** [clarify-questions-template.md](./clarify-questions-template.md) - 5 universal question types with examples

---

## Infrastructure & Validation Processes

### Document Integrity Scan

**File:** [document-integrity-scan.md](./document-integrity-scan.md)

**Description:** Comprehensive process for ensuring documentation correctness and consistency.

**What it checks:**
1. **Referential Correctness** - All links point to existing files
2. **Architectural Constraints** - system-prompts doesn't reference back into project files without explicit marking
3. **Naming Conventions** - Files follow established naming patterns
4. **Directory Structure** - Tool guides are organized correctly (generic vs. project-specific)
5. **Coverage** - All documentation relationships are captured and verified

**Automated via:** `docscan.py` (see below)

### Close Project

**File:** [close-project.md](./close-project.md)

**Description:** Comprehensive process for properly completing and landing work before ending an agentic session.

**What it covers:**
1. **Definition of Done Verification** - All quality criteria are met
2. **Test Execution** - All tests pass before committing
3. **Change Documentation** - Audit trail is complete
4. **Git Commit** - Changes are properly saved with attribution
5. **Abort Criteria** - When to stop and request human intervention

**When to use:** At the end of any development session to ensure proper project closure.

## Automated Tools

### docscan.py

**Location:** `docs/system-prompts/docscan.py` (next to bootstrap.py)

**Purpose:** Automate the document integrity scan process so it's easily repeatable and extensible.

**Usage:**
```bash
# Run full scan
python3 docs/system-prompts/docscan.py

# Check specific aspect
python3 docs/system-prompts/docscan.py --check broken-links
python3 docs/system-prompts/docscan.py --check back-references

# Verbose output
python3 docs/system-prompts/docscan.py --verbose

# Strict mode (fail on warnings)
python3 docs/system-prompts/docscan.py --strict
```

## Design Principles

1. **Automation First** - Processes should be scriptable, not manual
2. **Extensibility** - New constraints and rules should be easy to add
3. **Clarity** - Each process documents its constraints explicitly
4. **Repeatability** - Processes produce consistent, verifiable results
5. **Transparency** - Results are human-readable and actionable

## Future Processes

- [ ] Workflow validation (ensure AGENTS.md references are correct)
- [ ] Tool capability verification (automated testing of tool guides)
- [ ] Configuration drift detection (config.example.json vs actual config)
- [ ] Cross-project consistency checker
- [ ] Template validation (ensure docs follow template structure)
