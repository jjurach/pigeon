# Principle: Agent Jurisdiction & Cross-Project Coordination

**Purpose:** Establish clear boundaries for which code and configuration agents are permitted to modify, and define the escalation protocol for coordinating work across multiple repositories.

---

## The Three Core Rules

### Rule 1: Write-Local Rule

**Agents MUST write ONLY to their own project directory.**

- An agent working on `modules/hatchery` can **only write** to `modules/hatchery/`
- An agent working on `modules/pigeon` can **only write** to `modules/pigeon/`
- Agents in `hentown` (the parent repo) can write to `hentown/` directories only
- **Exception:** A hentown agent with `cross-project | full read/write authority` can write to any directory for coordination purposes

### Rule 2: Reads-Permitted Rule

**Agents MAY read sibling projects for context, but never to determine what they should write.**

- A hatchery agent may read `modules/pigeon/` files to understand dependencies
- A pigeon agent may read `modules/hatchery/` to understand interfaces
- Reads are **informational only** — they inform decisions, but never justify writing outside your jurisdiction
- Example: reading `modules/hatchery/socket.md` to understand the socket protocol is allowed. Modifying `modules/hatchery/socket.md` is **not**.

### Rule 3: Bead Creation Rule

**Agents create beads only in their own project DB or (for cross-project coordination) in hentown.**

- A hatchery agent creates beads in `modules/hatchery/.beads` only
- A pigeon agent creates beads in `modules/pigeon/.beads` only
- A hentown agent creates beads in `hentown/.beads` (and may create hentown beads for escalation)
- **Escalation-only exception:** A worker who discovers blocking work in a sibling project may create a FAILURE bead in `hentown/.beads` (see Failure Escalation Pattern below)
- **Never** create beads in sibling module `.beads/` directories

---

## The Jurisdiction Annotation Format

Every bead description MUST include a `jurisdiction:` line that declares boundaries. This signals to dispatched agents what they may modify.

### For Module Agents (hatchery, pigeon)

```markdown
repo: modules/hatchery
jurisdiction: write-local (modules/hatchery/) | reads permitted (other modules)
```

Or in abbreviated form:
```markdown
repo: modules/hatchery
jurisdiction: write-local | escalate-to: hentown
```

The `escalate-to: hentown` clause means: "If you discover blocking work outside your jurisdiction, create a FAILURE bead in hentown."

### For Cross-Project Coordination (hentown)

```markdown
repo: hentown (cross-project coordination)
jurisdiction: cross-project | full read/write authority
```

Or more specifically:
```markdown
repo: hentown (cross-project principle, P1)
jurisdiction: cross-project | full read/write authority | escalation target for module failures
```

The `escalation target` phrase signals that hentown agents expect FAILURE beads from other modules.

---

## Failure Escalation Pattern (3-Step Protocol)

When a worker discovers that their task is blocked by a defect, missing interface, or other issue **outside their jurisdiction**, the escalation protocol is:

### Step 1: Create a FAILURE Bead in hentown

Create a new bead in the hentown `.beads/` database (not in your module):

```bash
cd <path-to-hentown>
bd create "FAILURE: <module>: <brief description>" \
  --description="<detailed context>" \
  --priority=1 \
  --deps=discovered-from:<original-bead-id>
```

Example:
```bash
bd create "FAILURE: pigeon: SocketClient does not implement required authenticate() method" \
  --description="hatchery-8gh is blocked until pigeon implements SocketClient.authenticate() with token validation. See PR #123 for expected interface." \
  --priority=1 \
  --deps=discovered-from:pigeon-1f2
```

### Step 2: Block the Original Bead on the Failure Bead

Add a note to your original bead (via `bd update`) that documents the blocking FAILURE bead and explains why you're stopping:

```bash
bd update <your-bead-id> --append-notes="blocked-by: hentown-<failure-bead-id>
Escalation: pigeon-1f2 requires hatchery SocketClient.authenticate() implementation. Stopping until FAILURE bead resolved."
```

### Step 3: Stop. Do Not Write to Sibling Projects.

- **Do NOT attempt to fix the blocking issue yourself** in the sibling project (that violates write-local)
- **Do NOT work around it** in your own module (that masks the real problem)
- **Stop cleanly**, document the blocker, and wait for the sibling module's agent to resolve it

---

## Bead Notes: The cross-deps: Convention

In addition to `jurisdiction:`, bead notes may include a `cross-deps:` line that documents dependencies on other module beads. This convention works hand-in-hand with jurisdiction rules.

### Format

