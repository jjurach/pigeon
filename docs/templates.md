# Planning Document Templates

This document provides templates for planning documents used in the Pigeon project.

## Agent Kernel Templates

The project follows the Agent Kernel template system. For complete template documentation, see:

- **[Template Structure Guide](system-prompts/templates/structure.md)** - Standard templates for project plans, architecture decisions, and investigation reports

## Project-Specific Conventions

### Development Notes Directory

Development notes and session transcripts are stored in `dev_notes/` using the format:

```
dev_notes/subdir/YYYY-MM-DD_HH-MM-SS_description.md
```

### Planning Documents

When creating project plans, follow the structure from the Agent Kernel:

1. **Executive Summary** - Overview and objectives
2. **Issues Summary** - Problems being addressed
3. **Implementation Phases** - Step-by-step breakdown
4. **Critical Files Summary** - Files to create, modify, or delete
5. **Verification Steps** - Testing and validation
6. **Success Criteria** - Measurable outcomes
7. **Risk Mitigation** - Known risks and mitigation strategies

## Project-Specific Document Types

### Feature Implementation Plan

Used for adding new features to Pigeon.

**Template:**

```markdown
# Feature: [Feature Name]

**Status:** Draft
**Date:** YYYY-MM-DD
**Agent:** [Your Name]

## Executive Summary

[1-2 sentence description of what will be added]

## Motivation

[Why this feature is needed]

## Issues Being Addressed

- Issue 1: [Description]
- Issue 2: [Description]

## Implementation Phases

### Phase 1: [Setup/Investigation]
- [Step 1]
- [Step 2]

### Phase 2: [Implementation]
- [Step 1]
- [Step 2]

### Phase 3: [Testing and Documentation]
- [Step 1]
- [Step 2]

## Critical Files Summary

**New Files:**
- `src/pigeon/[module].py` - [Description]

**Modified Files:**
- `src/pigeon/poller.py` - Add [functionality]
- `docs/architecture.md` - Update architecture

**Deleted Files:**
- None

## Verification Steps

```bash
# Run tests
pytest

# Run specific feature tests
pytest tests/test_[feature].py -v

# Manual verification
pigeon [command] [args]
```

## Success Criteria

- [ ] Feature works as specified
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No regression in existing functionality

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Feature conflicts with existing code | Review architecture first |
| Tests fail in CI | Run locally with full test suite |
```

## Debugging/Investigation Template

Used when debugging issues or investigating root causes.

**Template:**

```markdown
# Investigation: [Issue Description]

**Status:** Draft
**Date:** YYYY-MM-DD
**Agent:** [Your Name]

## Problem Statement

[Clear description of the issue]

## Symptoms

- Symptom 1
- Symptom 2

## Investigation Steps

1. [Step 1] - [Expected result]
2. [Step 2] - [Expected result]
3. [Step 3] - [Expected result]

## Findings

- Finding 1: [Details]
- Finding 2: [Details]

## Root Cause

[Analysis of root cause]

## Solution

[Proposed fix]

## Verification

Steps to verify the fix works:

```bash
[Commands to verify]
```

## See Also

- Related issue: [Link]
- Related docs: [Link]
```

## Architecture Decision Record

Used when making significant architectural decisions.

**Template:**

```markdown
# ADR: [Title]

**Decision:** [Decision being made]
**Status:** Draft / Approved
**Date:** YYYY-MM-DD

## Context

[What led to this decision]

## Alternatives Considered

### Alternative 1: [Name]
- Pros: [Benefits]
- Cons: [Drawbacks]

### Alternative 2: [Name]
- Pros: [Benefits]
- Cons: [Drawbacks]

## Decision

[Selected alternative and why]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Downside 1]
- [Downside 2]

## Implementation Notes

[How to implement this decision]

## See Also

- Related docs: [Links]
```

## Meeting Notes / Session Plan

Used for planning sessions and documenting outcomes.

**Template:**

```markdown
# Session: [Date] - [Topic]

**Status:** Draft / Completed
**Date:** YYYY-MM-DD
**Participants:** [Names]

## Objectives

- [ ] Objective 1
- [ ] Objective 2

## Context

[What's happening and why]

## Discussion

### Topic 1: [Name]
- Question: [Ask]
- Conclusion: [Answer]

### Topic 2: [Name]
- Question: [Ask]
- Conclusion: [Answer]

## Decisions Made

1. Decision 1: [What and why]
2. Decision 2: [What and why]

## Action Items

- [ ] Action 1 - Owner: [Name]
- [ ] Action 2 - Owner: [Name]

## Next Steps

[What happens next]

## See Also

- Related issue: [Link]
- Related docs: [Link]
```

## Process Documentation

Used to document new processes or procedures.

**Template:**

```markdown
# Process: [Process Name]

**Purpose:** [Why this process exists]
**Owner:** [Who maintains this]
**Last Updated:** YYYY-MM-DD

## Overview

[Brief description of the process]

## Prerequisites

- [Requirement 1]
- [Requirement 2]

## Steps

1. **Step 1: [Name]**
   - [Sub-step 1]
   - [Sub-step 2]
   - Expected result: [What should happen]

2. **Step 2: [Name]**
   - [Sub-step 1]
   - [Sub-step 2]
   - Expected result: [What should happen]

## Verification

```bash
# Command to verify the process
[Commands]
```

## Troubleshooting

### Issue: [Problem]
- Cause: [What causes this]
- Solution: [How to fix]

### Issue: [Problem]
- Cause: [What causes this]
- Solution: [How to fix]

## See Also

- Related docs: [Links]
```

## Code Review Checklist

Used for reviewing pull requests and changes.

**Template:**

```markdown
# Code Review: [PR Title]

**Date:** YYYY-MM-DD
**Reviewer:** [Your Name]
**Status:** Approved / Requested Changes

## Changes Summary

[Brief summary of what changed]

## Review Checklist

### Functionality
- [ ] Changes work as intended
- [ ] No regression in existing features
- [ ] Handles edge cases

### Code Quality
- [ ] Code is readable
- [ ] Functions are documented
- [ ] No code duplication

### Testing
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Coverage is adequate

### Documentation
- [ ] README updated if needed
- [ ] Architecture docs updated if needed
- [ ] Comments added where complex

### Process
- [ ] Commit messages are clear
- [ ] Co-Authored-By trailer included
- [ ] Follows Definition of Done

## Comments

[Detailed feedback and suggestions]

## Approval

- [ ] Approved as-is
- [ ] Approved with minor comments
- [ ] Requested changes needed

## See Also

- [Definition of Done](definition-of-done.md) - Quality standards
- [Implementation Reference](implementation-reference.md) - Code patterns
```

## File Naming Convention

All development notes should use the timestamp format:

```
YYYY-MM-DD_HH-MM-SS_description.md
```

**Examples:**

```
2026-02-01_14-30-00_feature-plan-oauth-caching.md
2026-02-01_15-45-23_debugging-folder-id-resolution.md
2026-02-01_16-20-15_session-notes-polish.md
```

**Advantages:**
- Chronologically sortable
- Unique per second
- Readable date/time
- Easy to scan directory

## See Also

- [AGENTS.md](../AGENTS.md) - Core workflow for AI agents
- [Definition of Done](definition-of-done.md) - Quality standards
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Implementation patterns
- [Agent Kernel Templates](system-prompts/templates/structure.md) - Complete template documentation

---

Last Updated: 2026-02-01
