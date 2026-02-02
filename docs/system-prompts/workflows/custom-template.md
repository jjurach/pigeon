# Custom Workflow Template

**Use this template to create custom workflows for your project.**

This document shows the structure and sections that make a workflow compatible with the Agent Kernel and bootstrap.py system.

---

## Overview

A custom workflow is a set of instructions that govern how AI agents approach development tasks in your project. Workflows can range from lightweight (minimal structure) to heavyweight (comprehensive documentation and verification requirements).

When you create a custom workflow:

1. Follow this template structure
2. Register it with bootstrap.py (see "Integration" section below)
3. Project developers can enable/disable it via bootstrap.py arguments
4. The workflow is injected into AGENTS.md when enabled

---

## Template Structure

### 1. Title and Purpose

```markdown
# [Your Workflow Name]

**Purpose:** [1-2 sentence description of what this workflow is for]

**Best for:** [Types of projects that should use this workflow]

**Not recommended for:** [Types that shouldn't use this workflow]
```

### 2. Overview Section

Explain in plain language:
- What this workflow emphasizes (documentation? speed? testing? collaboration?)
- The core philosophy
- When/why to use it

### 3. Core Steps or Principles

Define the main workflow steps:

```markdown
## The Workflow

### Step 1: [First Phase]
- Substep 1a
- Substep 1b

### Step 2: [Second Phase]
- [Details]

### Step 3: [etc]
```

OR for principle-based workflows:

```markdown
## Core Principles

1. **Principle Name** - [explanation]
2. **Principle Name** - [explanation]
3. **Principle Name** - [explanation]
```

### 4. Rules and Constraints

List mandatory rules for your workflow:

```markdown
## Mandatory Rules

1. **Rule Name:** [explanation]
2. **Rule Name:** [explanation]
3. **Rule Name:** [explanation]
```

### 5. Definition of Done

What does "done" mean in this workflow?

```markdown
## Definition of Done

### Checklist

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3
```

### 6. Documentation & Resources

Link to related documents:

```markdown
## Resources

- `docs/file1.md` - [Brief description]
- `docs/file2.md` - [Brief description]
```

### 7. Example or Walkthrough (optional)

Show how the workflow works in practice:

```markdown
## Example: [Feature Name]

[Step-by-step walkthrough]
```

### 8. Further Reading (optional)

```markdown
## Further Reading

- [Link/reference]
- [Link/reference]
```

---

## Complete Example: "Rapid Iteration" Workflow

Here's a minimal custom workflow as reference:

```markdown
# Rapid Iteration Workflow

**Purpose:** Fast-moving projects where documented development is less important than velocity.

**Best for:** Startups, prototypes, internal tools, research projects

**Not recommended for:** Safety-critical systems, multi-team projects, public APIs

---

## The Workflow

### Step 1: Understand Request
- Ask clarifying questions if unclear
- Proceed directly if clear

### Step 2: Implement
- Make changes as efficiently as possible
- Write tests if time permits
- Use existing patterns from codebase

### Step 3: Verify
- Run tests (if they exist)
- Test manually if needed
- Get developer feedback

### Step 4: Iterate
- Adjust based on feedback
- Repeat Steps 2-3 until approved

---

## Mandatory Rules

1. **Code Quality:** Follow existing code patterns and style
2. **Testing:** No breaking changes to existing tests
3. **Documentation:** Update README/inline comments if APIs change
4. **No Secrets:** Never hardcode credentials or API keys
5. **Uncertainty Stops Work:** Ask for guidance if confused

---

## Definition of Done

- [ ] Changes implement the requested feature
- [ ] Existing tests still pass
- [ ] Code follows project style
- [ ] Documentation updated (if needed)
- [ ] Developer has reviewed and approved

---

## Further Reading

- `docs/definition-of-done.md` - Quality standards
- `docs/architecture.md` - How to modify system architecture
```

---

## Integration with Bootstrap.py

### Making Your Workflow Discoverable

Once you've created your custom workflow file (e.g., `docs/system-prompts/workflows/my-workflow.md`), register it in bootstrap.py:

