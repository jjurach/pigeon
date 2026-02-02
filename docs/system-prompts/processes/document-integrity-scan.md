# Document Integrity Scan Process

**Purpose:** Ensure consistency, correctness, and maintainability of documentation across the project.

**Status:** Documented and automated via `docscan.py`

---

## Overview

The document integrity scan is a multi-layer verification process that checks:

1. **Referential Correctness** - All links point to existing files
2. **Architectural Constraints** - System-prompts doesn't reference back into project files without explicit marking
3. **Reference Formatting** - All file references use hyperlinks or backticks (not plain text)
4. **Naming Conventions** - Files follow established naming patterns
5. **Directory Structure** - Tool guides are organized correctly (generic vs. project-specific)
6. **Coverage** - All documentation relationships are captured and verified

---

## Scan Layers

### Layer 1: Broken Link Detection

**Goal:** Ensure all markdown links `[text](path)` point to valid files.

**Process:**
1. Scan all `.md` files recursively from project root
2. Extract all markdown links using regex: `\[([^\]]+)\]\(([^)]+)\)`
3. For each link target:
   - Skip external URLs (http://, https://)
   - Skip anchors (#section)
   - Skip email links (mailto:)
   - Resolve relative paths from source file location
   - Check if target file exists on disk
4. Report any missing targets

**Example:**
```markdown
[See this guide](docs/system-prompts/tools/claude-code.md)
```

Resolution:
- Source: `README.md` (in project root)
- Relative path: `docs/system-prompts/tools/claude-code.md`
- Resolved: `/home/phaedrus/AiSpace/second_voice/docs/system-prompts/tools/claude-code.md`
- Verification: File exists ✅

**Failure Example:**
```markdown
[Broken link](./AGENTS.md)  <!-- From docs/ subdirectory -->
```
- Resolved to: `docs/AGENTS.md` (but AGENTS.md is in project root)
- Result: ❌ Link broken

---

### Layer 2: Back-Reference Detection

**Goal:** Ensure system-prompts files don't reference project-specific files unless explicitly marked as conditional.

**Rationale:**
- `docs/system-prompts/` should be reusable across projects
- References outside system-prompts indicate project-specific content
- Such references must be marked as "(if present)" or similar to signal they're optional

**Process:**
1. Identify all files in `docs/system-prompts/` and subdirectories
2. For each file, extract all markdown links
3. Categorize links:
   - ✅ **Safe:** External URLs, anchors, other system-prompts files, entry points (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.aider.md`, `.clinerules`)
   - ⚠️ **Conditional:** Links outside system-prompts that are marked with "(if present)" or similar
   - ❌ **Problematic:** Links outside system-prompts without conditional marking
4. Report problematic references

**Example (Safe):**
```markdown
<!-- In docs/system-prompts/tools/claude-code.md -->
See [AGENTS.md](../AGENTS.md) for workflow details.
```
- Target: AGENTS.md (entry point, always present)
- Status: ✅ Safe

**Example (Conditional - Safe):**
```markdown
<!-- In docs/system-prompts/tools/aider.md -->
For project-specific configuration, see [aider-config]
(`docs/tool-specific-guides/aider.md`) *(if this file exists in your project)*.
```
- Target: Outside system-prompts
- Marked: *(if this file exists in your project)*
- Status: ✅ Conditional reference

**Example (Problematic - Unsafe):**
```markdown
<!-- In docs/system-prompts/tools/cline.md -->
This integrates with [our provider](docs/tool-specific-guides/cline.md).
```
- Target: Outside system-prompts
- Marked: No
- Status: ❌ Project-specific reference without marking

---

### Layer 3: Reference Formatting Verification

**Goal:** Ensure all file/document references use proper markdown formatting (hyperlinks or backticks), not plain text.

**Rationale:**
- Markdown hyperlinks `[text](path)` are clickable in markdown viewers
- Backticks `` `file.md` `` semantically identify filenames as code/paths
- Plain text references are hard to discover and don't work in markdown viewers
- Consistent formatting makes documentation more professional and usable

**Process:**
1. Scan all `.md` files for markdown file references
2. Skip entry point files (AGENTS.md, CLAUDE.md, etc.) - these meta-documents frequently self-reference
3. Skip transient directories (dev_notes/, tmp/) - working documents, not canonical
4. For each reference to a `.md` file, check if it's properly formatted:
   - ✅ **Hyperlink:** Link format with brackets and parentheses - for navigation links
   - ✅ **Backtick:** Filename wrapped in backticks - for inline file references
   - ❌ **Plain text:** "see file.md" - NOT ALLOWED
5. Remove code blocks and inline code to avoid false positives
6. Report any plain-text references

**Examples:**

**Correct - Hyperlink for Navigation:**
```markdown
[AGENTS.md](AGENTS.md)
[See the test guide](docs/test-guide.md)
```

**Correct - Backticks for File References in Prose:**
```markdown
The `AGENTS.md` file defines the workflow.
Consult `docs/definition-of-done.md` for completion criteria.
Configuration files: `config.json`, `setup.py`
```

**Incorrect - Plain Text (FLAGGED):**
```markdown
See AGENTS.md for details.
Check docs/test-guide.md for more information.
```

**Severity:** Warning (flags potential issues but doesn't block)

---

### Layer 4: File Organization Verification

**Goal:** Verify tool guides are in correct locations based on reusability.

**Process:**
1. Check `docs/tool-specific-guides/` directory:
   - All files should be project-specific (reference second_voice architecture, configuration, etc.)
   - Should NOT be generic AGENTS.md + tool workflow guides
2. Check `docs/system-prompts/tools/` directory:
   - All files should be generic (reusable across projects)
   - Should document AGENTS.md workflow + tool integration
   - Should NOT reference project-specific implementation details

**Verification:**
- ✅ `docs/tool-specific-guides/cline.md` - Project-specific (references `second_voice` architecture, `src/second_voice/core/processor.py`)
- ✅ `docs/system-prompts/tools/claude-code.md` - Generic (explains AGENTS.md + Claude Code, no second_voice references)
- ✅ `docs/system-prompts/tools/aider.md` - Generic (explains AGENTS.md + Aider)
- ✅ `docs/system-prompts/tools/codex.md` - Generic (explains AGENTS.md + Codex)
- ✅ `docs/system-prompts/tools/gemini.md` - Generic (explains AGENTS.md + Gemini)

---

### Layer 5: Reference Coverage

**Goal:** Ensure all tool guide references from main project files are complete and correct.

**Process:**
1. Scan all `.md` files in project root and main docs/ directory
2. Find all tool guide references (links containing: claude-code, aider, codex, gemini, cline)
3. Verify each reference:
   - Points to correct location (generic → system-prompts/tools/, project-specific → tool-specific-guides/)
   - File exists at target location
   - Link syntax is correct
4. Report coverage (number of references found and verified)

**Example Coverage Report:**
```
README.md:
  → docs/system-prompts/tools/claude-code.md ✅ (generic)
  → docs/system-prompts/tools/aider.md ✅ (generic)
  → docs/system-prompts/tools/codex.md ✅ (generic)
  → docs/system-prompts/tools/gemini.md ✅ (generic)
  → docs/tool-specific-guides/cline.md ✅ (project-specific)
```

---

### Layer 6: Naming Convention Verification

**Goal:** Ensure all documentation files follow established naming conventions.

**Process:**
1. Check all files in `docs/` directory and subdirectories
2. For auto-discovered files (CLAUDE.md, GEMINI.md, etc.):
   - Verify exact names match
   - Verify they exist in expected locations (project root)
3. For documentation files in docs/:
   - Verify `lowercase-kebab.md` naming pattern
   - Allow exceptions for established patterns (like dev_notes/ with timestamp format)
4. Report any violations

**Example:**
- ✅ `docs/tools-capabilities.md` - Correct (lowercase-kebab)
- ✅ `docs/file-naming-conventions.md` - Correct (lowercase-kebab)
- ✅ `AGENTS.md` - Correct (auto-discovered entry point)
- ❌ `docs/Tools-Capabilities.md` - Incorrect (should be lowercase-kebab)

---

### Layer 7: Alias Verification

**Goal:** Ensure all shell aliases referenced in tips documents are defined in aliases.sh.

**Process:**
1. Scan all `.md` files in `docs/system-prompts/tips/` directory
2. Extract alias references from markdown (looking for `alias name=` patterns in code blocks)
3. Read `docs/system-prompts/tips/aliases.sh`
4. Verify each referenced alias exists in aliases.sh
5. Report any missing aliases

**Alias pattern detection:**
- Matches lines like: `alias claude-sys='claude --model sonnet'`
- Matches lines like: `# Use claude-dev for development`
- Matches inline references like: `` `claude-quick` ``
- Extracts alias names: claude-sys, claude-dev, claude-quick, codex-sys, cline-list, etc.

**Verification:**
```
tips/claude-code.md references:
  → claude-sys ✅ (found in aliases.sh)
  → claude-quick ✅ (found in aliases.sh)
  → claude-dev ✅ (found in aliases.sh)
  → claude-think ✅ (found in aliases.sh)

tips/codex.md references:
  → codex-sys ✅ (found in aliases.sh)
  → codex-quick ✅ (found in aliases.sh)
  → codex-dev ✅ (found in aliases.sh)
  → codex-think ✅ (found in aliases.sh)

tips/cline.md references:
  → cline-list ✅ (found in aliases.sh)
  → cline-resume ✅ (found in aliases.sh)
  → cline-view ✅ (found in aliases.sh)
  → cline-new ✅ (found in aliases.sh)
  → cline-chat ✅ (found in aliases.sh)
  → cline-sys ✅ (found in aliases.sh)
  → cline-dev ✅ (found in aliases.sh)
```

**Failure Example:**
```
tips/claude-code.md references:
  → claude-sys ✅ (found in aliases.sh)
  → claude-experimental ❌ (NOT found in aliases.sh)

Result: Alias verification failed
Recommendation: Add missing alias to aliases.sh or remove reference from tips
```

**Rationale:**
- Ensures aliases.sh is complete and up-to-date
- Prevents documentation drift (docs mention aliases that don't exist)
- Makes it easy for users to source all aliases at once
- Provides single source of truth for alias definitions

---

## Constraint Rules

The scan enforces these rules. Each can be customized or extended:

### Rule 1: No Broken Links
```
All [text](target) links must point to existing files.
```

### Rule 2: System-Prompts Back-References Must Be Marked
```
Links from docs/system-prompts/ to files outside docs/system-prompts/
must contain text indicating they are conditional:
  - "(if present)"
  - "(optional)"
  - "(if exists)"
  - Similar conditional language

Exception: Links to entry points (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.aider.md`, `.clinerules`)
are always safe (these files must exist in projects using AGENTS.md)
```

### Rule 3: Document Reference Formatting
```
All references to .md files must use proper markdown formatting:

Hyperlinks (for navigation links):
  Format: [text](relative/path/to/file.md)
  Use when: Creating call-to-action links, navigation sections
  Example: [AGENTS.md](AGENTS.md)

Backticks (for file references in prose):
  Format: `relative/path/to/file.md`
  Use when: Mentioning files inline, listing files, describing content
  Example: "The `AGENTS.md` file defines the workflow"

Never use plain text:
  ❌ See AGENTS.md (no formatting)
  ❌ check docs/file.md (no formatting)

Exemptions:
  Entry point files (`AGENTS.md`, `CLAUDE.md`, `.aider.md`, `.clinerules`, `GEMINI.md`)
  are exempt from reference-formatting checks.

  Rationale:
    - These are meta-documents that provide instructions to AI agents
    - They frequently reference themselves and other documentation as part of
      explaining the workflow (e.g., "See AGENTS.md section X", "this AGENTS.md file")
    - They are transitional instruction documents, not canonical user documentation
    - Forcing backticks on every self-reference creates noise and reduces readability
    - Similar to how dev_notes/ is exempt (transient working documents)

Rationale:
  - Hyperlinks are clickable in markdown viewers
  - Backticks identify files as code/paths
  - Consistency makes documentation more professional
  - Plain text references are hard to discover
```

### Rule 4: Tool Guides in Correct Locations
```
Generic tool guides (reusable across projects):
  Location: docs/system-prompts/tools/{tool}.md
  Content: AGENTS.md workflow + tool integration patterns
  References: No second_voice-specific code or architecture

Project-specific guides:
  Location: docs/tool-specific-guides/{tool}.md
  Content: Integration with project implementation
  References: OK to reference project architecture/config
```

### Rule 5: Naming Conventions
```
Documentation files in docs/ directory:
  Pattern: `lowercase-kebab.md`
  Exception: none currently

Auto-discovered entry points:
  Pattern: {TOOL}.md (uppercase)
  Location: Project root
  Examples: `AGENTS.md`, `CLAUDE.md`, `.aider.md`, `.clinerules`, `GEMINI.md`

Timestamped files (dev_notes/):
  Pattern: YYYY-MM-DD_HH-MM-SS_description.md
  Location: dev_notes/specs/, dev_notes/project_plans/, dev_notes/changes/
```

### Rule 6: Reference Coverage
```
All tool guides must be referenced from:
  1. README.md (main index)
  2. docs/tools-capabilities.md (tool matrix)
  3. docs/file-naming-conventions.md (if mentioned)

Missing references indicate:
  - New tool guide created but not linked
  - Guides need to be registered in project docs
```

### Rule 7: Alias Consistency

```
All shell aliases referenced in tips/ documents must be defined in aliases.sh.

Verification process:
  1. Scan all markdown files in docs/system-prompts/tips/
  2. Extract alias references (alias definitions and usage examples)
  3. Verify each alias exists in docs/system-prompts/tips/aliases.sh
  4. Report missing aliases

Patterns to detect:
  - Alias definitions: alias claude-sys='command'
  - Inline references: `claude-dev` in prose
  - Usage examples: claude-quick 'task'

Rationale:
  - Single source of truth for alias definitions
  - Prevents documentation drift
  - Ensures users can source all aliases at once
  - Makes aliases easy to discover and load
```

---

## Scan Output

The scan produces three output sections:

### 1. Broken Links
```
### BROKEN LINKS
Found 3 broken links:

  docs/file-naming-conventions.md
    → ./AGENTS.md
    Target: /home/phaedrus/AiSpace/second_voice/docs/AGENTS.md
    ❌ File does not exist
```

### 2. Back-References
```
### BACK-REFERENCES FROM docs/system-prompts/
(References from system-prompts to project-specific files)

  ⚠️  docs/system-prompts/tools/cline.md
      → docs/tool-specific-guides/cline.md [no marking]
```

### 3. Coverage
```
### REFERENCE COVERAGE

Files referencing tool guides:

  README.md:
    → docs/system-prompts/tools/claude-code.md ✅ (generic)
    → docs/system-prompts/tools/aider.md ✅ (generic)
```

---

## How to Run the Scan

### Manual Execution
```bash
cd /path/to/second_voice
python3 docs/system-prompts/docscan.py
```

### With Specific Checks
```bash
# Only check broken links
python3 docs/system-prompts/docscan.py --check broken-links

# Only check back-references
python3 docs/system-prompts/docscan.py --check back-references

# Check specific file
python3 docs/system-prompts/docscan.py --file docs/README.md

# Verbose output
python3 docs/system-prompts/docscan.py --verbose

# Strict mode (fail on warnings)
python3 docs/system-prompts/docscan.py --strict
```

### Integration with CI/CD
```bash
# In pre-commit hook or GitHub Actions
python3 docs/system-prompts/docscan.py --strict
if [ $? -ne 0 ]; then
  echo "Documentation integrity check failed"
  exit 1
fi
```

---

## Extending the Scan

The scan is designed to be extensible. To add new constraint rules:

### 1. Define Rule in Ruleset
```python
# In docscan.py
RULES = {
    'your-new-rule': {
        'name': 'Your New Rule Name',
        'description': 'What this rule checks',
        'severity': 'error',  # or 'warning'
        'checker': your_check_function,
    }
}
```

### 2. Implement Checker Function
```python
def your_check_function(project_root, options):
    """
    Check for specific constraint violations.

    Args:
        project_root: Path to project root
        options: Parsed command-line options

    Returns:
        List of violations
    """
    violations = []
    # Your check logic here
    return violations
```

### 3. Add Command-Line Option
```python
parser.add_argument(
    '--your-option',
    action='store_true',
    help='Enable your new check'
)
```

---

## Known Limitations

1. **Comments in Code:** Links in code blocks or comments are not scanned
2. **Dynamic Paths:** Cannot detect links generated dynamically
3. **Line Numbers:** Errors report file paths but not line numbers (could be added)
4. **Context:** Does not check semantic correctness of links (only file existence)
5. **Performance:** Scans all .md files (could cache results)

---

## Future Enhancements

- [ ] Add line number reporting for broken links
- [ ] Cache scan results between runs
- [ ] Add semantic link validation (verify link text matches file content)
- [ ] Generate HTML report with violations
- [ ] Integrate with GitHub Actions status checks
- [ ] Add metrics dashboard (link coverage over time)
- [ ] Support for custom constraint rules per project

---

## Example: Adding a New Constraint

**Scenario:** Project wants to ensure all tool guides have a Status field.

**Step 1: Define Rule**
```python
RULES = {
    'tool-guide-status': {
        'name': 'Tool Guide Status Field',
        'description': 'Verify all tool guides have a Status field',
        'severity': 'error',
        'checker': check_tool_guide_status,
    }
}
```

**Step 2: Implement Checker**
```python
def check_tool_guide_status(project_root, options):
    violations = []
    tools_dir = project_root / "docs" / "system-prompts" / "tools"

    for guide_file in tools_dir.glob("*.md"):
        if guide_file.name == "README.md":
            continue

        with open(guide_file) as f:
            content = f.read()

        if "**Status:**" not in content:
            violations.append({
                'file': str(guide_file.relative_to(project_root)),
                'type': 'missing-status',
                'message': 'Tool guide missing Status field'
            })

    return violations
```

**Step 3: Run Scan**
```bash
python3 docscan.py
# Output will include new violations if any exist
```

---

## Summary

This document describes a comprehensive, extensible document integrity scan that ensures:

- ✅ All links work correctly
- ✅ System-prompts files remain reusable
- ✅ Tool guides are organized by purpose
- ✅ Naming conventions are consistent
- ✅ Reference coverage is complete

The process is automated via `docscan.py` and can be extended with custom rules as project needs evolve.
