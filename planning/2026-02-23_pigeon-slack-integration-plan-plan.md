# Project Plan: Pigeon Slack Integration - Complete Implementation Roadmap

**Created:** 2026-02-23
**Status:** Planning (Clarifying Questions Complete)
**Module:** `modules/pigeon`
**Epic:** Slack #hentown-inbox Listener and Router
**Depends On:** None (hentown/hatchery Slack integration reference available)

---

## Overview

Implement Slack integration for pigeon, enabling the module to listen to #hentown-inbox channel, receive messages from authorized users, process them through an STT pipeline (for voice), and route them as bead issues to target projects.

This implementation is guided by 5 clarifying questions answered in pigeon-gjf (2026-02-23).

---

## Architecture Decisions (From Clarifying Questions)

### Decision 1: Slack App Architecture
**Answer: Separate Slack Apps**
- Pigeon uses dedicated `PIGEON_SLACK_BOT_TOKEN` and `PIGEON_SLACK_APP_TOKEN`
- Independent credentials from hatchery's Slack app
- Enables independent deployment and testing
- Clear separation of concerns: hatchery executes, pigeon routes

### Decision 2: Socket Mode Connection
**Answer: Separate Listener Daemon**
- Create dedicated `pigeon-slack-listener` daemon process
- Runs independently from pigeon router
- Listens to Slack via Socket Mode in real-time
- Writes messages to shared `dev_notes/inbox/` directory