1. Open `docs/system-prompts/bootstrap.py`
2. In the `load_system_prompt()` method, add your workflow to the section map:

```python
section_map = {
    "CORE-WORKFLOW": "workflow/core.md",
    "PRINCIPLES": "principles/definition-of-done.md",
    "PYTHON-DOD": f"languages/python/definition-of-done.md",
    "MY-CUSTOM-WORKFLOW": "workflows/my-workflow.md",  # Add your workflow
}
```

3. Add command-line argument support (in the main() function):

```python
parser.add_argument(
    "--enable-my-workflow",
    action="store_true",
    help="Enable the My Workflow workflow",
)
parser.add_argument(
    "--disable-my-workflow",
    action="store_true",
    help="Disable the My Workflow workflow",
)
```

4. Test the integration:

```bash
python3 docs/system-prompts/bootstrap.py --analyze-workflow
python3 docs/system-prompts/bootstrap.py --enable-my-workflow --commit
```

### Section Names

When creating your workflow file, choose a clear section name for use in AGENTS.md:
- Use uppercase with hyphens (e.g., `MY-CUSTOM-WORKFLOW`, `RAPID-ITERATION`, `ENTERPRISE-PROCESS`)
- This becomes the HTML section marker: `<!-- SECTION: MY-CUSTOM-WORKFLOW -->`

---

## Design Considerations

### 1. Scope

- **Small workflows** (< 1000 lines): Good for lightweight projects
- **Medium workflows** (1000-3000 lines): Suitable for most teams
- **Large workflows** (> 3000 lines): Consider breaking into multiple sections

### 2. Audience

Who will read this workflow?
- Individual developers? Keep it concise and practical
- AI agents? Include explicit step-by-step instructions
- Teams? Explain rationale behind rules
- Enterprise? Include governance and compliance notes

### 3. Compatibility

Your workflow should:
- Explain when to use it (vs. other workflows)
- Provide clear decision trees
- Include examples
- Have a Definition of Done section
- Link to related documentation

### 4. Extensibility

Plan for future changes:
- Use version markers if you plan major revisions
- Document known limitations
- Provide feedback mechanisms
- Consider how new team members will learn it

---

## Best Practices

1. **Start Simple** - Begin with core principles, add details later
2. **Use Examples** - Show how the workflow works in practice
3. **Make it Discoverable** - Link from main documentation
4. **Get Feedback** - Have team members review before committing
5. **Document Decision Rationale** - Explain the "why" behind rules
6. **Keep it Updatable** - Use sections that can be easily changed
7. **Link to Tools** - Show how bootstrap.py enables your workflow
8. **Consider Different Learning Styles** - Include diagrams, examples, text

---

## Common Workflow Patterns

### Documentation-Heavy Pattern
- Detailed specs and plans required
- Comprehensive change documentation
- Examples: logs-first workflow

### Speed-Focused Pattern
- Minimal documentation upfront
- Focus on rapid iteration
- Example: Rapid Iteration workflow above

### Process-Heavy Pattern
- Review steps, approval gates, compliance
- Detailed rollback procedures
- Examples: Enterprise deployments

### Minimal Pattern
- Only documentation when necessary
- Trust developer judgment
- Maximum flexibility

---

## Publishing Your Workflow

Once your workflow is ready:

1. Save to `docs/system-prompts/workflows/your-workflow.md`
2. Register in bootstrap.py
3. Add to `docs/system-prompts/workflows/README.md` directory listing
4. Document in `docs/workflows.md` (main user guide)
5. Consider creating a quick-start guide for new projects

---

## Questions?

- How to customize this template? → Adapt any section to your needs
- How to handle conflicts between workflows? → bootstrap.py supports enabling/disabling on a per-workflow basis
- How to share workflows between projects? → Copy the .md file and register in each project's bootstrap.py
- How to deprecate a workflow? → Mark as "legacy" and provide migration path to newer workflow

---

## Example Files in This Project

- `docs/system-prompts/workflows/logs-first.md` - Comprehensive documentation-based workflow
- `docs/templates.md` - Document templates for this workflow
- `docs/definition-of-done.md` - Quality standards
