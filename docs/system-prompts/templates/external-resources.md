# Template: External Resources Guide

**Purpose:** Document how to acquire, verify, and handle external resources required by a project.

**When to use:** When creating a project plan that depends on external code, data, APIs, or services.

**Where to place:** Reference from project plan as: `See: docs/system-prompts/templates/external-resources.md`

---

## Copy-paste template for project plans

```markdown
## External Resources

### Resource Name: [e.g., "External App Source Code"]

**Location:** [e.g., "external/orig/apps/mobile/"]

**Status:** [Current state - choose one]
- Available (verified access)
- Not available (needs acquisition)
- Partially available (some components missing)

**Description:**
[What is this resource? What does it contain? Why do we need it?]

Example:
> Mobile app source code for the scorecard application. Contains React Native components, assets, Android and iOS configuration. Needed for Phase 2 (code migration).

### Verification Checklist

**Current Status:** [date and who verified]

- [ ] Resource exists at documented location
- [ ] Can access it with current credentials/permissions
- [ ] Has expected structure/contents
- [ ] Files are complete (not stubs or empty)
- [ ] No blocker issues found
- [ ] All team members can access it

**If Any Checked Failed:** Provide details:
```
Example:
- [ ] Mobile app source: NOT FOUND
  - Attempted: git clone [url]
  - Error: Repository private, requires separate access
  - Resolution pending: Requesting access from external team
