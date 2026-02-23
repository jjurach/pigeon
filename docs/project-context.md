# Project Context

This document captures the design rationale and external interface for pigeon. It exists so that an agent working in isolation within this module has the background needed to make consistent decisions without access to broader planning context.

---

## Design Rationale

**What pigeon does.** pigeon is an inbox listener and router. It watches for incoming messages from Slack (and potentially other sources), optionally processes them through an STT/professionalization pipeline, and routes the resulting specs to target projects as bead issues.

**Why a dedicated routing module.** Rather than having the Slack bot live inside hatchery or another module, a dedicated routing module keeps the concern separate: hatchery executes work, pigeon captures and routes new work. This separation means pigeon can be extended to accept input from sources other than Slack without touching hatchery.

**File-based inbox.** Messages from Slack are written to `dev_notes/inbox/` as timestamped markdown files before routing. This decouples the Slack listener from the routing logic, allows manual inspection of queued items, and provides a natural audit trail.

**Project detection via beads.** The routing step determines which project a message belongs to by examining the beads databases of candidate modules. This avoids hardcoding routing rules and allows the routing logic to be aware of current project state.

**Slack Socket Mode (same as hatchery).** Socket Mode was chosen for the same reason as in hatchery — no public endpoint required. The RESEARCH phase (pigeon-gjf) is clarifying the exact Slack app configuration and whether pigeon shares a Slack app with hatchery or uses a separate one.

**STT pipeline dependency.** Voice messages from Slack require transcription before routing. pigeon calls the STT pipeline (currently second_voice) to convert audio to text. This is an optional processing step — text messages bypass STT.

---

## Phase Roadmap

| Phase | Description | Status |
|---|---|---|
| RESEARCH | Clarify Slack Integration Questions | open (in_progress: partial research complete) |
| Slack Listener | Slack #hentown-inbox listener | open (blocked by RESEARCH) |
| Router | Route inbox items to pipeline | open (blocked by Slack Listener) |

---

## External Dependencies

**second_voice (STT pipeline)** — for processing voice messages from Slack. pigeon invokes second_voice as a subprocess for audio-to-text conversion. If second_voice is not available, pigeon falls back to skipping STT (text-only routing).

**Beads databases in target modules** — pigeon creates bead issues in target projects. Target modules must have `.beads/` initialized.

**Slack app credentials** — Socket Mode bot token and app-level token. Stored via environment variables or mellona keyring. The RESEARCH phase is clarifying whether pigeon uses a dedicated Slack app or shares one with hatchery.

---

## What This Module Exports

pigeon is a daemon/service, not a library.

**Runtime behavior:**
- Listens on Slack #hentown-inbox channel for messages from authorized users
- Writes received messages to `dev_notes/inbox/<timestamp>_<user>.md`
- Optionally runs STT on audio messages
- Creates bead issues in the appropriate target module's `.beads/`

**No importable Python API.** Other modules do not import pigeon.
