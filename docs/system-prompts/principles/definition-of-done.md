# Definition of Done: Universal Principles

**MANDATORY:** No task is considered "Done" until all applicable criteria in this document are met. This document serves as the **State Transition Logic** for the project's development workflow.

## 1. The "Plan vs. Reality" Protocol

*   **Plan Consistency:**
    *   **Insignificant Deviation:** If the implementation differs slightly from the plan (e.g., helper function name change, minor logic simplification) but the *outcome* is identical, note this in the `dev_notes/changes/` entry.
    *   **Significant Deviation:** If you discover a significantly better architectural approach or a blocker that requires changing other components: **STOP**. Abort the current execution path and ask the human developer for intervention. Do not unilaterally rewrite the architecture.
*   **Plan Status:**
    *   All Project Plans in `dev_notes/project_plans/` must have a `Status` header.
    *   **Draft:** Initial state when creating the plan.
    *   **Approved:** State after human developer gives explicit approval.
    *   **Completed:** You MUST update the header to `Status: Completed` before declaring the task finished.

## 2. Verification as Data

*   **Proof of Work:**
    *   In the `dev_notes/changes/` entry, the "Verification Results" section is **mandatory**.
    *   You MUST include the **exact command** used to verify the change.
    *   You MUST include a **snippet of the terminal output** (stdout/stderr) showing success.
    *   "It works" is not acceptable. Proof is required.
*   **Temporary Tests:**
    *   If you created a temporary test script (e.g., `scripts/verify_bug_123.py`):
        1.  Run it and capture the output.
        2.  Include the **full content of the script** in the `dev_notes/changes/` entry (inside a code block).
        3.  **Delete** the temporary script from the repository.

## 3. Codebase State Integrity

*   **Dependencies:**
    *   If any new library is imported, follow your language-specific Definition of Done for dependency management (see language-specific guidance below).
*   **Configuration Drift:**
    *   If you add or modify a configuration key (e.g., `api_timeout`, `max_retries`):
        1.  Update your project's implementation documentation (e.g., `docs/implementation-reference.md`, `docs/config.md`).
        2.  Update your project's configuration example/template file (e.g., `config.example.json`, `.env.example`, `config.sample.yaml`) to include the new key with a safe default or placeholder.
    *   **Secrets:** Never hardcode secrets. Ensure they are read from env vars or config, and documented in your configuration example/template file.

## 4. The Agent Handoff

*   **Known Issues:**
    *   If the implementation is functional but has caveats (e.g., "slow on first run," "edge case X not handled"), you MUST add a **"Known Issues"** section to the `dev_notes/changes/` entry.
*   **Context Forwarding:**
    *   When starting a new task, agents are instructed to read the previous 2 change summaries to check for "Known Issues" that might impact their work.

## Checklist for "Done"

- [ ] `Status: Completed` set in Project Plan.
- [ ] `dev_notes/changes/` entry created.
- [ ] Verification command and output included in change log.
- [ ] Temporary test scripts content saved to log and file deleted.
- [ ] Dependencies updated (language-specific; see language sections below).
- [ ] Configuration example file updated (if applicable).
- [ ] `docs/` updated for new config/features.
- [ ] "Known Issues" documented.

---

## Language-Specific Requirements

### Python Projects

See `docs/system-prompts/languages/python/definition-of-done.md` for Python-specific requirements including:
- pytest test framework setup
- `requirements.txt` and `pyproject.toml` management
- Type hints and docstrings
- Test coverage requirements
