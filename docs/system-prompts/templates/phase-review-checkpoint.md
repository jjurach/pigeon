# Template: Phase Review Checkpoint

**Purpose:** Conduct mid-epic review to capture lessons learned, validate assumptions, and adjust remaining phases as needed.

**When to use:** After completing 40-60% of an epic (after 2-3 phases of a 5+ phase epic)

**Responsibility:**
- **Worker:** Document findings and feedback after completing each phase
- **Planner:** Conduct formal review at midpoint and integrate feedback
- **Human:** Review checkpoint and approve adjustments if needed

**Expected Outcome:** Updated project plan with documented lessons, risk adjustments, and refinements to remaining phases

---

## Phase Review Checkpoint Template

### Header

```markdown
# Phase Review Checkpoint: [Epic Name]

**Epic:** [Epic ID and title]
**Project Plan:** dev_notes/project_plans/YYYY-MM-DD_original_plan.md
**Review Conducted:** [Date/Time]
**Review By:** [Agent name/role]
**Status:** [Draft / Ready for Approval / Approved]

**Phases Completed:** 1-3
**Phases Remaining:** 4-6
**Current Progress:** [45% / 60% / etc.]

---
```

### Actual Completion vs. Plan

Document how reality compared to the plan:

```markdown
## Actual vs. Planned Progress

| Phase | Original Estimate | Actual | Variance | Status |
|-------|-------------------|--------|----------|--------|
| Phase 1 | 8 hours | 7.5 hours | ✅ On track | ✓ Closed |
| Phase 2 | 12 hours | 15 hours | ⚠️ +25% | ✓ Closed |
| Phase 3 | 16 hours | [In progress] | ? | → In progress |
| Phase 4 | 10 hours | [Not started] | ? | ○ Ready |
| Phase 5 | 12 hours | [Not started] | ? | ○ Ready |

**Overall:** 45 hours planned vs. 22.5 actual so far → On track

### Detailed Phase Feedback

#### Phase 1: [Phase Name]
**Outcome:** [Success / Partial / Issue]
**Effort:** Actual: 7.5h vs. Estimated: 8h
**What Went Well:**
- [Notable success item 1]
- [Notable success item 2]

**What Was Harder Than Expected:**
- [Issue 1 and how it was resolved]
- [Issue 2 and how it was resolved]

**Key Learnings:**
- [Learning 1 that applies to other phases]
- [Learning 2 for future work]

**Blocked By / Blockers Created:**
- [None]

---

#### Phase 2: [Phase Name]
[Same format as Phase 1...]

---

#### Phase 3: [Phase Name]
[In progress or if completed...]

---
```

### Risk Assessment Update

Review original risks and update with actual impact:

```markdown
## Risk Assessment & Adjustments

### Original Risks (From Project Plan)

| Risk | Likelihood | Impact | Actual Impact | Status |
|------|-----------|--------|---------------|--------|
| [Risk 1] | Medium | High | Occurred, mitigated | ✓ Resolved |
| [Risk 2] | Low | High | Did not occur | ✓ Avoided |
| [Risk 3] | High | Medium | [TBD] | → Ongoing |

### New Risks Discovered

- **[New Risk 1]**
  - Likelihood: [Low/Medium/High]
  - Impact: [Low/Medium/High]
  - Example: [Specific incident]
  - Mitigation: [Strategy for remaining phases]

- **[New Risk 2]**
  - [Same format]

### Removed/Resolved Risks
- [Risk that no longer applies]
- [Risk that was mitigated]

---
```

### Technology/Tool Updates

Document any changes needed to remaining phases based on lessons learned:

```markdown
## Technology & Tool Feedback

### Tools That Worked Well
- [Tool 1]: [Why it was helpful]
- [Tool 2]: [Why it was helpful]

### Tools That Had Issues
- **[Tool with issue]**
  - Problem: [Specific issue encountered]
  - Impact: [How it affected work]
  - Workaround: [How we worked around it]
  - Mitigation for Phase 4+: [Updated approach]

### Environment Issues
- **[Environment issue]**
  - Problem: [What went wrong]
  - Impact: [How it slowed us down]
  - Fix for Phase 4+: [What to change]

### New Tool/Library Recommendations
- [Tool/Library]: [Why it would help for Phase 4+]
  - Benefit: [Specific improvement]
  - Effort to integrate: [Hours estimate]
  - Risk: [If any]

**System Prompt Updates Needed:**
- [ ] [Update needed in docs/system-prompts/]
- [ ] [Update needed]

---
```

