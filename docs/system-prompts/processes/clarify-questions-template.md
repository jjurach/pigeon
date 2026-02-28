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

### Example 1: [Feature] - [Decision Point]

```
### Question 1: [Feature] [Architecture Aspect]—[Option A] vs. [Option B]?

**Context**:
Recent research shows [finding from project state]. The [related component]
uses [existing pattern]. [Scope] could follow multiple approaches.

**Options**:
- Option A: **[Approach 1 Name]** - [Description with tradeoffs]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option B: **[Approach 2 Name]** - [Description with tradeoffs]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option C: **[Approach 3 Name]** - [Description with tradeoffs]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])

**Why This Matters**:
This decision shapes [impact 1], [impact 2], and [sets pattern for impact 3].

**Related Recent Work**:
- Commit: [commit hash] ([what changed])
- Spec: dev_notes/project_plans/[date_filename]
- Bead: [related_bead_id] (related phase)
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

### Example 2: [Feature] - Standards Compliance

```
### Question 2: [Component] [Standards Area]—[Approach A] vs. [Approach B]?

**Context**:
Research shows [project] currently uses [current pattern] (pattern
from [related module(s)]). [Concern about current approach]. Modern
[technology/standard] practices suggest [recommendation].

**Options**:
- Option A: **[Approach 1]** - [Description of implementation]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option B: **[Approach 2]** - [Description of implementation]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option C: **[Approach 3]** - [Description of implementation]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])

**Why This Matters**:
[Standards/approach] choice affects: [impact 1] / [impact 2] / [impact 3] /
how other projects will [related concern].

**Related Recent Work**:
- Spec: dev_notes/specs/[date_filename].md ([topic])
- Commit: [commit hash] ([what changed])
- Bead: [example_bead_id] ([related work])
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

### Example 3: [Feature] - Documentation Scope

```
### Question 3: [Feature] Documentation—Scope for MVP?

**Context**:
[Feature] is [assessment of novelty/importance]. Users need to: [task 1],
[task 2], [task 3], [task 4]. Recent [related work] created [documentation level].
Team has [constraint: time/resources/bandwidth].

**Options**:
- Option A: **Minimal** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option B: **Comprehensive** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option C: **Progressive** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])

**Why This Matters**:
Documentation scope shapes: [impact 1] / [impact 2] / [impact 3] /
[cross-module concern].

**Related Recent Work**:
- Spec: dev_notes/project_plans/[date_filename]
- Bead: [related_bead_id] (documentation patterns from [related work])
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

### Example 4: [Feature] - Maintainability & Resilience

```
### Question 4: [Feature]—Error Handling & Recovery Strategy?

**Context**:
[Feature] depends on [external system/concern]. Research shows [component] should be resilient
to [failure modes]. Recent [related work] on [similar pattern] showed complexity of [concern].
Current project patterns are [assessment].

**Options**:
- Option A: **Minimal** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option B: **Comprehensive** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option C: **Pragmatic** - [What's included], [coverage]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])

**Why This Matters**:
Error handling choice affects: [impact 1] / [impact 2] / [impact 3] /
whether [stakeholders] trust [feature].

**Related Recent Work**:
- Spec: dev_notes/specs/[date_filename].md ([topic])
- Lessons Learned: [relevant patterns]
```

---

## Question Type 5: Cross-Module Impact & Consistency

**Purpose**: Clarify how decisions affect other projects and maintain ecosystem consistency.

**Generic Template**:
```
### Question N: [Feature] Cross-Module—[Consistency Point]?

**Context**:
This work affects [submodule_projects]. Each has [different state/pattern]. Research
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

### Example 5: [Feature] - Cross-Module Consistency

```
### Question 5: [Feature]—[Unified/Separate/Phased] Approach?

**Context**:
[Module-a], [module-b], and [module-c] all need [feature]. Research shows:
- [module-a] needs [requirement 1]
- [module-b] needs [requirement 2]
- [module-c] might eventually need [requirement 3]

Current plan: [approach]. But this [potential issue: duplication/complexity/coordination].
[Related work] already established [relevant pattern].

**Options**:
- Option A: **[Approach 1]** - [Description with ownership/coordination model]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option B: **[Approach 2]** - [Description with ownership/coordination model]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])
- Option C: **[Approach 3]** - [Description with ownership/coordination model]
  (Pros: [benefit 1], [benefit 2]; Cons: [tradeoff 1], [tradeoff 2])

**Why This Matters**:
Architectural choice affects: [impact 1] / [impact 2] / [impact 3] /
risk of [consequence].

**Related Recent Work**:
- Architecture: [design reference]
- Spec: dev_notes/specs/[date_filename]
- Epic: [Feature] beads across modules
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

