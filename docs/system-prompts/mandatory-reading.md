# MANDATORY READING - READ FIRST, EVERY SESSION

**CRITICAL:** Before starting ANY task in this project, you MUST read these files in this exact order.

## Why These Files Are Mandatory

These files define:
- How to approach all tasks (workflow and steps)
- Quality standards (definition of done criteria)
- Project-specific rules and structure
- What actions are prohibited

**Reading these files is NOT optional. Skip them and you WILL make mistakes.**

---

## The Mandatory Reading List

### 1. Core Workflow
**File:** [docs/system-prompts/workflows/logs-first.md](workflows/logs-first.md)

**What it contains:**
- 5-step workflow (Analyze Request → Create Spec → Create Plan → Get Approval → Implement & Document)
- File naming conventions: `YYYY-MM-DD_HH-MM-SS_description.md`
- Status definitions: Draft, Approved, In Progress, Completed, WONT-DO
- The unbreakable rules
- Definition of Done principles
- How to handle uncertainties

**Why mandatory:** Defines the entire workflow for this project. Without this, you won't know how to structure your work.

---

### 2. Definition of Done
**File:** [docs/definition-of-done.md](../definition-of-done.md)

**What it contains:**
- Completion criteria for all tasks
- Verification requirements with proof (actual commands and output)
- Configuration integrity rules
- Quality standards
- Dependencies and configuration management

**Why mandatory:** No task is "Done" until it meets these criteria. You must know them before starting work.

---

### 3. Project-Specific Guidelines
**File:** [docs/mandatory.md](../mandatory.md)

**What it contains:**
- Second Voice project structure and overview
- Key documentation references
- Development guidelines (language, dependencies, code style)
- Prohibited actions specific to this project
- When to stop and ask for help

**Why mandatory:** Contains rules unique to this project. Generic knowledge isn't enough.

---

## Optional Resources (Read As Needed)

These files provide additional context when working on specific features:

- **Architecture:** [docs/architecture.md](../architecture.md) - System design, components, and data flow
- **Implementation Reference:** [docs/implementation-reference.md](../implementation-reference.md) - Code patterns, style, and conventions
- **Workflows:** [docs/workflows.md](../workflows.md) - Development processes and available workflow options
- **Tool Guides:** [docs/system-prompts/tools/](tools/) - Guides for Aider, Claude Code, and other tools

---

## Self-Check: Did You Really Read Them?

After reading the mandatory files, you should be able to answer:

- ✓ What are the 5 steps of the core workflow? (Hint: A, B, C, D, E)
- ✓ What timestamp format do I use for dev_notes files? (Hint: YYYY-MM-DD_HH-MM-SS)
- ✓ What are the possible status values for a Project Plan? (Hint: 5 values)
- ✓ When is a task considered "Done"? (Hint: See Definition of Done checklist)
- ✓ What directories am I NOT allowed to edit? (Hint: docs/system-prompts/)
- ✓ Where do I create temporary files? (Hint: Current directory, pattern tmp-*)
- ✓ What should I do if I'm uncertain about something? (Hint: STOP and ask)

If you can't answer these, **re-read the mandatory files now**. This isn't punishment - it's debugging.

---

**Remember:** Reading is REQUIRED, not suggested. These files are in your context for a reason.