```
cross-deps: <bead-id>=<desired-status>[, <bead-id>=<desired-status>, ...]
```

Where `<desired-status>` is one of:
- `closed` — the blocking bead must be closed before this bead can be dispatched
- `open` — the blocking bead is expected to be open (soft dependency); proceed if it's not resolved

Example:
```
cross-deps: pigeon-1f2=closed, hatchery-9gh=closed
```

This means: "Do not dispatch this bead until both pigeon-1f2 and hatchery-9gh are closed."

### Checking Cross-Deps at Dispatch Time

The orchestrator (or human dispatcher) checks `cross-deps:` lines before assigning work:
- If a cross-dep bead is not yet closed, the bead is **not ready** (even if no other blockers exist)
- Ready beads are those with all cross-deps satisfied

### Soft Dependencies and Reads

Cross-deps do **not** permit writing to sibling projects. Even if a bead lists a hatchery bead as a cross-dep, a pigeon agent:
- **May read** hatchery outputs to adapt pigeon's implementation
- **Must not write** to hatchery to make pigeon's job easier
- If hatchery's design is broken, escalate with a FAILURE bead instead

---

## Real-World Example: Pigeon Hits a Hatchery Defect

### Scenario

Pigeon agent (worker on `pigeon-1f2`: Pigeon Slack Handler) discovers that the hatchery SocketClient doesn't have an `authenticate()` method required by the Slack handler interface.

### What NOT to Do

1. ❌ Don't modify `modules/hatchery/socket.py` to add the method
2. ❌ Don't work around it in pigeon by faking authentication
3. ❌ Don't create a bead in `modules/hatchery/.beads/` to fix it

### What TO Do

1. **Create a FAILURE bead in hentown:**
   ```bash
   cd /path/to/hentown
   bd create "FAILURE: hatchery: SocketClient missing authenticate() method" \
     --description="pigeon-1f2 (Pigeon Slack Handler) requires SocketClient.authenticate(token) for hub authentication. Current SocketClient lacks this method. Expected interface: authenticate(token: str) -> bool" \
     --priority=1 \
     --deps=discovered-from:pigeon-1f2
   ```
   This creates (hypothetically) `hentown-xxx`.

2. **Block pigeon-1f2 on the failure bead:**
   ```bash
   cd /path/to/pigeon
   bd update pigeon-1f2 --append-notes="blocked-by: hentown-xxx
   Escalation: hatchery SocketClient must implement authenticate() method before pigeon Slack handler can proceed."
   ```

3. **Stop work on pigeon-1f2.**

4. **A hentown or hatchery agent** will eventually see the FAILURE bead and create a fix bead in hatchery to implement the missing method.

---

## Jurisdiction and the Agent Kernel

When an agent is dispatched to work on a bead, the agent kernel includes the bead's `jurisdiction:` line in the system prompt. This means:

- Every dispatched agent **knows** their boundaries
- The agent's system instructions reinforce the write-local rule
- Agents are expected to honor jurisdiction even if they could technically write elsewhere
- Violation of jurisdiction is a critical error (equivalent to writing to the wrong config file)

---

## Coordination Between Modules

### hentown's Role

`hentown` is the **coordination hub** for cross-module work:
- Hosts principle documents (this one)
- Hosts epic-level beads for cross-module phases (e.g., `hentown-3zz`: Slack Migration Design)
- Hosts FAILURE beads escalated from modules
- Can write to other repos **only** for principle/workflow coordination (e.g., to update system prompts)

### Module Autonomy

Each module (`hatchery`, `pigeon`) is autonomous:
- Independent `.beads/` databases
- Independent implementation choices
- Independent test suites
- Write-local code changes only

### The Cross-Deps Mechanism

`cross-deps:` in bead notes provides the **only** way to express module dependencies:
- A pigeon bead lists which hatchery beads it depends on
- The dispatcher checks these before assigning work
- If a cross-dep is unmet, the bead is marked "not ready" (like a merge blocker)

---

## Summary: The Three Rules + Escalation Pattern

| Rule | Scope | Implementation |
|---|---|---|
| **Write-Local** | Only modify your own module/repo | FAILURE escalation if you discover blocking work elsewhere |
| **Reads-Permitted** | May read sibling projects for context | Information flows in; only decision flows out |
| **Bead Creation** | Create in own DB or hentown only | Never create beads in sibling module `.beads/` |
| **Escalation** | Cross-project blocking discovered? | 3-step: Create FAILURE bead, block original bead, stop |

---

**Last Updated:** 2026-03-04
**Status:** Active ✓
