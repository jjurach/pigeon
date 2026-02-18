# Workflows

This directory contains Agent Kernel workflows—reusable sets of instructions that govern how AI agents approach development tasks.

---

## What is a Workflow?

A workflow defines:
- **How to approach tasks** (steps, phases, decision points)
- **What's mandatory** (rules and constraints)
- **When you're done** (Definition of Done checklist)
- **What to document** (specs, plans, changes)

Workflows enable projects to adapt the Agent Kernel to their specific needs without losing the core benefits of consistency and accountability.

---

## Available Workflows

### logs-first.md

**For:** Small, iterative projects valuing detailed documentation and audit trails

**Approach:**
1. User request → Spec File (document intentions)
2. Spec → Project Plan (design strategy, await approval)
3. Approval → Implementation + Change Documentation (prove what was built)

**Best for:** Teams < 10, active projects, internal tools, startups

**Key features:**
- Complete audit trail (intention → design → implementation)
- Multi-step approval process
- Comprehensive verification requirements
- Emphasis on documentation-as-you-go

**Setup:**
```bash
python3 docs/system-prompts/bootstrap.py --enable-logs-first --commit
```

---

### custom-template.md

**For:** Projects creating their own custom workflows

**What it provides:**
- Template structure for creating workflows
- Integration guide with bootstrap.py
- Best practices and design considerations
- Examples of different workflow patterns

**How to use:**
1. Copy and adapt the template for your project needs
2. Follow the integration steps to register with bootstrap.py
3. Enable/disable via bootstrap.py command-line arguments

---

## How to Enable/Disable Workflows

### Check Recommendation

```bash
python3 docs/system-prompts/bootstrap.py --analyze-workflow
```

Shows:
- Recommended workflow for your project
- Current workflow state
- Available workflows

### Enable a Workflow

```bash
python3 docs/system-prompts/bootstrap.py --enable-logs-first --commit
```

This injects the workflow content into AGENTS.md.

### Disable a Workflow

```bash
python3 docs/system-prompts/bootstrap.py --disable-logs-first --commit
```

This removes the workflow content from AGENTS.md.

---

## Creating a Custom Workflow

1. **Read** `custom-template.md` for structure and best practices
2. **Create** your workflow file: `docs/system-prompts/workflows/my-workflow.md`
3. **Register** in `bootstrap.py` by adding to `section_map` and command-line args
4. **Enable** with `--enable-my-workflow --commit`
5. **Update** `README.md` (this file) to document your workflow

---

## Workflow Design Considerations

### Who Should Use Which Workflow?

| Project Type | Recommended | Why |
|---|---|---|
| Small team, active | logs-first | Complete audit trail, detailed planning helps coordination |
| Large enterprise | Custom (minimal) | Reduce overhead, maximum flexibility |
| Startup/MVP | Custom (rapid) | Speed over documentation |
| Research/experimental | Custom (exploration) | Different success criteria |
| Safety-critical | Custom (heavy) | Rigorous approval and testing |

### Key Questions When Choosing

1. **Team size?** Larger teams often benefit from more documentation
2. **Iteration pace?** Rapid iteration may favor lighter workflows
3. **Accountability needs?** Higher stakes = more verification
4. **Documentation value?** Do you need an audit trail?
5. **Existing culture?** Work with team preferences, not against them

---

## Workflow Content Structure

All workflows should include:

- **Title and Purpose** - What is this workflow for?
- **Core Steps or Principles** - How does it work?
- **Mandatory Rules** - What must always be done?
- **Definition of Done** - When is work complete?
- **Resources** - Where to find more info
- **Examples** (optional) - Show real-world usage
- **Further Reading** (optional) - Links and references

See `custom-template.md` for detailed structure.

---

## Integrating with Bootstrap.py

When you create a custom workflow:

1. **Add to section_map** in `load_system_prompt()`:
   ```python
   "MY-WORKFLOW": "workflows/my-workflow.md"
   ```

2. **Add command-line args** in `main()`:
   ```python
   parser.add_argument("--enable-my-workflow", action="store_true")
   parser.add_argument("--disable-my-workflow", action="store_true")
   ```

3. **Test**:
   ```bash
   python3 bootstrap.py --analyze-workflow
   python3 bootstrap.py --enable-my-workflow --commit
   ```

The workflow will be injected into AGENTS.md as:
```markdown
<!-- SECTION: MY-WORKFLOW -->
[workflow content]
<!-- END-SECTION -->
```

---

## Workflow State Management

### How State Persists

- bootstrap.py stores state in AGENTS.md as HTML comments
- Example: `<!-- BOOTSTRAP-STATE: logs-first=enabled -->`
- On next run, bootstrap.py reads this state and preserves it
- Explicit arguments override prior state

### Example State Transitions

```bash
# First run: auto-detect recommends logs-first
python3 bootstrap.py --analyze-workflow
# Output: "Recommended: logs-first (small active project)"

# Developer enables it
python3 bootstrap.py --enable-logs-first --commit
# State saved to AGENTS.md

# Future runs preserve state
python3 bootstrap.py --analyze-workflow
# Output: "Current: logs-first (enabled)"

# Developer can override if needed
python3 bootstrap.py --disable-logs-first --commit
```

---

## Workflow Recommendations

### Determining the Right Workflow for Your Project

**The bootstrap.py analyzer will recommend** based on your project characteristics:

**Example criteria:**
- Team size (solo developer vs larger team)
- Project activity (frequent commits vs stable)
- Existing structure (has dev_notes/ or similar)
- Documentation preferences (detailed audit trail vs minimal overhead)

**Setup:**
```bash
python3 docs/system-prompts/bootstrap.py --enable-logs-first --commit
```

---

## Future Workflows

As your project evolves, consider:

- **Minimal workflow** - Reduce documentation overhead as team grows
- **Enterprise workflow** - Add compliance and approval gates
- **Research workflow** - Flexible exploration with different DoD
- **Open-source workflow** - Community-friendly documentation

Each can be created by adapting the custom-template.

---

## Troubleshooting

### Workflow not appearing in AGENTS.md?

- Run bootstrap.py with `--commit` flag: `python3 bootstrap.py --enable-logs-first --commit`
- Check that workflow file exists: `docs/system-prompts/workflows/logs-first.md`
- Verify bootstrap.py can read it: `python3 bootstrap.py --analyze-workflow`

### Workflow changes not taking effect?

- State is sticky - previous decisions are preserved
- To apply new state: `python3 bootstrap.py --enable-logs-first --commit` (even if already enabled)
- For debugging: `python3 bootstrap.py --analyze-workflow` shows current state

### Custom workflow not recognized?

- Verify `section_map` entry in bootstrap.py
- Verify command-line args added to parser
- Run `python3 bootstrap.py --help` to confirm args appear
- Test with: `python3 bootstrap.py --analyze-workflow`

---

## More Information

- **How to use logs-first?** → See `logs-first.md`
- **How to create custom workflow?** → See `custom-template.md`
- **Full templates and examples?** → See `docs/templates.md`
- **Definition of Done details?** → See `docs/definition-of-done.md`
- **Architecture overview?** → See `docs/architecture.md`
