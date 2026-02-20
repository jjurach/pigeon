# Template: Epic Suffix Phases (Self-Healing & Workflow Analysis)

**Purpose:** Standardize the final two phases of multi-phase epics (phases 15-16) that focus on documentation improvement and workflow analysis rather than feature implementation.

**When to use:**
- Phase 15: After all implementation phases complete (typically Phase N-1)
- Phase 16: After Phase 15 completion (final phase of epic)

**Responsibility:**
- **Worker:** Execute pre-flight checklist, perform analysis, update documentation
- **Planner:** Review and merge documentation changes
- **Human:** Approve epic closure

**Expected Outcome:**
- Updated system prompts and workflow documentation based on lessons learned
- Workflow improvement recommendations for future epics
- Formal epic closure with audit trail complete

---

## Pre-Flight Checklist (Required Before Starting)

**Complete this checklist before beginning Phase 15:**

### Documentation Inventory

- [ ] All change documents from implementation phases (1-14) exist and are readable
- [ ] All change documents follow the consistent structure (Summary, Changes Made, Testing, etc.)
- [ ] Change documents are stored in `dev_notes/changes/` with correct timestamp format
- [ ] All change documents have `Status: Completed` (not In Progress)

### Beads Verification

- [ ] Current bead (Phase 15 or 16) is marked as `in_progress`
- [ ] Epic approval bead is marked as `✓ closed`
- [ ] All implementation phase beads (1-14) are marked as `✓ closed`
- [ ] No open blockers on current phase bead

### Project Plan Alignment

- [ ] Original project plan exists in `dev_notes/project_plans/`
- [ ] Project plan scope vs. actual implementation documented
- [ ] Original success metrics available for reference
- [ ] Risk assessment from original plan reviewed

### Analysis Artifacts

- [ ] Workflow analysis document exists (if Phase 16 or completed by Phase 15)
- [ ] All Phase review checkpoints completed (Phases 5, 10, 15 if applicable)
- [ ] Lessons learned section in project plan has entries from all phases
- [ ] Change document "Workflow & Tooling Feedback" sections reviewed for patterns

### System Prompts Readiness

- [ ] System prompts accessible and writable in `docs/system-prompts/`
- [ ] Current versions of templates reviewed (`structure.md`, etc.)
- [ ] AGENTS.md available for reference
- [ ] Guidelines directory examined for existing patterns

### Git Status

- [ ] Working directory clean (all changes committed)
- [ ] Current branch is main or feature branch appropriate for epic work
- [ ] No stale branches or uncommitted files that would interfere
- [ ] Can run `bd sync` without conflicts

---

## Phase 15: Self-Healing System Prompts & Documentation

### Execution Steps

1. **Analyze Change Documents** (1-2 hours)
   - Read all change documents from implementation phases
   - Note recurring patterns, issues, and workarounds
   - Identify patterns that should be formalized (see Multi-Project Error Handling example)

2. **Review Lessons Learned** (1 hour)
   - Compile "Lessons Learned - Running Log" entries from all phases
   - Identify themes (common challenges, successful patterns, tooling issues)
   - Cross-reference with original project plan success metrics

3. **Update System Prompts** (1-2 hours)
   - Add new patterns to implementation reference (if applicable)
   - Update templates with discovered best practices
   - Improve checklists based on actual usage
   - Add new guidelines for recurring issues (e.g., multi-project error handling)

4. **Create Change Documentation** (30 min)
   - Document all system prompt updates in `dev_notes/changes/`
   - Explain reasoning for each change with phase references
   - Include before/after examples if significant

5. **Validate Changes** (30 min)
   ```bash
   # Ensure documentation integrity
   python3 docs/system-prompts/docscan.py

   # Check that AGENTS.md is valid
   python3 docs/system-prompts/bootstrap.py --analyze
   ```

### Success Criteria for Phase 15

- [ ] All lessons learned from implementation phases reviewed
- [ ] System prompts updated where applicable (minimum: 1 change)
- [ ] New guidelines or patterns documented (if discovered)
- [ ] Change documentation entry created and complete
- [ ] Documentation passes integrity checks (docscan.py)
- [ ] Git status clean and ready to commit
- [ ] Bead marked as `✓ closed`

---

## Phase 16: Workflow Improvement Analysis

### Execution Steps

