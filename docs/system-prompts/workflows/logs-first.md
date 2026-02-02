# Logs-First Workflow

**Purpose:** Comprehensive workflow for small, iterative projects where detailed documentation and audit trails are valuable.

**Best for:**
- Small teams (1-10 developers)
- Active projects with frequent iterations
- Projects valuing accountability and decision history
- Internal/experimental projects

**Not recommended for:** Large enterprises with different documentation needs

---

## What is the Logs-First Workflow?

The logs-first workflow emphasizes documentation-as-you-go: every implementation is tracked through three connected documents (Spec → Plan → Changes), creating a complete audit trail of intentions, design decisions, and actual implementation.

This enables agents to:
- Understand what the user wanted
- Learn the approved implementation strategy
- See what was actually built and prove it works
- Maintain project continuity across team changes

---

## File Naming Conventions

**CRITICAL:** All timestamped files in `dev_notes/` use this exact format:

```
YYYY-MM-DD_HH-MM-SS_description.md
```

**Examples from this project:**
- `dev_notes/specs/2026-01-27_07-28-35_inbox-based-spec-generation.md`
- `dev_notes/project_plans/2026-01-25_18-46-25_add-tests-fix-pytest.md`
- `dev_notes/changes/2026-01-26_23-15-42_aac-support-implementation.md`

**How to generate the timestamp:**

```bash
date +%Y-%m-%d_%H-%M-%S
```

**IMPORTANT - Always check existing files first:**

Before creating any file in `dev_notes/specs/`, `dev_notes/project_plans/`, or `dev_notes/changes/`, you MUST:

1. **List existing files** in the target directory (e.g., `ls dev_notes/specs/`)
2. **Observe the naming pattern** used in existing files
3. **Match that exact pattern** for your new file

This ensures consistency and makes it obvious when the format is wrong.

**Common Mistakes to Avoid:**
- ❌ `20260128_103440` (no hyphens, wrong separators)
- ❌ `2026-01-28-10-34-40` (all hyphens, should be underscore between date and time)
- ❌ `2026_01_28_10_34_40` (all underscores, should use hyphens within date and time)
- ✅ `2026-01-28_10-34-40` (correct format)

---

## The Core Workflow

**MANDATORY:** For any request that involves creating or modifying code or infrastructure, you MUST follow this workflow.

### Step A: Analyze the Request & Declare Intent

1. **Is it a simple question?** → Answer it directly. No documentation required.
2. **Is it a Trivial Change?** → Make the change directly. No documentation required.
   - *Trivial Change Definition:* Non-functional changes like fixing typos in comments or code formatting.
3. **Is it just to fix tests or to fix broken usage?** → Make the change directly. No documentation required.
4. **Is it a Research/Documentation Change?** → Make the change directly. No project plan required, but for non-trivial documentation work, create a timestamped change log in `dev_notes/changes/` marked with `Status: ad-hoc`.
   - *Research/Documentation Change:* Requests which culminate ONLY into writes to markdown documents in the root folder or in `docs/` or in `dev_notes`.
   - *Non-Trivial Documentation:* Creating new documentation files, substantial rewrites, or establishing new patterns/conventions. These skip project plans but still require change documentation for the audit trail.
5. **Is it anything else?** → Announce you will create a **Spec File** and **Project Plan**.

### Step B: Process Spec File (If Required)

When a prompt involves planning, represent it in `dev_notes/specs`:

- **Check existing files first:** Run `ls dev_notes/specs/` to see the naming pattern
- Create a summary of what the user is asking for using the timestamp format (see "File Naming Conventions" above)
- **Example filename:** `dev_notes/specs/2026-01-28_14-22-15_add-authentication.md`
- If updating an existing un-timestamped spec file, rename it with the correct filename format based on the file's last modified time
- Add any additional context as developed over follow-up conversations

**Spec files signify user intentions and goals.** They are typically used to create or update project plans.

**Processing inbox items:** When the user asks you to process an item from `dev_notes/inbox/`, follow this pattern:
1. Read the inbox file to understand requirements
2. Create a timestamped spec file in `dev_notes/specs/` with the content reorganized
3. **Archive the inbox file:** Move it to `dev_notes/inbox-archive/` with a timestamp prefix (e.g., `dev_notes/inbox-archive/2026-01-28_14-22-15-original-name.md`)
4. This "archiving" moves the inbox file out of the way while preserving it with a timestamp

