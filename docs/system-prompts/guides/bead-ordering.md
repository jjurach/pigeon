# Bead Ordering Policy

**Purpose:** Define the canonical priority ordering of ready beads across a
root project and its git submodule projects, so that agents and orchestrators
always pick the highest-value work first.

---

## Quick Reference

```bash
# Find the next bead to work on (cross-project, priority-ordered):
python3 docs/system-prompts/planning-summary.py --next-bead
```

---

## When This Policy Applies

This multi-project ordering policy applies **only when the caller's working
directory is the root of a git project that contains submodules** (i.e., a
`.gitmodules` file exists and submodule directories are initialized).

If the caller is inside a submodule project with no further submodules of its
own, **only single-project ordering applies** — do not consider any bead
databases outside the current project.

---

## Ordering Rules

Ready beads are ordered by the following sort key (all ascending, meaning
lower values win):

| Key | Value | Meaning |
|-----|-------|---------|
| 1 | `priority` | P0 (0) is most urgent; P4 (4) is backlog |
| 2 | `project_tier` | 0 = root project, 1 = submodule |
| 3 | `project_path` | Lexicographic path of the submodule |
| 4 | `bead_id` | Lexicographic bead ID |

### Priority (Key 1)

Lower priority number = higher urgency:

- **P0** — Critical / blocking everything
- **P1** — High priority
- **P2** — Medium (default)
- **P3** — Low
- **P4** — Backlog

A P1 bead always beats a P2 bead, regardless of which project it belongs to.

### Project Tier (Key 2)

At equal priority, the **root project** beats any submodule. This reflects the
convention that top-level coordination work takes precedence over
module-specific work when urgency is otherwise equal.

**Example:** A P2 bead in the root project wins over a P2 bead in
`modules/chatterbox`.

### Submodule Path (Key 3)

Among submodules at equal priority, the submodule whose path sorts first
lexicographically wins.

**Example:** A P2 bead in `modules/chatterbox` wins over a P2 bead in
`modules/second_voice` because `"chatterbox" < "second_voice"`.

### Bead ID (Key 4)

Within the same project and priority, bead IDs are compared lexicographically.
`bead-abc` wins over `bead-def`.

---

## Worked Examples

| Scenario | Winner |
|----------|--------|
| P1 in `modules/chatterbox` vs P2 in root | P1 chatterbox (priority dominates) |
| P1 in root vs P1 in `modules/chatterbox` | P1 root (same priority, root tier wins) |
| P2 in `modules/chatterbox` vs P2 in `modules/second_voice` | P2 chatterbox (same priority/tier, lex path) |
| P2 `bead-abc` in root vs P2 `bead-def` in root | P2 `bead-abc` (same everything, lex ID) |

---

## Implementation

### For Agents (CLI)

Run from the root project directory:

```bash
python3 docs/system-prompts/planning-summary.py --next-bead
```

Output example:

```
Next ready bead (cross-project priority order):

  [P1] chatterbox-xyz
  Project: modules/chatterbox  [modules/chatterbox]
  Title:   Implement retry logic for provider dispatch
  Claim:   cd modules/chatterbox && bd update chatterbox-xyz --status=in_progress

────────────────────────────────────────────────────────────
All ready beads (3):
   1. [P1] chatterbox-xyz     modules/chatterbox           "Implement retry logic for provi…"
   2. [P2] hentown-abc        .                            "Update workflow documentation"
   3. [P3] hatchery-def       modules/hatchery             "Add config validation"
```

### For Orchestrators (Programmatic)

The `find_next_bead()` function in `planning-summary.py` returns a sorted list
of candidate dicts. The first entry is the highest-priority bead:

```python
from docs.system_prompts.planning_summary import process_all_projects, find_next_bead

projects = process_all_projects(".")
ranked = find_next_bead(projects)
if ranked:
    top = ranked[0]
    # top['bead']         — bead dict
    # top['project_path'] — e.g. "modules/chatterbox" or "."
    # top['project_name'] — e.g. "chatterbox"
    # top['project_tier'] — 0 (root) or 1 (submodule)
```

---

## Single-Project Mode

When running **within a submodule** (no further nested submodules), ignore this
multi-project policy entirely. Use:

```bash
bd ready --sort priority
```

This returns ready beads for the current project sorted by priority then
creation date (the beads tool's built-in ordering).

---

## Reference

- Implementation: `docs/system-prompts/planning-summary.py` → `find_next_bead()`
- CLI command: `planning-summary.py --next-bead`
- Used in: `docs/system-prompts/processes/iterate-next-bead.md` Phase 3