### Dependency & Assumption Validation

Verify that assumptions in the plan still hold:

```markdown
## Assumption Validation

### Original Assumptions - Still Valid?

| Assumption | Status | Evidence | Adjustment |
|-----------|--------|----------|------------|
| [Assumption 1] | ✓ Valid | [Evidence] | None needed |
| [Assumption 2] | ⚠️ Questionable | [Evidence] | Adjust Phase X |
| [Assumption 3] | ✗ Invalid | [Evidence] | Re-plan Phase Y |

### External Dependencies - Still Accessible?

- [ ] [Resource 1]: ✓ Verified accessible
- [ ] [Resource 2]: ✓ Verified accessible
- [ ] [Resource 3]: ✗ No longer accessible - **BLOCKS Phase 4**

**Action:** [If dependency is missing or broken, document impact and mitigation]

---
```

### Adjustments to Remaining Phases

Plan updates needed based on lessons learned:

```markdown
## Adjustments to Remaining Phases

### Phase 4: [Name] - Adjustments Needed?

**Original Plan:** [Brief description]
**Adjustment:** [How it should change based on lessons learned]
**Rationale:** [Why change is needed]
**New Effort Estimate:** [Updated hours]
**Owner Approval:** [If significant change, note human approval]

Example:
```
**Original Plan:** Test with mock DynamoDB
**Adjustment:** Use DynamoDB Local instead (Phase 2 proved it's more reliable)
**Rationale:** Mock testing caught only 60% of issues; Local catches edge cases
**New Effort Estimate:** 12 hours → 10 hours (faster because better test quality)
**Owner Approval:** Not needed (minor optimization)
```

### Phase 5: [Name] - Adjustments Needed?
[Same format as Phase 4...]

### New Phase Needed?
- **[New Phase if discovered during execution]**
  - Reason: [Why it's needed]
  - Where in sequence: [Before/After Phase X]
  - Effort: [Hours estimate]
  - Approval needed: Yes/No

---
```

### Effort Forecast Update

Reforecast remaining work based on actual progress:

```markdown
## Effort Forecast Update

### Current Progress
- Completed: Phases 1-3 (22.5 actual hours vs 36 planned)
- Remaining: Phases 4-6
- Total Epic: [Original plan] vs [New forecast]

### Original Forecast
- Total effort: 50 hours
- Timeline: 2 weeks (assuming 3 hours/day availability)

### Updated Forecast
- Remaining effort: [New estimate] hours
- Adjustment: [Faster/slower than planned?]
- New timeline: [Revised estimate]
- Rationale: [Why estimate changed]

**Example:**
```
Original: 50 hours total
Completed so far: 22.5 hours (was planned as 36)
Remaining: 14 hours (was planned as 14)
Updated total: 36.5 hours (9 hours faster)
Reason: Phase 2 setup work made Phase 3 easier than expected

New Timeline: Complete by [date] instead of [original date]
```

---
```

### Overall Health Assessment

Brief summary of epic status:

```markdown
## Epic Health

**Overall Status:** 🟢 Green / 🟡 Yellow / 🔴 Red

**Summary:**
[1-2 sentences on current health]

**Continue As-Is?** Yes / No

**If No:**
- [ ] Needs scope reduction
- [ ] Needs timeline extension
- [ ] Needs team reassignment
- [ ] Needs external decision (human review)

**Approval Action Needed?**
- [ ] Human review and approval of adjustments
- [ ] Human decision on scope/timeline changes
- [ ] Proceed as planned

---
```

### Next Steps

Clear action items to proceed with remaining phases:

```markdown
## Next Steps

### Immediate (Before Phase 4 Starts)
1. [Action 1 - specific task]
2. [Action 2 - specific task]
3. [Update project plan with adjustments above]

### For Phase 4 Planning
- [Specific focus area]
- [Specific focus area]
- Reference updated plan: dev_notes/project_plans/YYYY-MM-DD_original_plan.md (updated)

### For Phase 5-6 Planning
- [Specific focus area based on Phase 4 expectations]

### Communication
- [ ] Notify stakeholders of timeline/scope changes
- [ ] Update backlog/roadmap if schedule changed
- [ ] Archive checkpoint document

---
```

### Lessons Learned for Future Epics

Insights that apply beyond this specific epic:

```markdown
## Lessons for Future Epics

### System Prompt / Process Improvements
**Finding:** [A pattern or improvement discovered]
**Applies To:** [What other epics would benefit?]
**Recommendation:** [Suggest update to docs/system-prompts/]
**Link to PR:** [If system prompt was already updated during Phase 1-3]

Example:
**Finding:** External resource accessibility wasn't validated before starting work
**Applies To:** Any epic depending on external code
**Recommendation:** Add "Verify external resources exist and are accessible" to planning-preflight.md checklist
**Link to PR:** docs/system-prompts/checklists/planning-preflight.md (created by pj-14)

### Tools/Library Recommendations
[Recommendations for standardizing or changing tools...]

### Testing Strategy Improvements
[How testing approach should evolve...]

### Other Insights
[Anything else important for future work...]

---
```

---

## How to Use This Template

### For Workers (During Implementation)

After completing a phase:

1. **Document your phase results** (what worked, what was hard)
2. **Note tool/environment issues** you encountered
3. **Record new risks** you discovered
4. **Suggest improvements** for remaining phases
5. **Include in change documentation** for that phase

Example change doc section:
```markdown
## Phase Feedback (for Phase Review Checkpoint)

### What Worked
- DynamoDB Local setup was straightforward
- Test factory pattern enabled fast test writing

### What Was Harder
- Debugging async errors took longer than expected
- Jest configuration for integration tests required 2 hours debugging

### Recommendation for Phase 4
- Consider adding DynamoDB Local troubleshooting guide to docs
- Phase 4 team should use async/await patterns we discovered
```

### For Planners (At Midpoint)

When a phase or 40-50% of work is done:

1. Collect feedback from all workers (change docs, Slack, conversations)
2. Compile this template with actual data
3. Update project plan with adjustments
4. Mark phases for any needed updates
5. Send to human for review if significant changes needed

### For Humans (Approval Gate)

When reviewing a phase checkpoint:

1. **Scan Epic Health section** first (status, any blockers?)
2. **Review Adjustments section** (are changes reasonable?)
3. **Check New Risks** (are they mitigated?)
4. **Approve or request changes** before proceeding

---

## Real Example: Mobile App Migration (pj-5)

### What Should Have Happened at 40% Completion

```markdown
# Phase Review Checkpoint: Mobile App Migration

Epic: pj-5
Completed: Phase 1 (pj-7) ✓
In Progress: Phase 2 (pj-8) - BLOCKED

## Risk Assessment Update

### New Risk Discovered
**Risk:** External app source not accessible
- Likelihood: High (confirmed)
- Impact: High (blocks Phase 2-4)
- Evidence: Attempted git clone, no access
- Mitigation: DEFER phases 2-4 until source acquired

## Adjustments to Remaining Phases

**Phase 2-4 Status:** DEFERRED
- Reason: Blocked by missing external app source
- New Timeline: Pending source availability
- Alternative: Complete Phase 1-6 independently

## Next Steps

1. Acquire external app source (in progress with external team)
2. Defer pj-8 status to "deferred" (not "open" blocking)
3. Mark pj-11, pj-12 as blocked by availability, not by previous phase
4. Continue with Phases 5-6 which are independent

---
```

This would have provided clear visibility and prevented assumptions.

---

## When to Create This

**Mandatory for:** Epics with 5+ phases
**Recommended for:** Any project lasting 2+ weeks
**Optional for:** Small projects (< 1 week, < 5 phases)

**Typical timing:** After 40-60% completion

---

## Integration with Workflow

- **Created during:** Worker's change documentation (feedback section)
- **Compiled by:** Planner at midpoint
- **Reviewed by:** Human approval gate
- **Referenced by:** Remaining phases in updated project plan
- **Archived:** dev_notes/checkpoints/ (future enhancement)

---

**Last Updated:** 2026-02-15
**Created by:** pj-14 - Phase 1: Workflow Improvements
**Status:** Ready for use
