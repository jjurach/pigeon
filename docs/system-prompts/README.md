# Agent Kernel: System Prompts Module

> **⚠️ IMPORTANT: Generic Documentation**
>
> This entire `docs/system-prompts/` directory contains **generic, reusable documentation** designed to work across any project using the AGENTS.md workflow. It should **never** contain project-specific references (module names, file paths, architecture details).
>
> **For project-specific documentation:** Use `docs/` (outside of system-prompts/) or other project directories.

The **Agent Kernel** is a reusable, standardized collection of agentic workflow guidelines and patterns. It provides a foundation for consistent AI agent behavior across projects.

## Overview

This directory contains the "ideal state" documentation for:
- **Workflow Principles** - The core A-E workflow and unbreakable rules
- **Definition of Done** - Universal and language-specific completion criteria
- **Prompt Patterns** - Proven templates for effective AI prompts

## Directory Structure

```
docs/system-prompts/
├── bootstrap.py                 # Tool to inject/maintain sections in AGENTS.md
├── docscan.py                   # Document integrity scanner
├── planning-running.py          # Inspect running AI agent processes
├── README.md                    # This file
├── principles/
│   └── definition-of-done.md    # Universal DoD criteria
├── processes/
│   ├── README.md                # Processes directory guide
│   ├── bootstrap-project.md     # Agent Kernel integration process
│   ├── document-integrity-scan.md # Documentation verification process
│   └── tool-entry-points.md     # Tool entry point architecture
├── tools/
│   ├── README.md                # Tools directory guide
│   ├── aider.md                 # Aider specific guide
│   ├── claude-code.md           # Claude Code specific guide
│   ├── cline.md                 # Cline specific guide
│   └── gemini.md                # Gemini specific guide
├── workflows/                   # Workflow patterns (Core + Optional)
│   ├── README.md                # Workflows directory guide
│   ├── core.md                  # Core A-E workflow + Unbreakable Rules
│   ├── logs-first.md            # Documented development workflow
│   └── custom-template.md       # Template for creating custom workflows
├── patterns/
│   └── prompt-patterns.md       # Prompt templates for consistent results
├── templates/
│   ├── README.md                # Templates directory guide
│   └── structure.md             # Documentation templates (specs, plans, changes)
├── guides/
│   ├── beads-sticky-attribute.md   # Understanding beads as sticky attribute
│   └── agent-beads-detection.md    # How agents detect and use beads
└── languages/
    └── python/
        └── definition-of-done.md # Python-specific DoD (pytest, venv, etc.)
```

## Tool Entry Points

The project uses "anemic" tool entry points in the root directory that redirect to comprehensive guides in `docs/system-prompts/tools/`.

**Entry Point Files:**
- `.aider.md` → `docs/system-prompts/tools/aider.md`
- `.claude/CLAUDE.md` → `docs/system-prompts/tools/claude-code.md`
- `.clinerules` → `docs/system-prompts/tools/cline.md`
- `.gemini/GEMINI.md` → `docs/system-prompts/tools/gemini.md`

**Management:**
These files are managed by `bootstrap.py`:
- **Validation:** `python3 docs/system-prompts/bootstrap.py --validate-tool-entries`
- **Regeneration:** `python3 docs/system-prompts/bootstrap.py --regenerate-tool-entries --commit`

See `docs/system-prompts/processes/tool-entry-points.md` for the complete architecture.

## Guides

The `docs/system-prompts/guides/` directory contains implementation guides for agents:

1. **Beads Sticky Attribute** (`beads-sticky-attribute.md`)
   - Explains when beads becomes active for a project
   - Shows how beads persists across sessions
   - Decision tree for agents to detect beads status

2. **Agent Beads Detection** (`agent-beads-detection.md`)
   - Quick start checklist for detecting beads at session start
   - How to decide whether to use beads in project plans
   - Common scenarios and troubleshooting

## Processes