### Decision 3: Configuration Management
**Answer: Project-Specific Env Vars**
- Use `PIGEON_SLACK_*` prefix (matches hatchery's `HATCHERY_SLACK_*`)
- Env vars: `PIGEON_SLACK_BOT_TOKEN`, `PIGEON_SLACK_APP_TOKEN`, `PIGEON_SLACK_INBOX_CHANNEL`, `PIGEON_SLACK_AUTHORIZED_USERS`
- Clear ownership, independent evolution

### Decision 4: Message Reliability
**Answer: Socket Mode Only (Real-Time)**
- Use `SocketModeClient` for real-time message processing
- No polling fallback (unlike SlackSource base which has polling infrastructure)
- Matches hatchery approach, aligns with Slack recommendations
- Acceptable latency for routing messages to beads

### Decision 5: Code Sharing Strategy
**Answer: Phased Approach (Start Separate, Extract Later)**
- Implement SlackListenerDaemon and routing logic separately
- After pigeon + mellona both working, extract shared `hentown-slack-core` library
- Avoids premature abstraction, learn patterns first
- Future refactoring burden acceptable for flexibility now

---

## Implementation Phases

### Phase 1: Environment Configuration & Setup
**Beads:** pigeon-cfg, pigeon-env
**Duration:** 30 minutes

Update `.env.example` and `pigeon/config.py`:
```
# .env.example additions
PIGEON_SLACK_BOT_TOKEN=xoxb-your-token-here
PIGEON_SLACK_APP_TOKEN=xapp-your-token-here
PIGEON_SLACK_INBOX_CHANNEL=hentown-inbox
PIGEON_SLACK_AUTHORIZED_USERS=U0123456789,U9876543210

# pigeon/config.py additions
@dataclass
class SlackConfig:
    bot_token: str
    app_token: str
    inbox_channel: str
    authorized_user_ids: Set[str]
```

### Phase 2: SlackListenerDaemon Implementation
**Beads:** pigeon-nxo (main), pigeon-daemon-auth, pigeon-daemon-socket
**Duration:** 2-3 hours

Create `pigeon/daemon.py` with SlackListenerDaemon:
- Socket Mode connection management
- Message event handling
- User authorization filtering
- Markdown conversion
- Reconnection logic with exponential backoff
- Error handling and logging

**Key Features:**
- Accept messages from #hentown-inbox
- Convert to markdown: `dev_notes/inbox/{timestamp}_{user}.md`
- Include metadata: user, slack_user_id, channel, thread_ts, message content
- Handle attachments: images stored with references, audio passed to STT pipeline
- Resilient reconnection: exponential backoff up to 5 minutes

### Phase 3: Message Routing Implementation
**Beads:** pigeon-szb (main), pigeon-router-detect, pigeon-router-create, pigeon-router-archive
**Duration:** 2-3 hours

Create `pigeon/router.py` with MessageRouter:
- Watch `dev_notes/inbox/` for new markdown files
- Parse markdown metadata
- Detect target projects by examining `.beads/` databases
- Create bead issues in target projects
- Archive processed files to `dev_notes/inbox-archive/`

**Key Features:**
- Project detection: scan modules for .beads/pigeon.db
- Metadata preservation: slack_user_id, slack_timestamp, original_message
- Title generation: first line of message or auto-generated
- Priority parsing: P0-P4 from message if specified
- Error handling: log unparseable messages, retry on failure

### Phase 4: STT Pipeline Integration
**Beads:** pigeon-stt-integration
**Duration:** 1-2 hours

Integrate with second_voice (STT pipeline):
- Detect audio attachments in Slack messages
- Download audio from Slack
- Call second_voice subprocess for transcription
- Insert transcript into markdown (with speaker info if available)
- Handle transcription failures gracefully

### Phase 5: Comprehensive Testing
**Beads:** pigeon-daemon-tests, pigeon-router-tests, pigeon-integration-tests
**Duration:** 2-3 hours

Test coverage:
- SlackListenerDaemon: 40+ tests
  - Socket Mode connection, reconnection, error recovery
  - User authorization, message filtering
  - Markdown conversion, metadata handling
  - Attachment processing
- MessageRouter: 35+ tests
  - File parsing, metadata extraction
  - Project detection logic
  - Bead creation, archive operations
  - Error handling
- Integration: 15+ tests
  - End-to-end message ingestion and routing
  - STT pipeline integration
  - Error scenarios

### Phase 6: Configuration & Deployment
**Beads:** pigeon-config-docs, pigeon-deployment
**Duration:** 1 hour

- Update README with Slack integration setup instructions
- Document environment variable configuration
- Provide example .env configuration
- Document troubleshooting guide (connection issues, auth failures, etc.)

---

## File Structure

```
pigeon/
├── config.py (updated: add SlackConfig)
├── daemon.py (new: SlackListenerDaemon)
├── router.py (new: MessageRouter)
├── sources/
│   └── slack.py (existing: SlackSource base, reference)
└── tests/
    ├── test_daemon.py (new: 40+ tests)
    ├── test_router.py (new: 35+ tests)
    └── test_slack_integration.py (new: 15+ tests)

dev_notes/
├── project_plans/
│   └── 2026-02-23_pigeon-slack-integration-plan.md (this file)
└── inbox/ (created at runtime)
```

---

## Success Criteria

**Core Functionality:**
- ✅ Slack connection via Socket Mode with proper authentication
- ✅ Real-time message ingestion from #hentown-inbox
- ✅ Message conversion to markdown with metadata
- ✅ User authorization enforcement
- ✅ Automatic reconnection on connection loss
- ✅ Message routing to target projects
- ✅ Project detection via .beads/ database inspection
- ✅ Bead issue creation in target projects
- ✅ File archival after processing

**Reliability:**
- ✅ Graceful error handling (no crashes on Slack errors)
- ✅ Exponential backoff reconnection logic
- ✅ Comprehensive logging for debugging
- ✅ Handles network timeouts and transients

**Testing:**
- ✅ 90+ unit tests (daemon 40+, router 35+, integration 15+)
- ✅ All tests passing
- ✅ 95%+ code coverage
- ✅ Mock Slack SDK for testing without credentials

**Code Quality:**
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Follows Python conventions (PEP 8)
- ✅ No security vulnerabilities
- ✅ Proper error messages and logging

**Documentation:**
- ✅ README updated with setup instructions
- ✅ Environment variable configuration documented
- ✅ Example .env provided
- ✅ Troubleshooting guide
- ✅ Architecture decision rationale in project-context.md

---

## Timeline Estimate

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 1 | Config Setup | 30 min | Planned |
| 2 | SlackListenerDaemon | 2-3 hrs | Planned |
| 3 | MessageRouter | 2-3 hrs | Planned |
| 4 | STT Integration | 1-2 hrs | Planned |
| 5 | Testing | 2-3 hrs | Planned |
| 6 | Docs & Deploy | 1 hr | Planned |
| | **Total** | **9-15 hours** | |

**Critical Path:** Phase 1 → 2 → 3 → 4 → 5 → 6 (sequential)

---

## Dependencies

**Internal:**
- pigeon-gjf: RESEARCH - Clarify Slack Integration Questions ✅ (closed)
- hatchery: Slack SDK patterns and error handling reference
- second_voice: STT pipeline for audio transcription

**External:**
- slack-sdk Python library
- anthropic (Claude API for future NLU, if needed)
- Slack app credentials (bot token, app token)

---

## Risk Assessment

**Low Risk:**
- Slack SDK integration (well-documented, mature library)
- File-based inbox approach (already designed in project-context.md)
- Python subprocess for STT (standard approach)

**Medium Risk:**
- Socket Mode connectivity (network-dependent)
  - Mitigation: Robust reconnection with exponential backoff
  - Mitigation: Comprehensive logging for debugging
- Message parsing (malformed metadata)
  - Mitigation: Graceful error handling, fallback defaults
  - Mitigation: Archive unparseable messages for manual review

**High Risk:**
- None identified. Architecture decisions reduce risk by:
  - Separating listener and router (isolation)
  - Using file-based inbox (decouples Slack from routing)
  - Phased approach (learn patterns before abstracting)

---

## Future Enhancements (Out of Scope)

1. **Unified Slack Library** - Extract hentown-slack-core after mellona implements
2. **Message Scheduling** - Schedule messages for batch processing
3. **Slack Threading** - Track Slack thread conversations
4. **Interactive Responses** - Reply to Slack messages from pigeon router
5. **Rich Slack UI** - Use Slack blocks/buttons instead of text
6. **Multi-Channel Support** - Listen to multiple Slack channels
7. **User Profiling** - Track user preferences and history
8. **Analytics** - Track message routing patterns and success rates

---

## Related Documentation

- **pigeon/docs/project-context.md** - Design rationale and architecture overview
- **hentown/dev_notes/project_plans/2026-02-19_00-07-17_hatchery-epic-5-slack-integration.md** - Hatchery Slack integration reference
- **hentown/dev_notes/specs/2026-02-18_mellona-pigeon-specification.md** - Integration patterns and config hierarchy

---

## Beads to Create

After this plan, create these beads:

**Phase 1 (Configuration):**
- pigeon-cfg: Update pigeon/config.py with SlackConfig dataclass
- pigeon-env: Update .env.example with PIGEON_SLACK_* variables

**Phase 2 (SlackListenerDaemon):**
- pigeon-nxo: Main Slack listener implementation (already exists, now with clear acceptance criteria)
- pigeon-daemon-auth: Credential verification and auth logic
- pigeon-daemon-socket: Socket Mode connection and reconnection
- pigeon-daemon-events: Message event handling and filtering

**Phase 3 (MessageRouter):**
- pigeon-szb: Main router implementation (already exists, now with clear acceptance criteria)
- pigeon-router-detect: Project detection logic
- pigeon-router-create: Bead issue creation
- pigeon-router-archive: File archival and cleanup

**Phase 4 (STT Integration):**
- pigeon-stt-integration: Audio attachment handling and transcription

**Phase 5 (Testing):**
- pigeon-daemon-tests: SlackListenerDaemon unit tests
- pigeon-router-tests: MessageRouter unit tests
- pigeon-integration-tests: End-to-end integration tests

**Phase 6 (Documentation & Deployment):**
- pigeon-config-docs: README and setup documentation
- pigeon-deployment: Deployment guide and troubleshooting

---

## Implementation Notes for Agents

### Slack Configuration Best Practices
- Store tokens in environment variables only, never commit
- Validate tokens on daemon startup (auth_test API call)
- Handle token expiry gracefully (reconnect, prompt for new token)
- Log token validation for debugging (without exposing token)

### Socket Mode Implementation
- Use slack_sdk.socket_mode.SocketModeClient
- Register event handlers before connecting
- Acknowledge all requests immediately
- Handle reconnection automatically
- Set reasonable timeouts (30s connect, 60s event process)

### Message Markdown Format
```markdown
# Slack Message from @{user}

**Date:** {timestamp}
**User:** {slack_user_id}
**Channel:** {channel}
**Thread:** {thread_ts}

---

{message_content}

## Attachments

{attachment_list}
```

### Error Handling Philosophy
- Log all errors with context (user, message, stack trace)
- Never crash daemon on Slack error (continue operation)
- Archive unparseable messages for manual review
- Notify via logs if message routing fails (for observability)

### Testing Approach
- Mock SlackClient (don't connect to real Slack in tests)
- Use fixtures for sample messages and metadata
- Test error paths explicitly (network errors, malformed messages)
- Use pytest with 90%+ coverage requirement

---

## Lessons Learned (To Be Filled During Implementation)

*Document here as implementation progresses*

---

## Sign-Off

**Proposed By:** Claude Code (pigeon-gjf clarifying questions process)
**Status:** Awaiting implementation start
**Next Steps:** Create pigeon-cfg (Phase 1) and begin configuration setup

