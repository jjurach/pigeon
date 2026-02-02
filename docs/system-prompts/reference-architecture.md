# Reference Architecture & Dependency Graph

This document maps the reference patterns between all agent instruction files and documentation.

---

## Safety Guardrails for Logs-First Workflow

### Guardrail 1: Section-Based Activation

The logs-first workflow **only activates** when the `<!-- SECTION: LOGS-FIRST-WORKFLOW -->` section is present in AGENTS.md.

**When Disabled:**
- LOGS-FIRST-WORKFLOW section is removed from AGENTS.md
- Agents will NOT see the full workflow instructions
- Agents will NOT trigger plan/approval gates based on `@logs-first` marker
- Tasks with `@logs-first` marker are treated as normal tasks
- Result: No complexity surprises for unaware developers

**When Enabled:**
- LOGS-FIRST-WORKFLOW section is injected into AGENTS.md
- Agents see the mandatory workflow instructions
- Agents recognize `@logs-first` marker as a signal to follow the workflow
- Agents request Project Plans and approval gates
- Result: Full structured workflow engaged

### Guardrail 2: Explicit Marker Recognition

Agents should only respond to `@logs-first` marker if:
1. The LOGS-FIRST-WORKFLOW section is present in AGENTS.md (proof workflow is enabled), AND
2. The section explicitly documents that markers should trigger the workflow

Without both conditions, the marker is inert.

### Guardrail 3: Core Workflow Independence

The core workflow (Steps A-E, Unbreakable Rules) is **always present** and **never conditional**. This ensures:
- Basic structure is never compromised
- Agents always have guidance
- Logs-first is purely additive/optional
- Disabling logs-first doesn't break core functionality

---

## Reference Graph: File Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    PROJECT ROOT                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLAUDE.md ──────┐                                          │
│                  │                                          │
│  GEMINI.md ──────┼──→ AGENTS.md                             │
│                  │       │                                  │
│  README.md ──────┘       │                                  │
│                          │                                  │
│                          ├──→ docs/definition-of-done.md    │
│                          │                                  │
│                          ├──→ docs/templates.md             │
│                          │                                  │
│                          ├──→ docs/workflows.md             │
│                          │                                  │
│                          └──→ docs/architecture.md          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
                    ┌─────────┴──────────┐
                    │                    │
            docs/system-prompts/    [other docs/]
```

---

## Detailed Reference Matrix

### Entry Points for AI Agents

| File | Purpose | References |
|------|---------|-----------|
| **`CLAUDE.md`** | Claude-specific instructions | → `AGENTS.md` |
| **`GEMINI.md`** | Gemini-specific instructions | → `AGENTS.md`<br>→ `docs/definition-of-done.md` |
| **`AGENTS.md`** | Core agent instructions (MANDATORY for all agents) | ↔ `CLAUDE.md`, `GEMINI.md`<br>→ `docs/definition-of-done.md`<br>→ `docs/templates.md`<br>→ `docs/workflows.md`<br>→ `docs/architecture.md`<br>→ `docs/system-prompts/workflows/logs-first.md` (conditional) |

### Core Documentation Files

| File | Purpose | References |
|------|---------|-----------|
| **`docs/definition-of-done.md`** | Quality standards for task completion | Referenced by `AGENTS.md`, `GEMINI.md`<br>→ `docs/templates.md`<br>→ `docs/implementation-reference.md` (if present) |
| **`docs/templates.md`** | Templates for specs, plans, changes | Referenced by `AGENTS.md`<br>Referenced by `docs/definition-of-done.md` |
| **`docs/workflows.md`** | User guide for workflow selection | Referenced by `AGENTS.md`<br>→ `docs/system-prompts/workflows/logs-first.md`<br>→ `docs/system-prompts/workflows/README.md` |
| **`docs/architecture.md`** | System architecture and design | Referenced by `AGENTS.md`<br>→ `docs/system-prompts/workflows/` (explains workflow layer) |

### System Prompts Directory (Reusable, Language-Agnostic)

| File | Purpose | References | Conditional? |
|------|---------|-----------|-------------|
| **`bootstrap.py`** | Injection tool for `AGENTS.md` | Reads from: `workflows/`, `languages/`, `principles/`, `workflow/core.md` | N/A |
| **`README.md`** | System prompts overview | → `workflows/README.md`<br>→ `workflows/logs-first.md`<br>→ `custom-template.md` | No |
| **`workflows/logs-first.md`** | Complete logs-first workflow | → `docs/templates.md` (references)<br>→ `docs/definition-of-done.md` (references)<br>→ `docs/architecture.md` (references) | ✓ YES - Only referenced when section enabled in `AGENTS.md` |
| **`workflows/custom-template.md`** | Template for custom workflows | References `bootstrap.py` integration | ✓ YES - Conditional reference |
| **`workflows/README.md`** | Workflows directory guide | → `logs-first.md`<br>→ `custom-template.md` | ✓ YES - Only if workflows enabled |
| **`workflow/core.md`** | Core A-E workflow steps | → Always injected into `AGENTS.md` | No |
| **`principles/definition-of-done.md`** | Universal DoD criteria | → Always injected into `AGENTS.md` | No |
| **`languages/python/definition-of-done.md`** | Python-specific DoD | → Conditionally injected (if Python project) | ✓ YES |

---

## Conditional References: "If Present" Pattern

For system-prompts files that reference resources outside system-prompts, use this pattern:

### Example: workflows/logs-first.md references docs/templates.md

```markdown
## Documentation

- `docs/templates.md` - Detailed templates with examples
  *(If this file exists in your project)*

