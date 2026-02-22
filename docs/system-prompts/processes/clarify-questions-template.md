# Clarify Questions Template

> 5 universal question types, with domain-specific examples for slack integrations, architecture decisions, standards compliance, documentation, and maintainability.

---

## Question Type 1: Architecture & Integration Pattern

**Purpose**: Clarify how new work fits into existing system architecture and integration points.

**Generic Template**:
```
### Question 1: [Feature] Architecture—[Decision Point]?

**Context**:
Research shows [finding from commits/beads/docs]. Current architecture uses
[existing pattern]. The planned work ([scope]) could follow multiple approaches.

**Options**:
- Option A: [Approach 1 - description of how it integrates, pros/cons]
- Option B: [Approach 2 - different integration strategy, pros/cons]
- Option C: [Approach 3 - alternative pattern, pros/cons]

**Why This Matters**:
[Architecture decision impacts: consistency with existing patterns / future integrations /
maintainability / team understanding / performance characteristics]

**Related Recent Work**:
- Commit: [recent commit hash] ([what changed])
- Bead: [recent closed bead] (lessons learned)
- Spec: [related architecture doc]
```

### Example 1: Slack Integration - Channel Architecture

```
### Question 1: Slack Channel Architecture—Dedicated vs. Shared Channels?

**Context**:
Recent research shows hatchery and pigeon both need Slack presence. Current hentown
uses dedicated channels (#hentown-activity, #hentown-inbox). Pigeon could post to
#hentown-inbox OR create its own #pigeon-activity channel.

**Options**:
- Option A: **Unified Channel** - Both pigeon and hatchery post status to #hentown-activity
  (Pros: Single pane of glass for all automation; Cons: more noise, harder to filter)
- Option B: **Dedicated Channels** - hatchery→#hentown-activity, pigeon→#pigeon-activity
  (Pros: clear separation, each team owns their channel; Cons: user must monitor multiple channels)
- Option C: **Hybrid** - Activity goes to dedicated channels, high-priority alerts to #hentown-activity
  (Pros: detailed info where it belongs, critical alerts visible everywhere; Cons: complexity in priority logic)

**Why This Matters**:
This shapes how notifications are organized, affects user experience (information density),
and sets pattern for future modules (mellona, logist, etc.) that will also need Slack integration.

**Related Recent Work**:
- Commit: 9e6d746 (hatchery Epic 5 planning)
- Spec: dev_notes/project_plans/2026-02-19_00-07-17_hatchery-epic-5-slack-integration.md
- Bead: hentown-aog (mellona Ph5 - similar notification patterns needed)
```

---

## Question Type 2: Standards & Best Practices Compliance

**Purpose**: Clarify alignment with Python library standards, modern patterns, and team conventions.

**Generic Template**:
```
### Question N: [Component] Standards—[Decision Point]?

**Context**:
Research found [current state in project]. [Modern standard/best practice]
suggests [recommendation]. Our recent work on [similar feature] used [pattern].

**Options**:
- Option A: [Follow best practice approach, rationale, implications]
- Option B: [Keep current pattern for consistency, rationale, when to revisit]
- Option C: [Hybrid approach, combining elements, tradeoffs]

**Why This Matters**:
Standards compliance affects: developer onboarding / team velocity / external contributor
confidence / future refactoring effort / dependency choices.

**Related Recent Work**:
- Bead: [previous similar work]
- Doc: [standards reference]
- Commit: [recent related change]
```

### Example 2: Slack Integration - Configuration Management

```
### Question 2: Slack Config—Environment Variables vs. Config File vs. Secrets Manager?

**Context**:
Research shows hatchery currently uses `hatchery/config.py` + `.env` files (pattern
from logist, google-personal-mcp). Slack tokens are sensitive credentials. Modern
Python practices (e.g., python-dotenv, python-decouple) suggest centralizing credential
management. Recent mellona work established a config hierarchy pattern.

**Options**:
- Option A: **Status Quo (.env + config.py)** - Continue current pattern, update .env.example
  (Pros: already works, team familiar; Cons: credentials in .env during development, doesn't scale)
- Option B: **Secrets Manager (OS-level)** - Use keyring/python-keyring, fallback to env vars
  (Pros: encrypted storage, production-ready; Cons: requires setup, more complex for dev)
- Option C: **Config Hierarchy (as mellona does)** - ~/.config/hentown/ for user, env vars as override
  (Pros: scalable, follows modern Python conventions; Cons: more code, requires documentation)

**Why This Matters**:
Configuration management choice affects: security posture / developer experience / production
deployment complexity / how other projects (pigeon, mellona) will integrate Slack.

**Related Recent Work**:
- Spec: dev_notes/specs/2026-02-18_mellona-pigeon-specification.md (config patterns)
- Commit: d6d9f27 (mellona keys CLI - keyring backend integration)
- Bead: hentown-5dm (keyring backend implementation)
```