The `docs/system-prompts/processes/` directory documents maintenance workflows:

1.  **Bootstrap Project** (`bootstrap-project.md`)
    - Complete process for integrating Agent Kernel into new projects
    - Phase 6.5 covers beads initialization (optional, if requested)
    - Ensures clear content ownership and no duplication

2.  **Document Integrity Scan** (`document-integrity-scan.md`)
    - Describes how `docscan.py` validates the documentation graph.
    - Ensures no broken links or orphaned files.

3.  **Tool Entry Points** (`tool-entry-points.md`)
    - Describes the "Anemic Entry Point" pattern.
    - Explains how to add support for new AI tools.

## Core Concept

The Agent Kernel separates **generic** guidance (applicable to all projects) from **language-specific** guidance (e.g., Python pytest, JavaScript npm). Each project maintains its own `AGENTS.md` file, which can be:

1. **Bootstrapped** with kernel content via `bootstrap.py`
2. **Extended** with project-specific rules
3. **Kept in sync** when the kernel evolves

## Using the Bootstrap Tool

### Quick Start

```bash
# From project root, ensure AGENTS.md exists
# Then run:
python3 docs/system-prompts/bootstrap.py

# By default, this is a DRY RUN - no changes made
# To actually apply changes:
python3 docs/system-prompts/bootstrap.py --commit
```

### Available Commands

```bash
# Dry-run mode (default) - shows what would happen
python3 bootstrap.py

# Apply changes to AGENTS.md
python3 bootstrap.py --commit

# Overwrite locally modified sections (use with caution)
python3 bootstrap.py --commit --force

# Analyze without changes
python3 bootstrap.py --analyze

# Specify a different project root
python3 bootstrap.py --root /path/to/project --commit

# Workflow Commands (Optional Workflows)
python3 bootstrap.py --analyze-workflow        # Show workflow state and recommendation
python3 bootstrap.py --enable-logs-first --commit   # Enable logs-first workflow
python3 bootstrap.py --disable-logs-first --commit  # Disable logs-first workflow
```

### How It Works

1. **Detection:** Identifies project language (Python, JavaScript, etc.)
2. **Comparison:** Reads current `AGENTS.md` and compares to ideal state
3. **Smart Updates:**
   - **Unmodified sections:** Overwrites with latest ideal state
   - **Modified sections:** Warns and skips (unless `--force` used)
   - **Missing sections:** Adds them
4. **Safe by Default:** Dry-run mode is the default; use `--commit` to write

### Link Transformation