- `docs/definition-of-done.md` - Full Definition of Done checklist
  *(If this file exists in your project)*
```

### Why This Pattern?

The `docs/system-prompts/` directory is designed to be **reusable across projects**. Not all projects have:
- `docs/templates.md`
- `docs/workflows.md`
- `docs/architecture.md`

By marking references as "if present," we allow system-prompts to be portable while still providing context when files exist.

---

## Logs-First Workflow Connectivity

### When Disabled

```
AGENTS.md (basic workflow only)
  │
  ├─→ docs/definition-of-done.md
  ├─→ docs/templates.md
  └─→ [other core docs]

[LOGS-FIRST-WORKFLOW section REMOVED]
[workflows/logs-first.md NOT referenced]
[No plan/approval gates triggered by @logs-first marker]
```

**Risk Assessment:** ✅ LOW - Agents won't discover or engage logs-first workflow. No surprises.

### When Enabled

```
AGENTS.md (includes logs-first)
  │
  ├─→ docs/definition-of-done.md
  ├─→ docs/templates.md
  ├─→ docs/workflows.md
  ├─→ docs/architecture.md
  │
  └─→ [LOGS-FIRST-WORKFLOW SECTION]
       │
       ├─→ docs/templates.md (again, explicit reference)
       ├─→ docs/definition-of-done.md (again, for verification)
       └─→ docs/architecture.md (for workflow layer explanation)
```

**Benefit:** ✅ WELL-CONNECTED - All relevant docs are reachable. Agents have complete context.

---

## Required Files in docs/system-prompts/

These files **must** exist for bootstrap.py to function:

- ✓ `workflow/core.md` - Core workflow (Steps A-E)
- ✓ `principles/definition-of-done.md` - Universal DoD
- ✓ `workflows/logs-first.md` - Logs-first workflow
- ✓ `languages/python/definition-of-done.md` - Python DoD

These files are **optional** (used only in specific cases):

- ◯ `languages/javascript/definition-of-done.md` - Only if project is JavaScript
- ◯ `workflows/custom-template.md` - Only if creating custom workflows

---

## Bootstrap State Tracking

The workflow state is stored in AGENTS.md itself:

```html
<!-- BOOTSTRAP-STATE: logs_first=enabled -->
```

**How it works:**

1. **On first run:** bootstrap.py auto-detects project and recommends workflow
2. **User action:** `python3 bootstrap.py --enable-logs-first --commit`
3. **State storage:** State marker added to AGENTS.md
4. **On future runs:** bootstrap.py reads the marker and remembers the choice
5. **No surprise:** State is explicit and visible in AGENTS.md

---

## Guidelines for Adding New Documentation

### If adding to docs/

1. Reference from AGENTS.md if relevant to all agents
2. Reference from CLAUDE.md or GEMINI.md if agent-specific
3. If new file documents a workflow section, make sure it's linked in that section

### If adding to docs/system-prompts/

1. Update `README.md` to list the new file
2. For references outside system-prompts: Use "if present" pattern
3. Update `bootstrap.py` if it's injectable into AGENTS.md
4. For workflows: Follow the pattern in `workflows/README.md`

---

## Verification Checklist

- [ ] **Core sections present:** CORE-WORKFLOW, PRINCIPLES always in AGENTS.md
- [ ] **Logs-first conditional:** Only present when bootstrap state says enabled
- [ ] **No circular hard-dependencies:** (circular *references* are OK)
- [ ] **All referenced files exist:** Check for broken links
- [ ] **Conditional references marked:** "if present" pattern used in system-prompts
- [ ] **Bootstrap state consistent:** `<!-- BOOTSTRAP-STATE: logs_first=enabled|disabled -->`
- [ ] **Agent entry points clear:** CLAUDE.md, GEMINI.md → AGENTS.md
- [ ] **Core workflow independent:** Works with or without logs-first

---

## ASCII Dependency Graph (Simple Version)

```
                        ┌──────────┐
                        │ CLAUDE.md│
                        └────┬─────┘
                             │
                             │
        ┌────────────┐       │       ┌──────────┐
        │  README.md │───────┼──────→│AGENTS.md │←──────┐
        └────────────┘       │       └────┬─────┘       │
                             │            │             │
                        ┌────┴──────┐    │             │
                        │ GEMINI.md │    │    ┌────────┴──────────┐
                        └───────────┘    │    │                   │
                                         │    ▼                   ▼
                                         └──→ docs/           docs/system-prompts/
                                              │                │
                                    ┌─────────┼────────┐      └─→ workflows/
                                    ▼         ▼        ▼              │
                            definition-  templates.md  workflows.md   ├─→ logs-first.md
                            of-done.md                  (references)   │   (conditional)
                                                        architecture.  ├─→ custom-
                                                        md            │    template.md
                                                                      └─→ README.md
```

---

## Summary

**Guardrails Preventing Accidental Logs-First Engagement:**

1. ✅ **Section-based**: Only active when section present in AGENTS.md
2. ✅ **Conditional reference**: workflows/logs-first.md marked as conditional
3. ✅ **Core independent**: Core workflow never depends on logs-first
4. ✅ **Explicit marker**: @logs-first only triggers if section enabled
5. ✅ **State tracking**: Decision explicitly recorded in AGENTS.md

**Graph Characteristics:**

- ✅ Entry points clear: CLAUDE.md, GEMINI.md → AGENTS.md
- ✅ References documented: Both always-present and conditional
- ✅ Circular references: OK (e.g., AGENTS.md → workflows → AGENTS.md when enabled)
- ✅ Disabled case: logs-first completely disconnected
- ✅ Enabled case: logs-first well-integrated with clear documentation links
