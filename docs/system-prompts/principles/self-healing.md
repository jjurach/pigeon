# Principle: Self-Healing System Prompts

**Purpose:** Ensure the system prompts and documentation evolve and improve automatically based on interaction and lessons learned during project execution.

---

## The Self-Healing Cycle

1. **Discovery:** During task execution or planning, an agent or human identifies a recurring problem, a better way of doing things, or general advice that applies beyond the current task.
2. **Generalization:** The insight is abstracted from the specific task into a general principle, process update, or template improvement.
3. **Application:** The agent immediately updates the relevant documentation in `docs/system-prompts/` rather than just noting it in a local project plan or change document.
4. **Reinforcement:** Future agents, following the updated system prompts, benefit from the previous insight without needing human intervention.

## Guidelines for Agents

- **Abstract General Advice:** If you find yourself giving or receiving advice that would be useful for all future projects or epics, move that advice to `docs/system-prompts/`.
- **Update Templates:** If a project plan or spec could be improved by a new section (e.g., "Lessons Learned"), update the standard template in `docs/system-prompts/templates/structure.md`.
- **Fix Process Gaps:** If a workflow (e.g., `plan-and-dispatch.md`) is missing a step that would prevent a common error, add it to the workflow document.
- **Proactive Improvement:** Do not wait for a human to ask for system prompt improvements. If an interaction results in a better understanding of how the project should be managed, document it in the system prompts.

## Lessons Learned in Project Plans

Every project plan should include a **Lessons Learned (Self-Healing)** section. 
- **Workers:** Update this section whenever you discover something that subsequent workers on the same plan should know.
- **Planners:** Before creating a new plan, review the lessons learned from recent similar plans and incorporate them into the new plan or the system prompts.

## Continuous Learning

The goal is to make the `docs/system-prompts/` directory a "living" repository of collective wisdom. Whenever a problem is fixed or a process is improved in a specific project instance, that improvement should be reflected back into the global instructions to prevent the same issue from occurring again.

---

**Last Updated:** 2026-02-15
**Status:** Active ✓