```

### Access Instructions

**For Team Members:**

1. [Step 1 to get access/download]
2. [Step 2]
3. [Verification step - how to confirm it works]

Example:
```
1. Request credentials from [Contact Name] in Slack: #external-resources
2. Clone repo: git clone [url] into external/orig/
3. Verify: ls external/orig/apps/mobile/src/ (should show source files)
```

**Prerequisites:**
- [Tool 1] installed (e.g., Git, AWS CLI)
- [Authentication] configured (e.g., GitHub PAT, AWS credentials)
- [Environment] setup (e.g., Node 18.x, Python 3.10+)

**Troubleshooting:**
- **Error: "Permission denied"**
  - Cause: GitHub credentials not configured
  - Fix: Run `gh auth login` and authenticate with your GitHub account

- **Error: "Repository not found"**
  - Cause: Resource URL changed or repo deleted
  - Fix: Verify URL in this guide, contact [team/person] if URL incorrect

- [Add more common issues and fixes]

### Acquisition Path (If Not Currently Available)

**Current Status:** [Date and context of why resource is not available]

**How to Acquire:**

1. [Contact/process to get resource]
2. [Setup/import steps]
3. [Verification]
4. [Where to place in repo]

Example:
```
Status: External team has source but hasn't shared yet
Process:
1. Contact: Sarah Chen (sarah@external.com)
2. Request: "Can we get read access to scorecard app source?"
3. Expected: Archive or git repo
4. Setup: Unzip to external/orig/apps/mobile/ or git clone
5. Verify: Run build step to confirm compilation works
```

**Timeline:** [Expected availability, SLA, or dependencies]

Example:
> Expected by: 2026-02-20
> Contact confirmed: Resource shared within 2-3 business days
> Dependency: No other blockers

**Fallback Plan:** [What to do if resource never becomes available]

Example:
> If not available by 2026-02-22:
> - Defer Phases 2-4 to future epic
> - Proceed with Phase 1 (dependency alignment)
> - Document lessons learned for next attempt
> - Consider: Mock app components, use samples from docs, etc.

### Dependency Impact

**Blocked Work:**
- [Phase/Bead that requires this resource]
- [Phase/Bead that requires this resource]
- etc.

Example:
```
- pj-8 (Phase 2: Source Code Migration) - BLOCKED
- pj-11 (Phase 3: Integration & Feature Parity) - BLOCKED
- pj-12 (Phase 4: E2E Testing) - BLOCKED
```

**Work That Can Proceed:** [Phases that don't depend on this]

Example:
```
- pj-7 (Phase 1: Dependency Alignment) - Can proceed independently
- pj-10 (Self-Healing Prompts) - Can proceed after Phase 1
```

**Mitigation:**
[Strategy if resource remains unavailable. Defer? Mock? Alternative?]

Example:
> Mitigation: Defer dependent phases if source not available by 2026-02-22.
> Phase 1 (pj-7) can be completed successfully without source.
> Update planning summary and beads to mark pj-8/11/12 as "deferred" with clear remediation path.

---

### Resource Requirements Reference

**For Planning Teams:** Use this section when creating the resource section in your project plan.

**Dependencies:**
- [What must already exist for this resource to work?]
- [Environment setup needed?]
- [Conflicting tools/versions?]

Example:
```
- Node.js 16.x or higher (react-native requirement)
- npm 8+
- iOS 13+ SDK (for iOS build)
- Android SDK 30+ (for Android build)
```

**Alternatives/Fallbacks:**
- [Can we use a different resource?]
- [Can we mock/stub this resource?]
- [What happens if we skip this phase?]

Example:
```
- If source unavailable: Use sample components from official React Native docs
- If full source unavailable: Use portions from public repos
- Defer: Complete other phases first, return to this when source available
```

**Last Known Good State:**
- Date: [When was this resource last verified?]
- Location: [Where was it verified?]
- Who: [Who verified it?]
- Status: [Accessible? Complete? Any issues?]

Example:
```
Date: 2026-02-15 14:30 UTC
Who: Claude Haiku 4.5
Location: checked git clone, file system access
Status: Available, full source present, no access issues
```

---

## How to Use This Template

1. **In Project Plan:** Reference this template when describing external resources
   ```markdown
   External Dependencies:

   See: docs/system-prompts/templates/external-resources.md

   ### Mobile App Source Code
   - Location: external/orig/apps/mobile/
   - Status: [checked at plan creation time]
   - Verification: [Document findings]
   ```

2. **In Planning Checklist:** Verify before approval using the checklist in [planning-preflight.md](../checklists/planning-preflight.md)

3. **In Implementation:** Workers refer to this when starting work
   ```bash
   # Workers see external resource guide in plan
   cat dev_notes/project_plans/YYYY-MM-DD_name.md | grep -A 50 "External Resources"
   ```

4. **During Approval:** Humans check that external dependencies are realistic
   ```
   ✓ Is the resource really accessible now?
   ✓ Is the acquisition path clear if not?
   ✓ Are fallback/deferral plans documented?
   ```

---

## Real Example: Mobile App Migration (pj-5)

### What Went Wrong ❌

```
Plan: Port source code from external app
Status at Approval: Assumed availability, not verified
Result: Phase 2 (pj-8) completely blocked
Impact: Blocked entire epic for weeks
```

### What Should Have Happened ✅

```
External Resource: Mobile App Source Code

Verification Checklist:
- [ ] Repository accessible (FAILED - access needed)
- [ ] Required files present (UNKNOWN)
- [ ] Build configuration included (UNKNOWN)

Acquisition Path:
Contact: [External team]
Status: Not yet received
Timeline: Pending confirmation
Risk: High - no confirmed ETA

Fallback Plan:
IF not available by [date]:
  - Defer Phase 2 (pj-8) explicitly
  - Mark pj-11, pj-12 as blocked by availability
  - Proceed with Phase 1 independently
  - Document remediation for next attempt

Dependency Map:
✓ pj-7 (Phase 1) - Independent, can proceed
✗ pj-8 (Phase 2) - Blocked by source availability
✗ pj-11 (Phase 3) - Blocked by pj-8
✗ pj-12 (Phase 4) - Blocked by pj-11
```

This would have prevented the surprise mid-execution and allowed proper planning.

---

## Integration

- **Parent:** [planning-preflight.md](../checklists/planning-preflight.md) Section 1
- **Used in:** Project plans when external resources needed
- **Reviewed by:** Human approver during approval gate
- **Updated during:** Implementation if resource status changes

---

**Last Updated:** 2026-02-15
**Created by:** pj-14 - Phase 1: Workflow Improvements
**Status:** Ready for use
