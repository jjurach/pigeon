# Project Context

This document captures the design rationale and external interface for pigeon. It exists so that an agent working in isolation within this module has the background needed to make consistent decisions without access to broader planning context.

---

## Design Rationale

**What pigeon does.** pigeon is an inbox listener and router. It watches for incoming messages from Slack (and potentially other sources), optionally processes them through an STT/professionalization pipeline, and routes the resulting specs to target projects as bead issues.

**Why a dedicated routing module.** Rather than having the Slack bot live inside hatchery or another module, a dedicated routing module keeps the concern separate: hatchery executes work, pigeon captures and routes new work. This separation means pigeon can be extended to accept input from sources other than Slack without touching hatchery.

**File-based inbox.** Messages from Slack are written to `dev_notes/inbox/` as timestamped markdown files before routing. This decouples the Slack listener from the routing logic, allows manual inspection of queued items, and provides a natural audit trail.

**Project detection via beads.** The routing step determines which project a message belongs to by examining the beads databases of candidate modules. This avoids hardcoding routing rules and allows the routing logic to be aware of current project state.

**Slack Socket Mode & Separate App (pigeon-gjf resolved).** Socket Mode was chosen for the same reason as in hatchery — no public endpoint required. Pigeon uses a **dedicated Slack app** (separate from hatchery) with its own bot and app tokens. This enables independent deployment, testing, and credential isolation. Trade-off: two Slack apps to manage in the workspace, but clear separation of concerns.

**Separate Listener Daemon (pigeon-gjf resolved).** Pigeon Slack listener runs as a **dedicated daemon** (`pigeon-slack-listener`) independent from the hatchery daemon. This separates concerns: hatchery executes work, pigeon routes work. Trade-off: operational overhead of managing separate daemon process, but clean architecture with no cross-module dependencies at runtime.

**Project-Specific Environment Variables (pigeon-gjf resolved).** Slack credentials use `PIGEON_SLACK_*` prefixes (e.g., `PIGEON_SLACK_BOT_TOKEN`, `PIGEON_SLACK_APP_TOKEN`, `PIGEON_SLACK_INBOX_CHANNEL`, `PIGEON_SLACK_AUTHORIZED_USERS`) instead of sharing hatchery's variables. This provides clear ownership and allows each module to evolve independently. Trade-off: more `.env` variables to manage, but matches hatchery's pattern.

**Socket Mode Only (pigeon-gjf resolved).** Pigeon uses SocketModeClient for real-time message processing (not Events API webhooks). This matches hatchery's approach and aligns with Slack recommendations. Acceptable latency for routing messages to beads. Trade-off: network-dependent, requires robust reconnection logic.

**Phased Code Sharing (pigeon-gjf resolved).** Code sharing with hatchery and mellona will be phased:
  1. **Phase 1 (Current):** Pigeon implements separate `SlackSource` and listener daemon (learn patterns first)
  2. **Phase 2 (Future):** After pigeon and mellona are both implemented, extract shared `hentown-slack-core` library
  3. Trade-off: temporary duplication, but avoids premature abstraction. Allows each module to solve its own problems first.

**STT pipeline dependency.** Voice messages from Slack require transcription before routing. pigeon calls the STT pipeline (currently second_voice) to convert audio to text. This is an optional processing step — text messages bypass STT.

---

## Phase Roadmap

| Phase | Description | Status |
|---|---|---|
| RESEARCH | Clarify Slack Integration Questions | ✓ closed (5 questions answered, architecture decisions made) |
| Slack Listener | Slack #hentown-inbox listener daemon | open (ready to implement) |
| Router | Route inbox items to pipeline | open (blocked by Slack Listener) |

---

## External Dependencies

**second_voice (STT pipeline)** — for processing voice messages from Slack. pigeon invokes second_voice as a subprocess for audio-to-text conversion. If second_voice is not available, pigeon falls back to skipping STT (text-only routing).

**Beads databases in target modules** — pigeon creates bead issues in target projects. Target modules must have `.beads/` initialized.

**Slack app credentials** — Pigeon uses a dedicated Slack app (separate from hatchery) with its own Socket Mode bot token (`PIGEON_SLACK_BOT_TOKEN`) and app-level token (`PIGEON_SLACK_APP_TOKEN`). Stored via environment variables or mellona keyring. This isolation enables independent deployment and testing.

---

## What This Module Exports

pigeon is a daemon/service, not a library.

**Runtime behavior:**
- Listens on Slack #hentown-inbox channel for messages from authorized users
- Writes received messages to `dev_notes/inbox/<timestamp>_<user>.md`
- Optionally runs STT on audio messages
- Creates bead issues in the appropriate target module's `.beads/`

**No importable Python API.** Other modules do not import pigeon.