### Step C: Create a Project Plan (If Required)

- **Check existing files first:** Run `ls dev_notes/project_plans/` to see the naming pattern
- Use the **Project Plan Structure** defined in `docs/templates.md`
- The plan must be detailed enough for another agent to execute
- **Example filename:** `dev_notes/project_plans/2026-01-28_14-25-30_add-authentication.md`
- Save using the exact timestamp format (see "File Naming Conventions" above)

### Step D: AWAIT DEVELOPER APPROVAL

**NEVER EXECUTE A PLAN WITHOUT EXPLICIT APPROVAL.**

- Present the full Project Plan to the developer
- "Approved", "proceed", "go ahead", "ok", or "yes" mean you can start
- If the developer asks questions or provides feedback, answer them and then **return to a waiting state** until receiving new, explicit approval
- **If approval is ambiguous** (e.g., "maybe", "I think so", "probably"): Ask a follow-up clarifying question such as "I want to confirm: should I proceed with this Project Plan? Please respond with 'yes' or 'no'."

### Step E: Implement & Document Concurrently

- Execute the approved plan step-by-step
- After each logical change, create or update a **Change Documentation** entry in `dev_notes/changes/`
- Use the structure from `docs/templates.md`

---

## The Unbreakable Rules

1. **Approval is Mandatory:** This is the most important rule. Never act on a Project Plan without explicit developer approval.

2. **Quality is Mandatory:** You MUST follow the existing code patterns, conventions, style, and typing of the files you are editing. New code should look like the old code.

3. **Uncertainty Requires a Full Stop:** If you encounter any error, are confused by a requirement, or are unsure how to proceed, you MUST **STOP** immediately. Document the issue and ask the developer for guidance. Do not try to solve novel problems alone.

4. **File Naming is Mandatory:**
   - All Project Plans, Specs, and Change Documentation in `dev_notes/` MUST use the timestamp format defined in "File Naming Conventions" section above
   - **Always check existing files first** to observe the pattern before creating new files
   - All new documentation files in `docs/` MUST use `lowercase-kebab.md` naming convention

5. **Temporary Files:** NEVER use `/tmp` or system temporary directories for temporary files. Always create temporary files in the current working directory using the naming patterns `tmp-*` or `*.tmp` or `tmp/*`. These files should be cleaned up when no longer needed.

---

## The "Plan vs. Reality" Protocol

### Plan Consistency

- **Insignificant Deviation:** If the implementation differs slightly from the plan (e.g., helper function name change, minor logic simplification) but the *outcome* is identical, note this in the `dev_notes/changes/` entry
- **Significant Deviation:** If you discover a significantly better architectural approach or a blocker that requires changing other components: **STOP**. Abort the current execution path and ask the human developer for intervention. Do not unilaterally rewrite the architecture.

### Plan Status

All Project Plans in `dev_notes/project_plans/` must have a `Status` header:
- **Draft:** Initial state when creating the plan
- **Approved:** State after human developer gives explicit approval
- **In Progress:** Plan is being actively implemented
- **Completed:** You MUST update the header to `Status: Completed` before declaring the task finished
- **WONT-DO:** Plan is cancelled or indefinitely postponed (include reason in header)

---

## Definition of Done: Universal Principles

**MANDATORY:** No task is considered "Done" until all applicable criteria are met.

### Verification as Data

- **Proof of Work:**
  - In the `dev_notes/changes/` entry, the "Verification Results" section is **mandatory**
  - You MUST include the **exact command** used to verify the change
  - You MUST include a **snippet of the terminal output** (stdout/stderr) showing success
  - "It works" is not acceptable. Proof is required.

- **Temporary Tests:**
  - If you created a temporary test script (e.g., `scripts/verify_bug_123.py`):
    1. Run it and capture the output
    2. Include the **full content of the script** in the `dev_notes/changes/` entry (inside a code block)
    3. **Delete** the temporary script from the repository

### Codebase State Integrity

- **Dependencies:**
  - If any new library is imported, the task is **NOT DONE** until both `requirements.txt` AND `pyproject.toml` are updated

- **Configuration Drift:**
  - If you add or modify a configuration key (e.g., `openrouter_llm_model`):
    1. Update `docs/implementation-reference.md` (or relevant doc)
    2. Update `config.example.json` to include the new key with a safe default or placeholder
  - **Secrets:** Never hardcode secrets. Ensure they are read from env vars or config, and documented in `config.example.json`

