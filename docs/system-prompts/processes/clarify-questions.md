# Clarify Questions Process

> A cross-project workflow for researching system state, identifying improvement opportunities, and gathering human input before major planning decisions.

## Overview

The **Clarify Questions Process** enables agents to:

1. **Research** recent commits, closed beads, dev_notes, and project state
2. **Synthesize** findings into 5 actionable clarifying questions
3. **Present** questions in structured markdown format
4. **Block** for human interaction using gates (if in bead context) or direct halt
5. **Iterate** interactively with human on resume
6. **Adjust** future work based on answers

This process applies to **any project with `docs/system-prompts/`** and is **universal across all projects in the ecosystem**.

---

## When to Apply This Process

### Auto-Trigger Conditions
Apply clarify-questions automatically when:
- Creating major epics or significant features
- Planning new modules or system components
- Establishing new integrations (Slack, external APIs, etc.)
- Beginning multi-phase implementations
- Starting infrastructure or architecture work

### Manual Invocation
Apply on-demand when:
- User explicitly requests: "Apply clarify-questions.md to [scope]"
- Uncertainty exists about approach or requirements
- Multiple valid implementation paths exist
- Cross-project impact unclear

---

## Process Phases

### Phase 1: Discovery (Agent-Driven Research)

**Duration**: 5-15 minutes
**Context**: Agent runs this in the project context

Agent performs:
```
1. Scan recent commits (last 2 weeks)
   - git log --oneline --since="2 weeks ago"
   - Identify patterns, trends, recent decisions

2. Review closed beads (recent work)
   - bd list --status=closed --limit=20
   - Read "lessons learned" sections
   - Extract patterns, blockers, decisions

3. Read dev_notes changes
   - Scan recent specs/ project_plans/ changes/
   - Identify patterns in planning, architecture, requirements
   - Note any stated uncertainties or open questions

4. Understand current system state
   - Read relevant README.md, ARCHITECTURE.md
   - Identify gaps between documented intent and reality
   - Note Python/standards compliance, maintainability concerns

5. Check for related projects' work
   - For parent projects: check all submodule projects
   - For submodules: check parent project coordination hub
   - Identify integration points, dependencies, patterns
```

**Outcome**: Rich understanding of project context, recent decisions, patterns, gaps.

---

### Phase 2: Synthesis (Agent-Generated Questions)

**Duration**: 5-10 minutes
**Context**: Agent thinks through research

Agent synthesizes 5 clarifying questions:

```
Question Selection Criteria:
✓ Each question should address a potential improvement
✓ Each question should have real project impact
✓ Questions should span: architecture, standards, maintainability, documentation, integration
✓ Each question should offer options or actionable paths
✓ Questions should be grounded in research (reference specific commits/beads/docs)
```

**Question Format** (structured markdown):

```markdown
## Clarifying Questions: [Scope]

### Question 1: [Title]
**Context**: [What did we find in research that prompted this?]
**Options**:
- Option A: [Description of approach A and tradeoffs]
- Option B: [Description of approach B and tradeoffs]
- Option C: [Description of approach C and tradeoffs]

**Why This Matters**: [Impact on project quality, maintenance, integration]

**Related Recent Work**: [Reference commits/beads/docs that informed this]

---

### Question 2: [Title]
...
```

See `clarify-questions-template.md` for 5 universal question types with examples.

---

### Phase 3: Presentation & Blocking

**Duration**: Immediate, then 24-48 hours
**Context**: Agent presents findings to human

#### If in Bead Context (executing as bead):

1. **Create human gate** to block on clarification:
   ```bash
   bd gate create \
     --await human:clarify-[scope] \
     --title "Clarifying Questions: [Scope]" \
     --timeout 48h
   ```

2. **Post structured markdown** with 5 questions in gate comment

3. **Update bead** status:
   ```bash
   bd update <bead-id> \
     --status=blocked \
     --notes="RESEARCH COMPLETE: Identified 5 clarifying questions. GATE: human:clarify-[scope]. Awaiting human answers to proceed."
   ```

4. **Display to human**:
   - Show gate ID
   - Show question summary
   - Explain: "Gate blocks until you approve. Session will pause here."

#### If NOT in Bead Context:

1. **Display structured markdown** with 5 questions directly

2. **Halt execution**:
   - Message: "Research complete. Awaiting your input to proceed."
   - Wait for human response
   - No gate created, no bead status change

**Human Experience**: Same either way—questions presented, agent waits for input.

---

### Phase 4: Resume & Iteration (Interactive Q&A)

**Duration**: 5-20 minutes
**Context**: On `--resume` or user resumption

