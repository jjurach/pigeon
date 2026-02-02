# System Processes & Tools

This directory contains processes and tools for maintaining, validating, and improving the system-prompts infrastructure.

Unlike **workflows/** (which describe how agents execute tasks), **processes/** contains:

- **Automated scanning and validation tools**
- **Development environment setup and verification**
- **Quality assurance and integrity checking**
- **Documentation maintenance processes**

## Available Processes

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