1. **Collect All Change Documents** (30 min)
   - Create master list of all change documents from phases 1-16
   - Verify completeness and accessibility

2. **Perform Workflow Analysis** (2-3 hours)
   - Apply `docs/system-prompts/processes/workflow-improvement-analysis.md` process (if exists)
   - Or follow this structure:
     - **Categorization:** Group feedback by area (tools, process, documentation, structure)
     - **Pattern Recognition:** Identify recurring issues vs. one-time problems
     - **Quantification:** Count frequency and estimate impact
     - **Recommendations:** Propose specific, actionable improvements

3. **Create Analysis Document** (1-2 hours)
   - Write workflow improvement analysis in `dev_notes/analysis/`
   - Include executive summary, categorized findings, recommendations
   - Prioritize recommendations by effort vs. impact
   - Reference specific phases and change documents

4. **Update Project Plan** (30 min)
   - Add or update "Lessons Learned" synthesis section in original project plan
   - Capture high-level insights for future epics
   - Document successful patterns for reuse

5. **Create Change Documentation** (30 min)
   - Document the analysis process and findings in `dev_notes/changes/`
   - Include recommendations for system prompt improvements (Phase 15 follow-up)

### Success Criteria for Phase 16

- [ ] Workflow analysis document created and comprehensive
- [ ] All phases (1-16) covered in analysis
- [ ] Recommendations prioritized and estimated
- [ ] Original project plan updated with lessons learned
- [ ] Change documentation entry created
- [ ] Git status clean and ready to commit/push
- [ ] Bead marked as `✓ closed`

---

## Template: Epic Closure Checklist

After Phase 16 completion, verify epic is properly closed:

```markdown
## Epic Closure Verification: [Epic Name]

**Epic:** [Epic ID]
**Completion Date:** YYYY-MM-DD
**Total Duration:** XX weeks
**Total Effort:** XXX hours estimated, XXX actual

### Completion Checklist

#### Implementation (Phases 1-14)
- [ ] All deliverables completed and tested
- [ ] All phase beads marked as ✓ closed
- [ ] Code changes merged and committed
- [ ] Documentation complete and accurate

#### Self-Healing (Phase 15)
- [ ] System prompts updated based on lessons learned
- [ ] New guidelines/patterns documented
- [ ] Change documentation created
- [ ] Updates follow self-healing principle

#### Workflow Analysis (Phase 16)
- [ ] Workflow analysis completed
- [ ] Recommendations documented
- [ ] Original project plan updated
- [ ] Analysis findings integrated into system prompts

#### Final Verification
- [ ] All change documents exist and are complete (Phases 1-16)
- [ ] All tests pass
- [ ] Documentation builds without errors
- [ ] No broken links in updated files
- [ ] All code follows project standards
- [ ] Git history is clean and well-documented

#### Handoff
- [ ] Epic approval bead closed with completion note
- [ ] All beads synced to remote
- [ ] Changes pushed to main branch
- [ ] Epic documented as complete in project log
```

---

## Common Issues & Solutions

### Issue: Change Documents Missing or Incomplete

**Prevention:** Use the pre-flight checklist to verify all documents exist before starting Phase 15.

**Solution:** If a phase is missing documentation:
1. Review git history for what was actually implemented
2. Create retroactive change documentation (status: ad-hoc, mark as backfilled)
3. Include note explaining why documentation was created late

### Issue: Lessons Learned Not Captured Consistently

**Prevention:** Ensure each phase's change document includes "Workflow & Tooling Feedback" section (per template).

**Solution:** During Phase 15 analysis, extract lessons from change document summaries even if not explicitly in feedback section.

### Issue: System Prompts Already Updated in Different Phase

**Prevention:** Check system prompts early in Phase 15 to see if any changes already made.

**Solution:** Document what was already updated, focus Phase 15 efforts on additional gaps identified.

---

## References

- **Template Source:** Workflow analysis from Mellona-Pigeon epic (2026-02-20)
- **Related Process:** `docs/system-prompts/processes/workflow-improvement-analysis.md` (if exists)
- **Example Epic:** [dev_notes/project_plans/2026-02-18_03-50-15_mellona-pigeon-implementation.md](../../../dev_notes/project_plans/2026-02-18_03-50-15_mellona-pigeon-implementation.md)