### The Agent Handoff

- **Known Issues:**
  - If the implementation is functional but has caveats (e.g., "slow on first run," "edge case X not handled"), you MUST add a **"Known Issues"** section to the `dev_notes/changes/` entry

- **Context Forwarding:**
  - When starting a new task, agents are instructed to read the previous 2 change summaries to check for "Known Issues" that might impact their work

### Checklist for "Done"

- [ ] `Status: Completed` set in Project Plan
- [ ] `dev_notes/changes/` entry created
- [ ] Verification command and output included in change log
- [ ] Temporary test scripts content saved to log and file deleted
- [ ] `requirements.txt` & `pyproject.toml` updated (if applicable)
- [ ] `config.example.json` updated (if applicable)
- [ ] `docs/` updated for new config/features
- [ ] "Known Issues" documented

---

## Documentation & Resources

- **`docs/definition-of-done.md`**: Details for marking tasks complete
- **`docs/templates.md`**: Full templates for Spec Files, Project Plans, and Change Documentation
- **`docs/file-naming-conventions.md`**: Naming conventions for new documentation
- **`docs/architecture.md`**: High-level system design
- **`docs/implementation-reference.md`**: Patterns for adding features
- **`config.example.json`**: Source of truth for configuration keys

---

## How Projects Set Up Logs-First Workflow

### Initial Setup

Run bootstrap.py with workflow detection:

```bash
cd /path/to/your/project
python3 docs/system-prompts/bootstrap.py --analyze-workflow
```

This will:
1. Auto-detect your project characteristics (size, git history, structure)
2. Recommend a workflow
3. Show you the recommendation without making changes

To enable logs-first workflow:

```bash
python3 docs/system-prompts/bootstrap.py --enable-logs-first --commit
```

### Subsequent Runs

Once enabled, logs-first workflow will be injected into AGENTS.md automatically. To maintain state:

```bash
# Check current state (dry run)
python3 docs/system-prompts/bootstrap.py --analyze-workflow

# Disable if needed
python3 docs/system-prompts/bootstrap.py --disable-logs-first --commit
```

---

## Directory Structure

Projects using logs-first workflow should create and maintain:

```
project-root/
├── dev_notes/
│   ├── specs/               # User intentions and requirements
│   │   └── YYYY-MM-DD_HH-MM-SS_spec-name.md
│   ├── project_plans/       # Implementation strategies (awaiting approval)
│   │   └── YYYY-MM-DD_HH-MM-SS_plan-name.md
│   └── changes/             # Proof of implementation
│       └── YYYY-MM-DD_HH-MM-SS_change-name.md
├── docs/
│   ├── templates.md         # Document templates
│   ├── definition-of-done.md
│   └── system-prompts/
│       └── workflows/
│           └── logs-first.md (this file)
└── AGENTS.md                # Agent instructions (includes workflow)
```

---

## Example Workflow: Adding a New Feature

### Step A: Analyze Request

User says: "Add a caching layer to reduce API calls"

Analysis: This is not trivial, not a test fix, not just documentation → Create Spec + Plan

### Step B: Create Spec File

`dev_notes/specs/2026-01-26_12-30-45_add-caching-layer.md`

Document:
- What caching is needed
- Why it's needed
- What success looks like

### Step C: Create Project Plan

`dev_notes/project_plans/2026-01-26_12-35-20_add-caching-layer.md`

Document:
- How you'll implement caching
- Which modules change
- What tests are needed
- Risk assessment

### Step D: Get Approval

Present plan to developer. Wait for "yes" or "approved".

### Step E: Implement & Document

1. Make changes to codebase
2. After each major change, create entry in `dev_notes/changes/`
3. Include verification (test output, coverage, etc.)
4. Mark Plan as "Completed" when all steps done

---

## Notes for Using Logs-First Workflow

- **Specs are lightweight** - 1-2 pages is typical
- **Plans should be detailed** - Detailed enough for another agent to execute
- **Change documentation proves work** - Include actual test output and metrics
- **State matters** - Always check Definition of Done before declaring "done"
- **Ask when uncertain** - Better to ask than to guess

---

## Further Reading

- `docs/templates.md` - Detailed templates with examples
- `docs/definition-of-done.md` - Full Definition of Done checklist
- `docs/architecture.md` - How Agent Kernel and workflows integrate
