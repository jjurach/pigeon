# Trigger Phrases: Invoke iterate-next-bead.md Process

**Purpose:** Document all trigger phrases that invoke the `iterate-next-bead.md` workflow for bead-based task execution.

**When you see ANY of these phrases from the user, apply the `iterate-next-bead.md` process immediately.**

---

## Exact Match Triggers

These phrases trigger the full workflow:

- `apply iterate-next-bead.md process`
- `apply iterate-next-bead process`
- `use iterate-next-bead.md`
- `iterate-next-bead.md`

---

## Pattern Triggers

These patterns also trigger the workflow:

### Pattern: "iterate [the] next bead"
Examples:
- `iterate the next bead`
- `iterate next bead`
- `iterate next ready bead`

### Pattern: "iterate bead"
Examples:
- `iterate bead {id}`
- `iterate {bead_id}`
- `start iterating beads`

### Pattern: "process bead" / "claim bead"
Examples:
- `process the next bead`
- `claim and process the next bead`
- `work on the next ready bead`

### Pattern: "continue with beads" / "next bead"
Examples:
- `continue with beads`
- `move to next bead`
- `work on next ready bead`
- `what's the next bead?` (if followed by approval)

---

## Command-Style Triggers

These command-like requests trigger the workflow:

- `bd ready` (if followed by implicit "apply the process")
- `next bead` (in command context)
- `iterate` (alone, in bead context)
- `claim and implement` (implies iterate-next-bead workflow)

---

## When in Doubt: Ask for Clarification

If the user's phrasing is ambiguous:
1. Check if they're clearly requesting bead work
2. Check the context (are beads ready? are we in a bead session?)
3. If still unclear, confirm: "Should I apply the iterate-next-bead.md process?"

---

## The Full Process Flow

When triggered, follow this in sequence:

1. **Phase 1-3:** Environmental assessment and find ready bead
2. **Phase 4:** Claim the bead (`bd update {id} --status=in_progress`)
3. **Phase 5:** Determine execution type (interactive vs. non-interactive)
4. **Phase 5.4:** ⭐ Pre-Implementation Completeness Check (NEW - CRITICAL)
   - Verify if work is already complete
   - If YES → Skip to Phase 7
   - If NO → Proceed to Phase 6
5. **Phase 6:** Implement the gap (if needed)
6. **Phase 7:** Close the bead and commit changes
7. **Phase 8:** Loop (check for more work) or halt

**Reference:** `docs/system-prompts/processes/iterate-next-bead.md`

---

## Key Points for Agents

⭐ **Phase 5.4 is the most important change**
- Always check if work is already done BEFORE implementing
- Don't re-implement working code
- Close immediately if criteria already met

✅ **What triggers this process:**
- Any phrase mentioning "iterate" + "bead"
- Any phrase mentioning "bead" + "next/ready"
- The exact phrase "apply iterate-next-bead.md process"
- Related commands like "process next bead", "claim bead"

❌ **What does NOT trigger this:**
- "What beads are ready?" (just answer the question)
- "Show me the bead details" (just show details)
- "Check bead status" (just check status)
- Research or investigation requests unrelated to claiming/implementing

---

## Examples of Triggered Requests

### Clear Triggers ✅

User: `"iterate the next bead"`
→ **Apply iterate-next-bead.md process**

User: `"apply iterate-next-bead.md"`
→ **Apply iterate-next-bead.md process**

User: `"claim the next ready bead and implement it"`
→ **Apply iterate-next-bead.md process**

User: `"work on the next bead"`
→ **Apply iterate-next-bead.md process**

User: `"process bead proj-07r"`
→ **Apply iterate-next-bead.md process (with specific bead)**

### Ambiguous Cases ⚠️

User: `"are there any ready beads?"`
→ Run `bd ready` and report, but DON'T auto-trigger process
→ Unless user follows up with "iterate them"

User: `"what's next?"`
→ In bead context, ask: "Should I apply iterate-next-bead.md to the next ready bead?"

User: `"continue"`
→ In bead session, likely means continue with beads (apply process)
→ In other context, ask for clarification

---

## Agent Implementation Notes

### For Claude Code

When you see a trigger phrase:

1. Recognize it explicitly:
   ```
   "User is asking to apply iterate-next-bead.md process"
   ```

2. Follow the 8-phase workflow from `docs/system-prompts/processes/iterate-next-bead.md`

3. Track which phase you're in:
   ```
   [Phase 1] Environmental assessment...
   [Phase 2] Health check...
   [Phase 5.4] Completeness check - Work already done? YES → Phase 7
   ```

4. At Phase 8, decide: continue to Phase 3 or halt

### For Other Agents

Same workflow. Key differences:
- Commands may vary (e.g., Gemini uses different CLI tools)
- But the 8-phase structure is universal
- Phase 5.4 completeness check is CRITICAL and applies to all agents

---

## Integration with Other Processes

**iterate-next-bead.md is separate from:**
- `close-project.md` (used within Phase 7 of iterate-next-bead)
- `logs-first.md` (for planning, not bead execution)
- `plan-and-dispatch.md` (for creating beads, not executing them)

**iterate-next-bead.md is the EXECUTION process for beads created by plan-and-dispatch.md**

---

## Last Updated

2026-02-22 - Initial version with full trigger phrase documentation and Phase 5.4 emphasis
