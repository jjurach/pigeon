# Planning Pre-Flight Checklist

**Purpose:** Unified validation checklist for planners before creating approval beads. Consolidates all external dependency, tool reliability, and process validation requirements to prevent blocking issues during implementation.

**When to use:** After creating project plan (logs-first Step C), before creating approval bead (plan-and-dispatch Step 1.2)

**Responsibility:** Planner agent (before requesting human approval)

---

## Checklist

### 1. External Dependencies (CRITICAL)

**Purpose:** Ensure all external resources referenced in the plan are accessible and documented.

- [ ] **Identify all external resources**
  - List every external tool, library, API, data file, or codebase required
  - Include: git repositories, S3 buckets, APIs, third-party services, external source code

- [ ] **Verify each external resource is accessible NOW**
  - Test the URL/path immediately (don't assume availability)
  - If it's a git repo: clone/fetch it
  - If it's an API: make a test request
  - If it's a file: verify it exists and has expected structure
  - Document the access method in the plan

- [ ] **For each missing or inaccessible resource:**
  - Add acquisition instructions to the plan
  - Document where/how to get it
  - Include setup steps or prerequisites
  - Specify authentication/credentials needed (without storing secrets)
  - Define fallback plan (defer? mock? alternative?)

- [ ] **Plan includes remediation path**
  - If resource unavailable at approval time: Plan should specify what happens
  - Options: Create pre-flight validation bead, defer epic, mock resource, use alternative
  - Risk explicitly acknowledged and documented

**Example (from Mobile App Migration):**
```
External Dependency: external/orig/apps/mobile/ (source code)

Verification:
- [ ] Directory exists
- [ ] Contains src/, assets/, android/, ios/ subdirectories
- [ ] Files not empty (not stubs)
- [ ] Can build/run without additional resources

If Missing:
- [ ] Document acquisition instructions
- [ ] Defer phase pj-8 until source provided
- [ ] Block dependent phases pj-11, pj-12 explicitly
```

---

### 2. Project Plan Structure (CRITICAL)

**Purpose:** Ensure plan is clear, sequenced, and realistic.

- [ ] **Phases clearly defined**
  - Each phase has distinct scope
  - Phases sequenced logically (dependencies respected)
  - No circular dependencies (Phase A → B → C, not C → A)

- [ ] **Deliverables specified for each phase**
  - What files/features/tests will exist after each phase?
  - Clear "done" criteria that can be verified

- [ ] **Effort estimates included**
  - Hours or days per phase
  - Realistic based on similar prior work
  - Contingency included for unknowns

- [ ] **Dependencies documented**
  - Between phases ("Phase 2 requires Phase 1 complete")
  - On external resources ("Requires external app source")
  - On tooling/environment ("Requires DynamoDB Local installed")

- [ ] **Risks identified**
  - What could go wrong?
  - How will you detect/handle it?
  - Mitigation strategy specified

---

### 3. Process Alignment (IMPORTANT)

**Purpose:** Ensure plan follows established workflows and won't introduce surprises.

- [ ] **Plan references established patterns**
  - Uses documented naming conventions
  - Follows standard file structure
  - Aligns with existing tooling (beads, logs-first, etc.)

- [ ] **Plan includes Standard Epic Suffix (if applicable)**
  - If creating an epic (5+ phases):
    - [ ] Last phase before suffix: final implementation task
    - [ ] Suffix Phase 1: Self-Healing System Prompts & Documentation
    - [ ] Suffix Phase 2: Workflow Improvement Analysis
  - See: [plan-and-dispatch.md Step 1.4](../workflows/plan-and-dispatch.md)

- [ ] **Implementation beads will have clear closure criteria**
  - Each bead references specific deliverables
  - Success is objectively verifiable
  - Change documentation template identified

---

### 4. Tool & Environment Prerequisites (IMPORTANT)

**Purpose:** Prevent "tool not available" surprises during implementation.

- [ ] **All required tools documented**
  - Language/runtime versions (Node 18.x? Python 3.10+?)
  - Build tools (npm, pytest, cargo, etc.)
  - External services (AWS, Docker, DynamoDB Local)
  - Development tools (Git, text editor, terminal)

- [ ] **Installation/setup instructions included**
  - Link to tool setup guides in docs/
  - Or explicit steps if custom setup needed
  - Troubleshooting section for common issues

- [ ] **Environment assumed in plan is realistic**
  - Will all team members have this environment?
  - Or only specific machine types?
  - Documented clearly to prevent surprises

- [ ] **Tool reliability patterns identified**
  - Any tools known to have flakiness?
  - See: [tool-reliability.md](../patterns/tool-reliability.md)
  - Plan includes fallback strategies if needed

**Example:**
```
Required Tools:
- Node.js 18.x (use nvm to install)
- AWS CLI v2 with local credentials
- DynamoDB Local (npm install globally)
- Docker (for DynamoDB Local)
- Jest 28+ for testing

Troubleshooting:
- If DynamoDB Local fails to start: [See DynamoDB Local troubleshooting section]
- If npm install fails: [See ESM/CommonJS compatibility notes]
```

---

### 5. Team/Authority Alignment (IMPORTANT)

**Purpose:** Ensure human reviewer won't find surprises when approving.

- [ ] **Plan scope is within team authority**
  - Not requesting architecture changes beyond scope
  - Not introducing new dependencies without justification
  - Not changing established patterns without discussion

- [ ] **Plan is reviewable by human**
  - Plan file is readable (~200-400 lines max for approval)
  - Complex details in separate reference files
  - Key decisions/risks highlighted at top

- [ ] **No hidden assumptions**
  - Plan doesn't assume decisions made elsewhere
  - Doesn't depend on other unrelated work
  - Prerequisites clearly listed upfront

---

### 6. Lessons Learned Preparation (NICE-TO-HAVE)

**Purpose:** Set up knowledge capture for continuous improvement.

- [ ] **Plan references docs where lessons will be recorded**
  - Example: "See dev_notes/project_plans/ for lessons learned"
  - Or: "Lessons captured in change documentation"

- [ ] **Process feedback section included in plan**
  - Template for noting workflow friction points
  - Link to [workflow improvement process](../processes/workflow-improvement-analysis.md)

---

## Self-Check

Before considering plan "ready for approval", answer these questions:

1. **Could a colleague with access to this repo successfully start Phase 1 with just the plan and beads?**
   - If no: Add missing details

2. **Would I notice immediately if an external resource becomes unavailable?**
   - If no: Add explicit verification step

3. **Are there any assumptions I'm making that aren't documented?**
   - If yes: Add them to Prerequisites or Dependencies

4. **Could Phase 1 start tomorrow, or are there blockers I haven't acknowledged?**
   - If blockers exist: Document them explicitly

5. **Have I used established patterns, or am I inventing new ones?**
   - If new patterns: Justify why and plan to document them

---

## How Planner Uses This

**Workflow integration:**

1. Create project plan (logs-first Step C)
2. **Run this checklist** against the plan
3. Fix any "No" answers before proceeding
4. Create approval bead with checklist reference:
   ```bash
   bd create "Approve: [Plan Name]" --label approval \
     --body "Plan: dev_notes/project_plans/YYYY-MM-DD_HHM-SS_name.md

   ✓ Planning Pre-Flight Checklist complete
   See: docs/system-prompts/checklists/planning-preflight.md

   Review Checklist:
   - [ ] External dependencies verified
   - [ ] Plan structure clear
   - [ ] Effort estimates reasonable

   Approve by closing this bead."
   ```
5. Proceed to plan-and-dispatch Step 1.3+

---

## How Humans Use This

When reviewing an approval bead:

1. Check that planner referenced this checklist
2. If "No" answers exist, ask planner to fix before approving
3. Special focus on #1 (External Dependencies) - this blocked entire phases in pj-5
4. Look for hidden assumptions that planner missed

---

## Examples

### ✅ GOOD: Plan with external dependency fully validated

```
External Dependency: External app source at external/orig/apps/mobile/

Verification Completed:
✓ Directory exists at specified location
✓ Contains required subdirectories (src/, assets/, android/, ios/)
✓ Sample source files reviewed (not empty stubs)
✓ Can be accessed by all team members
✓ No authentication required

Acquisition: Source already in repo, no action needed
Fallback: N/A (resource available)
```

### ❌ BAD: Plan with unvalidated external dependency

```
Phase 2: Port source code from external app

Note: We'll need to get the source from the external repository
(assumes it exists and we can access it)
```

### ✅ GOOD: Plan with missing resource and explicit handling

```
External Dependency: External app source

Current Status: Source not available (repo access required)

Remediation:
- Phase 1 (pj-7): Complete and standalone
- Phases 2-4 (pj-8, pj-11, pj-12): DEFERRED pending source availability
- Rationale: Can't port code without source; prevents wasted effort
- Trigger: When source becomes available, reactivate deferred phases

Documentation: See external-resources.md for acquisition path
```

---

## Integration with Other Documents

- **Parent:** [plan-and-dispatch.md Step 1](../workflows/plan-and-dispatch.md) (Planner Agent)
- **Related:** [external-resources.md](../templates/external-resources.md) (Detailed resource guide)
- **Related:** [tool-reliability.md](../patterns/tool-reliability.md) (Tool fallback patterns)
- **Related:** [phase-review-checkpoint.md](../templates/phase-review-checkpoint.md) (Mid-epic reviews)

---

**Last Updated:** 2026-02-15
**Created by:** pj-14 - Phase 1: Workflow Improvements
**Status:** Ready for use