When agent resumes (or human is ready to answer):

1. **Present questions interactively** (one at a time):
   ```
   Question 1 of 5: [Title]

   [Full context and options from Phase 2]

   What's your preference? (A / B / C / Custom)
   ```

2. **Collect human answer**:
   - Accept selection (A/B/C)
   - Or custom text input for flexibility
   - Capture reasoning if human provides it

3. **Move to next question**:
   ```
   Q1 Answer: Option B ✓

   Question 2 of 5: [Title]
   [context and options]
   ```

4. **Offer extended interaction**:
   ```
   Completed: 5/5 questions

   Would you like to explore deeper on any question,
   or discuss related considerations?
   ```

5. **Collect follow-up insights**:
   - Allow human to ask clarifying questions back
   - Allow human to suggest additional considerations
   - Build richer context for Phase 5

---

### Phase 5: Adjustment & Closure

**Duration**: 10-15 minutes
**Context**: Agent uses answers to improve future work

Agent actions:

1. **Document answers**:
   ```
   bd update <bead-id> --notes "
   RESEARCH: [summary of research phase]

   QUESTIONS & ANSWERS:
   Q1: [question] → A: [human answer]
   Q2: [question] → A: [human answer]
   Q3: [question] → A: [human answer]
   Q4: [question] → A: [human answer]
   Q5: [question] → A: [human answer]

   FOLLOW-UP: [any additional insights from discussion]

   ADJUSTMENTS MADE: [list what changed based on answers]
   "
   ```

2. **Create/update related beads** based on answers:
   - Create new beads for recommended improvements
   - Update acceptance criteria on pending beads
   - Add new dependencies if architectural decisions changed
   - Link new beads with `discovered-from` relationship

3. **Squash research wisp** (if used persistent molecule):
   ```bash
   bd mol squash <wisp-id> --summary "Clarify questions research: [key decisions made]"
   ```

4. **Close or unblock bead**:
   - Close clarify bead if scope complete
   - Or unblock dependent beads if they were waiting
   ```bash
   bd close <clarify-bead-id> --reason="Research complete, answers inform future work on [list dependent beads]"
   ```

5. **Close human gate** (if in bead context):
   ```bash
   bd gate approve <gate-id> --comment "Human reviewed and answered clarifying questions"
   ```

---

## Implementation Checklist for Agents

### Before Starting
- [ ] Identify scope (e.g., "feature X across module-a and module-b")
- [ ] Check if in bead context (executing as bead task) or standalone
- [ ] Confirm `docs/system-prompts/processes/clarify-questions-template.md` exists in project

### Phase 1: Discovery
- [ ] Scan commits (last 2 weeks) for patterns
- [ ] List recent closed beads (last 20)
- [ ] Read recent dev_notes changes
- [ ] Read relevant architecture/design docs
- [ ] Check related projects (root project and sibling modules)

### Phase 2: Synthesis
- [ ] Generate 5 questions using universal template
- [ ] Ground each question in research findings
- [ ] Ensure questions have real project impact
- [ ] Format as structured markdown

### Phase 3: Presentation & Blocking
- [ ] If bead context: create human gate with 48h timeout
- [ ] If bead context: update bead status to blocked with gate reference
- [ ] Display questions to human
- [ ] Wait for human input (gate approval or direct response)

### Phase 4: Resume & Iteration
- [ ] Present questions one-at-a-time on resume
- [ ] Collect human answers
- [ ] Offer follow-up exploration
- [ ] Record additional insights

### Phase 5: Adjustment & Closure
- [ ] Document all answers in bead notes
- [ ] Create/update beads based on answers
- [ ] Close human gate and/or clarify bead
- [ ] Report adjustments made to human

---

## Auto-Trigger Guidance

### How to Detect When to Auto-Apply

When creating beads for:
- **Epics** (major features, system components)
- **Multi-phase implementations**
- **Cross-module integrations**
- **Architecture or infrastructure changes**
- **New input/output flows**

**Trigger Rule**: If a bead would involve:
- More than 3 sub-beads, OR
- Changes across multiple projects/modules, OR
- Novel integration patterns, OR
- Significant architectural decisions

→ Auto-create a clarify-questions bead with **lower priority (P3-P4)** that **blocks** the epic until questions are answered.

---

## Related Files

- `clarify-questions-template.md` - 5 universal question types
- `AGENTS.md` - Agent workflow framework
- `tools/claude-code.md` - Claude Code tool guide
- `../processes/` - Other process documents

---

## Notes & Lessons Learned

*To be filled during execution—capture what works, what doesn't, improvements to the process.*