Bootstrap automatically transforms relative markdown links when assembling `AGENTS.md` from component files in `docs/system-prompts/`. This ensures links work correctly in both the source files (where they're edited) and the assembled `AGENTS.md` (where agents read them).

**How it works:**
- Source files can use relative links that work in their location (e.g., `../definition-of-done.md`)
- During assembly, links are automatically rewritten to work from `AGENTS.md`'s location at the project root

**Example transformation:**
```markdown
# In docs/system-prompts/mandatory-reading.md (source)
[Definition of Done](../definition-of-done.md)

# After assembly in AGENTS.md (at root)
[Definition of Done](docs/definition-of-done.md)
```

**What gets transformed:**
- Relative paths with `../` or `./` prefixes
- Anchors are preserved: `../file.md#section` → `docs/file.md#section`

**What stays unchanged:**
- External URLs: `https://example.com`
- Absolute paths: `/absolute/path`
- Self-references: `#anchor-only`
- Non-relative paths: `file.md` (no prefix)

**Benefits:**
- Source files remain navigable in IDEs and GitHub
- Assembled `AGENTS.md` has working links for AI agents
- Bootstrap process is truly idempotent
- No manual link maintenance required

## Testing Agent Kernel Tools

The Agent Kernel includes a comprehensive test suite for `bootstrap.py` and `docscan.py`. Tests are located in `docs/system-prompts/tests/` and use Python's standard library only—no external dependencies required.

### Running Tests

**Run all tests:**
```bash
python3 -m unittest discover -s docs/system-prompts/tests -p "test_*.py"
```

**Run specific test suite:**
```bash
python3 docs/system-prompts/tests/test_docscan.py              # Test document scanner
python3 docs/system-prompts/tests/test_bootstrap.py            # Test bootstrap tool
python3 docs/system-prompts/tests/test_link_transformation.py  # Test link transformation
```

**Using the test runner script:**
```bash
./docs/system-prompts/tests/run_tests.sh              # Run all tests
./docs/system-prompts/tests/run_tests.sh docscan      # Run docscan tests only
./docs/system-prompts/tests/run_tests.sh bootstrap    # Run bootstrap tests only
./docs/system-prompts/tests/run_tests.sh -v           # Verbose output
```

### What Tests Cover

**docscan.py Tests:**
- Anchor extraction (explicit `{#id}`, auto-generated from headings, HTML anchors)
- Link target resolution (file paths + anchors)
- Broken link detection (missing files, missing anchors)
- Conditional link handling
- External URL handling
- Mandatory reading anchor validation

**bootstrap.py Tests:**
- Section marker validation (matching pairs, no duplicates, proper formatting)
- Section extraction and updates
- Project language detection (Python, JavaScript, unknown)
- Project root detection
- MANDATORY-READING section handling
- Safe update operations with force flag

**Link Transformation Tests:**
- Parent directory links (`../file.md` → `docs/file.md`)
- Anchor preservation (`../file.md#section` → `docs/file.md#section`)
- External URL preservation (`https://example.com` unchanged)
- Absolute path preservation (`/absolute/path` unchanged)
- Self-reference preservation (`#anchor` unchanged)
- Current directory links (`./file.md` transformation)
- Edge cases (multiple parent traversals, complex anchors)

### Test Requirements

**When Adding New Features:**

1. **Update Tests When Adding Features**
   - If you add new functionality to `bootstrap.py` or `docscan.py`, you MUST add corresponding tests
   - This prevents regressions and documents expected behavior
   - Tests serve as executable documentation

2. **Test Coverage Expectations**
   - New methods should have unit tests
   - Edge cases should be tested (malformed input, missing files, etc.)
   - Happy path and error paths should both be covered

3. **Running Tests Before Committing**
   ```bash
   # Before committing changes to bootstrap.py or docscan.py:
   python3 -m unittest discover -s docs/system-prompts/tests -p "test_*.py"

   # All tests must pass before commit
   ```

4. **Backwards Compatibility**
   - New tests should not break existing tests
   - If you change behavior, update the corresponding tests
   - Ensure new features work with existing projects

### Test Structure

```
docs/system-prompts/tests/
├── __init__.py                    # Test module initialization
├── test_docscan.py               # Document scanner tests (~400 lines, 8 test classes)
├── test_bootstrap.py             # Bootstrap tool tests (~350 lines, 6 test classes)
└── run_tests.sh                  # Test runner script
```

### Adding Tests

To add tests for new features:

1. Identify which file your feature is in (`docscan.py` or `bootstrap.py`)
2. Open the corresponding test file (`test_docscan.py` or `test_bootstrap.py`)
3. Add a new test class or add methods to an existing class:

```python
class TestMyNewFeature(unittest.TestCase):
    """Test description of the feature."""

    def setUp(self):
        """Initialize test environment."""
        # Create temporary files/directories as needed
        pass

    def tearDown(self):
        """Clean up test artifacts."""
        pass

    def test_happy_path(self):
        """Test normal operation."""
        # Test code
        self.assertEqual(expected, actual)

    def test_edge_case(self):
        """Test edge cases or error conditions."""
        # Test code
        self.assertRaises(SomeException, function_call)
```

4. Run tests to verify:
```bash
python3 docs/system-prompts/tests/test_docscan.py -v
```

### No External Dependencies

All tests use Python's standard library:
- `unittest` - Test framework
- `tempfile` - Temporary test files
- `pathlib` - File path handling
- `sys` - Module imports
- `re` - Regular expressions (already used by bootstrap.py and docscan.py)

This ensures tests run on any Python 3.x installation without setup overhead.

## Understanding Workflows

The Agent Kernel includes optional **Workflows**—sets of instructions that govern how AI agents approach development tasks. Projects can enable, disable, or create custom workflows.

### What is Logs-First Workflow?

The **logs-first workflow** emphasizes documentation and accountability through three connected documents:

1. **Spec File** (`dev_notes/specs/YYYY-MM-DD_HH-MM-SS_spec-*.md`)
   - Documents user intentions and requirements
   - Example: "Add user authentication to the app"
   - Simple outline with acceptance criteria

2. **Project Plan** (`dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_plan-*.md`)
   - Details the implementation strategy
   - Broken into phases with specific tasks
   - Requires explicit developer approval before work begins

3. **Change Documentation** (`dev_notes/changes/YYYY-MM-DD_HH-MM-SS_change-*.md`)
   - Proof that work was completed correctly
   - Includes actual test output, coverage metrics
   - References the approved plan

**When Logs-First is Enabled:**
- AGENTS.md includes the complete logs-first workflow (inserted between `<!-- SECTION: LOGS-FIRST-WORKFLOW -->` markers)
- AI agents automatically follow the three-document pattern for non-trivial tasks
- The workflow state is tracked in AGENTS.md via `<!-- BOOTSTRAP-STATE: logs_first=enabled -->`
- Developers expect agents to ask for approval before implementing plans
- Definition of Done checklist includes verification requirements

**When Logs-First is Disabled:**
- The LOGS-FIRST-WORKFLOW section is removed from AGENTS.md
- Agents fall back to basic guidelines (core workflow, universal DoD)
- Less structured development allowed
- Suitable for large projects or teams with different needs

### Opt-In Logs-First Per-Task

Even when logs-first is **not** enabled project-wide, you can opt-in to the workflow for specific tasks by including a special marker in your spec file.

**When to use:** For complex features, architectural changes, or cross-cutting concerns where you want structured planning and approval gates.

**How to opt-in:** Add this marker to your spec file:

```markdown
# Spec: Add Dark Mode Support

**Workflow:** @logs-first

**Date:** 2026-01-26

## User Request
- Add dark mode toggle to GUI
- Save preference to config
- Auto-detect system theme on startup

## Goals
- Improve UX for users in dark environments
- Follow existing config patterns

## Acceptance Criteria
- [ ] Dark mode toggle appears in settings
- [ ] Preference persists between sessions
- [ ] All UI elements are readable in dark mode
- [ ] Tests verify toggle functionality
```

**What the `@logs-first` marker does:**
- Signals to agents that this task requires the full logs-first workflow
- Agent will ask you to create a Project Plan before implementing
- Agent will wait for explicit approval before starting work
- Agent will track changes in Change Documentation files
- Ensures structured decision-making for this specific feature

**Without the marker:**
- Agents use standard workflow (Steps A-E)
- Less structured documentation required
- Faster path to implementation
- Still follows quality standards

**Benefits of opt-in approach:**
- ✅ Gradual team adoption - no forced complexity
- ✅ Per-task control - use for important features only
- ✅ Natural learning - team sees the workflow in action
- ✅ Flexibility - different features can have different rigor
- ✅ No surprises - developers see the marker and know what to expect

**Example workflow with opt-in:**

```markdown
# Spec: Add Dark Mode Support

**Workflow:** @logs-first

[rest of spec...]
```

When the agent sees `@logs-first`, it will:
1. Acknowledge the marker
2. Ask you to approve the approach
3. Request a Project Plan before implementation
4. Track all changes in dev_notes/changes/
5. Verify completion against Definition of Done

**For simple tasks, skip the marker:**

```markdown
# Spec: Fix typo in README

[rest of spec...]
```

No `@logs-first` marker means:
- Standard workflow applies
- Faster iteration
- Less documentation overhead
- Still maintains quality standards

### Decision Tree: To Enable or Not?

- **Is the project small (< 200 files)?** → Consider enabling logs-first
- **Are you value detailed decision history?** → Enable logs-first
- **Is the team > 10 people?** → Consider disabling or custom workflow
- **Do you just want the option to use logs-first sometimes?** → Leave disabled and use manually

### Logs-First Benefits

When used (enabled or manually):
- ✅ Complete audit trail of decisions
- ✅ Prevents miscommunication via formal plans
- ✅ Makes onboarding easier (new devs understand the "why")
- ✅ Reduces rework when plans are discussed upfront
- ✅ Proof of correctness via verification in change docs

### Logs-First Trade-offs

- ⚠️ More documentation overhead (3 documents per feature)
- ⚠️ Slower time-to-first-code (planning before implementation)
- ⚠️ Not ideal for rapid prototyping or one-off scripts
- ⚠️ Requires discipline from team to follow patterns

### Custom Workflows

You can create custom workflows (lighter, heavier, or specialized) using the template:
- See `docs/system-prompts/workflows/custom-template.md`
- Register in `bootstrap.py`
- Enable/disable like logs-first

---

## Section Markers

The bootstrap tool uses HTML comments to mark managed sections:

```markdown
<!-- SECTION: CORE-WORKFLOW -->
... section content ...
<!-- END-SECTION -->
```

Only content between these markers is managed. Project-specific rules can be added in a separate section:

```markdown
<!-- SECTION: PROJECT-SPECIFIC -->
This project uses:
- dev_notes/ for tracking
- config.example.json for config keys
... (your project rules) ...
<!-- END-SECTION -->
```

## Content Included

### 1. Workflow Core (`workflow/core.md`)
- **Steps A-E:** Analyze, Spec, Plan, Await Approval, Implement & Document
- **Unbreakable Rules:** Approval, Quality, Uncertainty, File Naming, Temp Files, Slack Notifications

### 2. Universal Definition of Done (`principles/definition-of-done.md`)
- Plan vs. Reality protocol
- Verification as data
- Codebase state integrity
- Agent handoff patterns

### 3. Python Definition of Done (`languages/python/definition-of-done.md`)
- Environment & dependencies (venv, requirements.txt, pyproject.toml)
- Testing with pytest
- Code quality standards
- File organization
- Fixtures and mocking
- Python version compatibility

### 4. Documentation Templates (`templates/structure.md`)
- Spec File Template (user intentions & requirements)
- Project Plan Template (implementation strategy)
- Change Documentation Template (proof of work)
- Best practices, naming conventions, and state transitions

### 5. Prompt Patterns (`patterns/prompt-patterns.md`)
- Request Analysis Pattern
- Planning & Design Pattern
- Implementation Pattern
- Verification Pattern
- Debugging Pattern
- Documentation Pattern
- Code Review Pattern
- Testing Pattern
- Integration/System Pattern
- And more...

## Project-Specific Extensions

Your project can extend the kernel with project-specific rules. Example:

```markdown
# MANDATORY AI Agent Instructions (Condensed)

<!-- SECTION: CORE-WORKFLOW -->
... (injected by bootstrap.py) ...
<!-- END-SECTION -->

<!-- SECTION: PROJECT-SPECIFIC -->

## Project-Specific Rules

1. **Development Notes:**
   - Use `dev_notes/specs/` for specification files
   - Use `dev_notes/project_plans/` for formal plans
   - Use `dev_notes/changes/` for implementation tracking

2. **Configuration:**
   - All config keys MUST be defined in `config.example.json`
   - Never hardcode secrets or API keys
   - Environment variables take precedence

3. **Documentation:**
   - API docs in `docs/api/`
   - Architecture decisions in `docs/adr/`
   - Implementation guides in `docs/implementation-reference.md`

<!-- END-SECTION -->
```

## Keeping Synchronized

To update your project when the kernel evolves:

```bash
# Check what would change
python3 docs/system-prompts/bootstrap.py --analyze

# Apply updates
python3 docs/system-prompts/bootstrap.py --commit

# Verify no critical info was lost
git diff AGENTS.md
```

## Safety Considerations

- **Dry Run First:** Always review with `--analyze` or dry-run
- **Backup:** Keep git history for easy rollback
- **Project-Specific:** Use `<!-- SECTION: PROJECT-SPECIFIC -->` for rules you want to keep
- **Modified Sections:** Bootstrap warns before overwriting custom content
- **Use `--force` Carefully:** This skips modification warnings

## Supported Languages

Currently supported language-specific content:
- **Python:** Definition of Done with pytest, venv, requirements management
- **JavaScript:** (Coming soon)
- **Go:** (Coming soon)

## Extending the Kernel

To add new patterns or guidelines to the kernel:

1. Create/modify files in `docs/system-prompts/`
2. Update `bootstrap.py` if needed to reference new sections
3. Commit and push the changes
4. Projects using the kernel can pull the latest version

## Troubleshooting

**Problem:** Bootstrap can't find project root
```bash
# Explicitly specify root
python3 bootstrap.py --root /path/to/project --analyze
```

**Problem:** AGENTS.md doesn't exist
```bash
# Create a basic one first
echo "# MANDATORY AI Agent Instructions" > AGENTS.md

# Then run bootstrap
python3 bootstrap.py --commit
```

**Problem:** Sections aren't being updated
```bash
# Check project language detection
python3 bootstrap.py --analyze

# Use --force to overwrite any modified sections
python3 bootstrap.py --commit --force
```

**Problem:** Want to keep custom section
```markdown
<!-- SECTION: MY-CUSTOM-SECTION -->
This won't be touched by bootstrap
<!-- END-SECTION -->
```

## Customizing for Your Project

The Agent Kernel is **generic and reusable**. To adopt it in a new project:

### 1. Choose Your Planning Directory

The kernel references `[PLANNING_DIR]` as a placeholder. Choose your naming:
- **Option A:** `dev_notes/` (recommended, matches examples in this kernel)
- **Option B:** `docs/planning/`
- **Option C:** `.ai-plans/`
- **Option D:** Any other directory structure

Your AGENTS.md should document which convention you chose.

### 2. Create Project-Specific Documentation

After adopting the kernel, create these files:
- `docs/templates.md` - Copy from `docs/system-prompts/templates/structure.md` if customizing the structure
- `docs/implementation-reference.md` - Implementation patterns for your tech stack
- `docs/file-naming-conventions.md` - Your project's file naming rules (if different from the kernel)

### 3. Document Your Configuration Format

Update your `config.example.json` (or `.env.example`, `config.sample.yaml`, etc.) to document configuration keys. The kernel references this in the Definition of Done.

### 4. Language-Specific Setup

- **Python projects:** Use `docs/system-prompts/languages/python/definition-of-done.md` as-is (no changes needed)
- **JavaScript/Node projects:** Create similar guidance in `docs/system-prompts/languages/javascript/definition-of-done.md`
- **Other languages:** Create language-specific DoD following the Python structure

### 5. Project-Specific Rules

Add a `PROJECT-SPECIFIC` section to your AGENTS.md (see "Project-Specific Extensions" above) to document:
- Your planning directory choice
- Configuration management practices
- Code style/formatting requirements
- Custom patterns or tools

---

## Integration with Claude Code

The Agent Kernel is designed to work with [Claude Code](https://github.com/anthropics/claude-code) and other AI development tools.

To use in a new project:

1. Add `docs/system-prompts/` to your repo (or use as git submodule)
2. Create/initialize `AGENTS.md`
3. Run `python3 docs/system-prompts/bootstrap.py --commit`
4. Customize with project-specific rules
5. Commit the updated `AGENTS.md`

## Understanding the System

**Start here:** `docs/system-prompts/reference-architecture.md`
- Explains how all files reference each other
- Documents safety guardrails for logs-first workflow
- Shows what happens when logs-first is enabled vs disabled

## Related Resources

- `docs/system-prompts/principles/definition-of-done.md` - Detailed universal DoD
- `docs/system-prompts/languages/python/definition-of-done.md` - Python-specific requirements
- `docs/system-prompts/templates/structure.md` - Templates for specs, plans, and changes
- `docs/system-prompts/patterns/prompt-patterns.md` - Universal prompt patterns
- `AGENTS.md` - Your project's customized agent instructions (generated by bootstrap.py)
- `docs/workflows.md` - User guide for managing workflows

## Available Workflows and Processes

**IMPORTANT:** These workflows and processes are **informational resources only**. AI agents should **NOT** execute these processes unless explicitly requested by the user or referenced in agent instructions (e.g., AGENTS.md, CLAUDE.md, etc.).

### Workflows

Workflows define how development work should be structured. Located in `docs/system-prompts/workflows/`:

**Core Workflow (Built-in to AGENTS.md)**
- **File:** `workflows/core.md`
- **Purpose:** The standard A-E workflow (Analyze, Build, Code, Document, Evaluate)
- **Usage:** Automatically included in AGENTS.md via bootstrap.py
- **Activation:** Always active (default workflow)

**Logs-First Workflow (Optional)**
- **File:** `workflows/logs-first.md`
- **Purpose:** Defensive workflow requiring human approval before any file writes
- **Usage:** Enable by setting `WORKFLOW=logs-first` in project config or AGENTS.md
- **Activation:** User must explicitly enable
- **When to use:** High-risk projects, paranoid mode, learning/training scenarios

**Custom Workflow Template**
- **File:** `workflows/custom-template.md`
- **Purpose:** Template for creating project-specific custom workflows
- **Usage:** Copy and modify to create custom workflow for your project
- **Activation:** Reference in AGENTS.md

**Workflows Directory Guide**
- **File:** `workflows/README.md`
- **Purpose:** Overview of workflow system and how to choose/customize workflows
- **Usage:** Reference documentation for understanding workflow architecture

### Processes

Processes are specialized, one-time or periodic maintenance operations. Located in `docs/system-prompts/processes/`:

**Bootstrap Project (One-Time)**
- **File:** `processes/bootstrap-project.md`
- **Purpose:** Complete process for integrating Agent Kernel into a new project
- **Usage:** Run once when importing system-prompts into a new project
- **Invocation:** User must explicitly request: "Follow the bootstrap-project process"
- **Duration:** 6-7 phases, typically 15-20 file operations
- **Output:** Integrated documentation with 0 TODOs, 0 broken links, clear content ownership

**Document Integrity Scan (Periodic)**
- **File:** `processes/document-integrity-scan.md`
- **Purpose:** Comprehensive documentation quality check (broken links, formatting, references)
- **Usage:** Run periodically or before major releases
- **Invocation:** Run via `python3 docs/system-prompts/docscan.py` or when user requests integrity check
- **Output:** Report of broken links, formatting issues, and documentation problems

**Tool Entry Points (Maintenance)**
- **File:** `processes/tool-entry-points.md`
- **Purpose:** Process for creating/maintaining tool-specific entry files (CLAUDE.md, AIDER.md, etc.)
- **Usage:** When adding new AI development tool support to project
- **Invocation:** User must explicitly request: "Create entry point for [tool]"
- **Output:** New [TOOL].md entry file following anemic file pattern

**Processes Directory Guide**
- **File:** `processes/README.md`
- **Purpose:** Overview of available processes and when to use them
- **Usage:** Reference documentation

### When to Use These Resources

**For Humans (Project Maintainers):**
- Reference these documents to understand available workflows and processes
- Choose workflows based on project risk profile and team preferences
- Run processes manually when needed (bootstrap, integrity scans, etc.)

**For AI Agents:**
- **DO NOT** execute processes unless explicitly requested by user
- **DO NOT** switch workflows unless instructed in AGENTS.md or by user
- **DO** reference workflow/process documentation when user asks about them
- **DO** suggest relevant processes when user describes a problem they solve (e.g., "Would you like me to run the document integrity scan process?")

### Process Invocation Examples

**Correct invocations (user explicitly requests):**
- "Follow the bootstrap-project process in `docs/system-prompts/processes/bootstrap-project.md`"
- "Run the document integrity scan"
- "Create a Claude Code entry point following the tool-entry-points process"
- "Switch to logs-first workflow" (requires AGENTS.md modification)

**Incorrect invocations (agent decides on its own):**
- ❌ Agent notices broken links and runs bootstrap-project without being asked
- ❌ Agent decides project needs integrity scan and runs it proactively
- ❌ Agent switches workflows because it thinks logs-first is "better"
- ❌ Agent executes any process from system-prompts without explicit user request

### Quick Reference

| Resource | Type | Invocation | Duration |
|----------|------|------------|----------|
| Core Workflow | Workflow | Automatic (default) | Continuous |
| Logs-First Workflow | Workflow | User enables | Continuous |
| Bootstrap Project | Process | User requests | 1-2 hours |
| Document Integrity Scan | Process | User requests or periodic | 1-5 minutes |
| Tool Entry Points | Process | User requests | 10-30 minutes |

## Project Integration

This Agent Kernel can be integrated into any project following these patterns:

### Entry Points

- **[AGENTS.md](../../AGENTS.md)** - Main agent instructions combining Agent Kernel workflows with project-specific requirements
- **[docs/definition-of-done.md](../definition-of-done.md)** - Project-specific DoD extending Agent Kernel universal DoD
- **[docs/workflows.md](../workflows.md)** - Project-specific development workflows

### Project-Specific Extensions

Projects typically add domain-specific requirements for their:

**Project Type:**
- CLI Application, Web Service, Library, etc.
- Domain-specific processing needs
- External API integrations

**Technology Stack:**
- Language and version (Python 3.x, Node 18+, etc.)
- Testing framework (pytest, jest, etc.)
- Libraries and dependencies

See [docs/definition-of-done.md](../definition-of-done.md) for project-specific requirements in your implementation.

### Sync Status

After running bootstrap.py, check:
- **Bootstrap sync:** Last run date
- **Last integration update:** When AGENTS.md was last updated
- **Sections synchronized:** CORE-WORKFLOW, PRINCIPLES, language-specific DoD

### Documentation Structure

```
project-root/
├── AGENTS.md                           # Combined: Agent Kernel + project extensions
├── [TOOL].md                           # Tool-specific instructions (if exists)
├── docs/
│   ├── definition-of-done.md          # Project DoD (extends Agent Kernel)
│   ├── architecture.md                # Project architecture
│   ├── implementation-reference.md    # Implementation patterns
│   ├── workflows.md                   # Project workflows (extends Agent Kernel)
│   ├── examples/                      # Project-specific examples (if exists)
│   └── system-prompts/                # Agent Kernel (this directory)
│       ├── README.md                  # This file
│       ├── principles/                # Universal principles
│       ├── languages/                 # Language-specific standards
│       ├── templates/                 # Document templates
│       ├── workflows/                 # Workflow documentation
│       └── tools/                     # Tool-specific guides
└── dev_notes/                         # Runtime documentation
    ├── specs/                         # Specifications
    ├── project_plans/                 # Project plans
    └── changes/                       # Change documentation
```

## Version

Agent Kernel v1.0 - January 2026

For updates, issues, or contributions, refer to your project's development guidelines.