---

## Question Type 3: Documentation & Knowledge Capture

**Purpose**: Clarify what documentation is needed, at what level, and for whom.

**Generic Template**:
```
### Question N: [Feature] Documentation—[What Level]?

**Context**:
The [feature/component] involves [complexity level]. Similar work in [related project]
created [doc level]. Users of this feature are [audience]. Current documentation patterns
in the project are [state].

**Options**:
- Option A: [Light documentation - what it covers, sufficient for whom]
- Option B: [Comprehensive documentation - what it covers, effort required]
- Option C: [Progressive documentation - start minimal, expand based on adoption]

**Why This Matters**:
Documentation choices affect: new contributor onboarding / support burden / external
adoption / maintenance burden / knowledge preservation / future refactoring risk.

**Related Recent Work**:
- Doc: [related documentation]
- Bead: [similar feature documentation effort]
- Commit: [documentation-related change]
```

### Example 3: Slack Integration - Documentation Scope

```
### Question 3: Slack Integration Documentation—Scope for MVP?

**Context**:
Slack integration is novel for hatchery/pigeon ecosystem. Users need to: setup bot
credentials, configure channels, understand rate limits, troubleshoot connection issues.
Recent mellona work created comprehensive provider docs. Team has limited doc bandwidth.

**Options**:
- Option A: **Minimal (Setup Only)** - .env.example, quick setup instructions in README
  (Pros: fast to write, covers immediate need; Cons: users struggle with troubleshooting,
  limited adoption)
- Option B: **Comprehensive** - Setup guide, architecture deep-dive, troubleshooting,
  rate limit guide, security best practices
  (Pros: self-service, professional appearance; Cons: effort-intensive, maintenance burden)
- Option C: **Progressive** - MVP docs (setup + basic troubleshooting), expand based on
  real user questions captured in beads
  (Pros: focused on real needs, manageable effort; Cons: requires discipline to update)

**Why This Matters**:
Documentation scope shapes: ease of adoption / support load / ability to scale to other
modules / team time investment / user confidence in integration reliability.

**Related Recent Work**:
- Spec: dev_notes/project_plans/2026-02-19_00-07-17_hatchery-epic-5-slack-integration.md
- Bead: hentown-ddx (documentation patterns from mellona/pigeon integration work)
```

---

## Question Type 4: Maintainability & Technical Debt

**Purpose**: Clarify maintenance strategy to avoid future pain points.

**Generic Template**:
```
### Question N: [Feature] Maintenance—[Concern]?

**Context**:
The [feature] will need to handle [complexity]. Similar implementations in [project]
discovered [maintenance issue]. Current project patterns for [concern] are [state].

**Options**:
- Option A: [Minimal approach - what's included, future refactor risk]
- Option B: [Overbuilt approach - what's included, complexity cost]
- Option C: [Pragmatic approach - balanced coverage, clear upgrade path]

**Why This Matters**:
Maintenance strategy affects: debugging complexity / future refactoring effort /
contributor friction / consistency with other modules / ability to adapt to new requirements.

**Related Recent Work**:
- Bead: [similar maintenance work]
- Lessons Learned: [what we learned from similar feature]
```

### Example 4: Slack Integration - Error Handling & Recovery

```
### Question 4: Slack Integration—Error Handling & Recovery Strategy?

**Context**:
Slack connection is network-dependent. Research shows hatchery daemon should be resilient
to network failures, credential expiry, rate limits. Recent mellona work on provider
fallback chains showed complexity of retry logic. Current hentown patterns are minimal.

**Options**:
- Option A: **Minimal** - Log errors, continue daemon, manual recovery
  (Pros: simple code, fast to implement; Cons: daemon silently fails Slack, user unaware,
  manual fix required)
- Option B: **Comprehensive** - Exponential backoff, circuit breaker, automatic reconnection,
  slack error notifications to admin email
  (Pros: production-ready, excellent reliability; Cons: ~200 lines code, testing complexity)
- Option C: **Pragmatic** - Automatic reconnect with jitter, log errors prominently,
  CLI command to check Slack health status
  (Pros: catches most failures, maintainable; Cons: still some manual intervention needed)

**Why This Matters**:
Error handling choice affects: production reliability / debugging time when things break /
user frustration / whether users trust automation / future feature additions (pigeon,
mellona also depend on Slack reliability).

**Related Recent Work**:
- Spec: dev_notes/specs/2026-02-20_23-35-00.md (executor pool error handling)
- Lessons Learned: (from hentown builds, network resilience issues)
```

