# Project Documentation Templates

This directory contains templates for standard project documentation that supports the Agent Kernel workflow.

## Contents

- **`structure.md`** - Formalized templates for:
  - Spec Files (user intentions and requirements)
  - Project Plans (implementation strategies)
  - Change Documentation (proof of work)
  - Best practices and state transition rules

## Usage

When adopting the Agent Kernel in your project:

1. Read `structure.md` to understand the three core document types
2. Create new specs, plans, and change documentation following these templates
3. Store them in your chosen planning directory (e.g., `dev_notes/`, `docs/planning/`, `.ai-plans/`)

## Key Principles

- **Spec Files** capture "what the user wants"
- **Project Plans** describe "how we'll build it"
- **Change Documentation** proves "what we actually built"

Together, these form an audit trail showing intent → design → execution.

## Customization

The templates use placeholders (e.g., `YYYY-MM-DD_HH-MM-SS`) for dates and structure. Your project may customize:
- Directory location (see `workflow/core.md` for guidance)
- Status values (if appropriate for your project)
- Verification procedures (adapt to your tech stack)

But do NOT customize the core workflow structure or filename format—these enable consistency across tools and agents.
