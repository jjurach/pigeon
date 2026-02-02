# Agent Kernel: Core Workflow & Unbreakable Rules

## 1. The Core Workflow

**MANDATORY:** For any request that involves creating or modifying code or infrastructure, you MUST follow this workflow.

**Step A: Analyze the Request & Declare Intent**
1.  **Is it a simple question?** → Answer it directly.
2.  **Is it a Trivial Change?** → Make the change directly. No documentation required.
3.  **Is it just to fix tests or to fix broken usage?** → Make the change directly. No documentation required.
4.  **Is it a Research/Documentation Change?** → Make the change directly. No project plan required, but for non-trivial documentation work, create a timestamped change log in `dev_notes/changes/` marked with `Status: ad-hoc`.
5.  **Is it anything else?** → Announce you will create a **Project Plan**.

> **Trivial Change Definition:** Non-functional changes like fixing typos in comments or code formatting.
> **Research/Documentation Change:** Requests which culminate ONLY into writes to markdown documents in the root folder or in docs/ or in `dev_notes`.
> **Non-Trivial Documentation:** Creating new documentation files, substantial rewrites, or establishing new patterns/conventions. These skip project plans but still require change documentation for the audit trail.

**Step B: Process Spec File (If Required)**
- When a prompt involves planning, represent the planning in `dev_notes/specs`
- Create a summary of what the user is asking for in `dev_notes/specs/YYYY-MM-DD_HH-MM-SS_spec-description.md` (using the timestamp-based filename format)
- If the prompt involves processing user intentions from a un-timestamped file already in `dev_notes/specs`, then rename it to match the filename format based on the file's last modified time.
  - Add any additional context as developed over follow-up conversations about the spec.
- Spec files signify user intentions and goals, and are typically used to create or update project plans.

**Step C: Create a Project Plan (If Required)**
- Use the **Project Plan Structure** defined in `docs/system-prompts/templates/structure.md`.
- The plan must be detailed enough for another agent to execute.
- Save the plan to `dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_description.md`.

**Step D: AWAIT DEVELOPER APPROVAL**
- **NEVER EXECUTE A PLAN WITHOUT EXPLICIT APPROVAL.**
- Present the full Project Plan to the developer.
- "Approved", "proceed", "go ahead", "ok", or "yes" mean you can start.
- If the developer asks questions or provides feedback, answer them and then **return to a waiting state** until you receive a new, explicit approval.
- **If approval is ambiguous** (e.g., "maybe", "I think so", "probably"): Ask a follow-up clarifying question such as "I want to confirm: should I proceed with this Project Plan? Please respond with 'yes' or 'no'."

**Step E: Implement & Document Concurrently**
- Execute the approved plan step-by-step.
- After each logical change, create or update a **Change Documentation** entry in `dev_notes/changes/`. Use the structure from your project's templates documentation.

## 2. The Unbreakable Rules

1.  **Approval is Mandatory:** This is the most important rule. Never act on a Project Plan without explicit developer approval.
2.  **Quality is Mandatory:** You MUST follow the existing code patterns, conventions, style, and typing of the files you are editing. New code should look like the old code.
3.  **Uncertainty Requires a Full Stop:** If you encounter any error, are confused by a requirement, or are unsure how to proceed, you MUST **STOP** immediately. Document the issue and ask the developer for guidance. Do not try to solve novel problems alone.
4.  **File Naming is Mandatory:**
    - All Project Plans and Change Documentation MUST use the `YYYY-MM-DD_HH-MM-SS_description.md` filename format. (See your project's documentation for the directory location.)
    - All new documentation files in `docs/` MUST use `lowercase-kebab.md` naming convention.
5.  **Temporary Files:** NEVER use `/tmp` or system temporary directories for temporary files. Always create temporary files in the current working directory using the naming patterns `tmp-*` or `*.tmp` or `tmp/*`. These files should be cleaned up when no longer needed.
6.  **Slack Notification (If Supported):** Notify using the slack-notifications MCP service each time you commit to the local git repo. **Note:** This rule applies only to agents with MCP support.