---

## Question Type 5: Cross-Module Impact & Consistency

**Purpose**: Clarify how decisions affect other projects and maintain ecosystem consistency.

**Generic Template**:
```
### Question N: [Feature] Cross-Module—[Consistency Point]?

**Context**:
This work affects [modules/projects]. Each has [different state/pattern]. Research
shows [recent decisions in related projects]. Future work [related feature] depends
on how we decide this.

**Options**:
- Option A: [Project-specific approach - justification, impact on other projects]
- Option B: [Unified approach across projects - benefits, implementation cost]
- Option C: [Phased approach - start unified, diverge if needed - risk of drift]

**Why This Matters**:
Cross-module consistency affects: developer mental model / shared infrastructure reusability
/ migration paths for future work / team knowledge transfer / difficulty of future unification
efforts.

**Related Recent Work**:
- Integration: [related cross-project work]
- Spec: [shared architecture decision]
- Bead: [related work in other module]
```

### Example 5: Slack Integration - Unified vs. Project-Specific

```
### Question 5: Slack Integration—Unified hatchery-pigeon-mellona Client or Separate?

**Context**:
Hatchery, pigeon, and mellona all need Slack presence. Research shows:
- hatchery needs activity notifications + interactive commands
- pigeon needs #hentown-inbox listener + message routing
- mellona might eventually need execution status updates

Current plan: separate SlackClient implementations in each. But this duplicates:
auth, reconnection logic, message formatting, error handling. Mellona already
established shared library pattern for LLM providers.

**Options**:
- Option A: **Separate Clients** - Each project owns its Slack integration
  (Pros: autonomy, no cross-project coordination; Cons: duplicate code, inconsistent
  error handling, hard to upgrade shared behavior)
- Option B: **Shared Slack Library** - Create mellona-slack (or hentown-slack) for
  common patterns, projects build on top
  (Pros: DRY, consistent behavior, easier maintenance; Cons: upfront effort, coordination
  overhead, future integration work)
- Option C: **Phased Approach** - Start separate, extract shared client once patterns clear
  (Pros: learn what's actually shared before abstracting; Cons: refactoring burden later,
  temporary duplication)

**Why This Matters**:
Architectural choice affects: code maintenance burden across 3 projects / ability to
fix bugs centrally / future module additions / team velocity on Slack-related changes /
risk of inconsistent user experience across modules.

**Related Recent Work**:
- Architecture: mellona library design (shared provider abstraction)
- Spec: dev_notes/specs/2026-02-18_mellona-pigeon-specification.md
- Epic: pigeon + hatchery Slack integration beads (hentown-ye5, hentown-6ge)
```

---

## Using This Template

### For Agents Creating Questions:

1. **Select 5 question types** based on scope:
   - **Always use**: Type 1 (Architecture) + Type 5 (Cross-Module Impact)
   - **When applicable**: Type 2 (Standards), Type 3 (Documentation), Type 4 (Maintenance)
   - Adjust based on scope (e.g., infrastructure-heavy → emphasize Type 4)

2. **Ground each question** in research:
   - Reference specific commits, beads, docs
   - Show what you found during discovery phase
   - Justify why THIS question matters for THIS project

3. **Format consistently**:
   - Use structured markdown (Context, Options, Why This Matters, Related Work)
   - Keep options balanced (no leading the human)
   - Make each option viable (avoid strawman options)

4. **Customize for domain**:
   - Slack integration example shows how to instantiate template
   - Adapt example language for your specific scope
   - Keep examples grounded in actual recent work

### For Humans Answering Questions:

- Each option represents a real tradeoff
- Pick the one that aligns with project values/goals
- Elaborate if you have context the research missed
- Ask for clarification if options aren't clear

---

## Common Pitfalls

❌ **Questions too vague** - "Should we document this?" (What level? For whom?)
✅ **Questions specific** - "What documentation scope: minimal setup guide vs. comprehensive guide?"

❌ **Questions without grounding** - "What's the right architecture?"
✅ **Questions grounded in research** - "Research shows X pattern; should we adopt for Y reason?"

❌ **Biased options** - "Should we follow best practices or cut corners?"
✅ **Balanced options** - "Option A: best practice (effort/benefit tradeoffs); Option B: pragmatic (effort/benefit tradeoffs)"

❌ **Too many/too few questions** - 8 questions is exhausting; 2 questions misses nuance
✅ **Exactly 5 questions** - Manageable, covers major decision areas

---

## Lessons Learned & Improvements

*Document here as clarify-questions process executes across projects.*

