# Principle: Tool Reliability & Fallback Mechanisms

**Purpose:** Ensure tools used by agents work reliably across different environments without requiring special setup or external CLI availability.

---

## The Problem

When tools depend solely on external CLIs or services, they become fragile:

```python
# ❌ FRAGILE: Only works if 'bd' CLI is available
result = subprocess.run(['bd', 'ls', '--json'], capture_output=True, text=True, check=True)
data = json.loads(result.stdout)
```

Issues this causes:
1. **Environment dependency** - Works on some machines, fails on others
2. **Setup requirements** - Agents must activate venvs or install tools
3. **No transparency** - Agents don't know why it failed
4. **Cascading failures** - Single point of failure blocks entire workflow

---

## The Solution: Dual-Tier Architecture

Every tool that agents depend on should have a **primary method** and **fallback method**:

```python
# ✅ RELIABLE: Primary + fallback architecture
def load_data():
    try:
        # Primary: Use external CLI if available
        result = subprocess.run(['bd', 'ls', '--json'], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        # Fallback: Read directly from file if CLI fails
        with open('.beads/issues.jsonl', 'r') as f:
            data = []
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
```

**Benefits:**
- ✅ Works with or without external CLI
- ✅ No special setup needed
- ✅ Transparent to agents
- ✅ Graceful degradation

---

## Guidelines for Implementing Tool Reliability

### 1. Identify Primary & Fallback Methods

For any data source, identify two ways to get the same information:

| Tool | Primary Method | Fallback Method |
|------|---|---|
| `bd` CLI for beads | `bd list --json` | Read `.beads/issues.jsonl` directly |
| AWS Lambda status | AWS SDK / API | Read CloudFormation state files |
| Git repository state | `git status --json` | Parse `.git/index` + `HEAD` |
| Environment config | CLI tool | Read JSON/YAML config files |

### 2. Handle Format Differences

Different sources may return data in different formats. Normalize them:

```python
def normalize_beads(raw_data):
    """
    Convert different source formats to consistent internal format.

    CLI format: {'id': 'bd-123', 'status': 'closed', ...}
    JSONL format: {'id': 'bd-123', 'status': 'open', ...}
    """
    normalized = []
    for item in raw_data:
        normalized.append({
            'id': item.get('id'),
            'status': item.get('status', 'unknown'),
            'title': item.get('title', ''),
            'labels': item.get('labels', [])
        })
    return normalized
```

### 3. Test Fallback Paths

Ensure fallback methods work even when primary fails:

```bash
# Test without 'bd' CLI available
PATH="" python3 my_tool.py  # Should still work

# Test with missing config files
rm .beads/issues.jsonl
python3 my_tool.py  # Should handle gracefully
```

### 4. Provide Clear Error Messages

If both primary and fallback fail, give actionable guidance:

```python
except Exception as e:
    print(f"Error: Could not load beads data.")
    print(f"  Primary (bd CLI): {primary_error}")
    print(f"  Fallback (.beads/issues.jsonl): {fallback_error}")
    print(f"  Action: Ensure you're in project root with .beads/ directory")
    sys.exit(1)
```

### 5. Document Format Handling

Always document which formats are supported:

```python
def load_beads(self) -> bool:
    """
    Load beads from either CLI or direct file read.

    Supported formats:
    - bd CLI output: JSON array with id, status, title, labels, dependencies
    - .beads/issues.jsonl: JSONL format (one JSON object per line)

    Returns:
        True if data loaded successfully, False otherwise

    Raises:
        FileNotFoundError: If both methods fail and .beads/ not found
    """
```

---

## Multi-Source Aggregation Patterns

When building tools that read from multiple independent data sources (e.g., submodules, projects, or files), use these patterns to avoid cascade failures and produce clear output.

### Pattern: Per-Source Error Isolation

Always wrap each source's processing in an exception catch. Store the error in the result object rather than propagating it. This prevents one bad source from blocking all others.

```python
results = []
for item in items:
    try:
        result = process(item)
        results.append({'name': item.name, 'data': result, 'error': None})
    except Exception as e:
        # Log to stderr with source identifier, continue processing
        print(f"Warning: [{item.name}] {e}", file=sys.stderr)
        results.append({'name': item.name, 'data': None, 'error': str(e)})
# Process results - check result['error'] is None before using result['data']
```

**Key rules:**
- Always prefix error messages with `[SourceName]` so failures are identifiable in multi-source output
- Store error state in result object, don't silently swallow or re-raise
- Continue processing remaining sources after any single failure

### Pattern: Annotate All Messages with Source Context

In multi-source tools, every log line must include a source prefix:
```python
# ❌ BAD: Ambiguous in multi-project output
print(f"Warning: Skipping corrupt line 42 in .beads/issues.jsonl", file=sys.stderr)

# ✅ GOOD: Source identified
print(f"Warning: [myproject] Skipping corrupt line 42 in .beads/issues.jsonl", file=sys.stderr)
```

### Pattern: Separate Structured Output from Diagnostic Output

Tools that produce machine-readable output (JSON, CSV) must **never** write to stdout except for the structured data. All warnings and diagnostics go to stderr.

```python
# ❌ BAD: Mixes warning into JSON stream
print("Warning: some issue")   # stdout - will corrupt JSON consumers
print(json.dumps(result))

# ✅ GOOD: Diagnostics to stderr, data to stdout
print("Warning: some issue", file=sys.stderr)
print(json.dumps(result))      # stdout only for structured data
```

**Document this in the tool's help text**, since users piping output may use `2>&1` which silently corrupts the structured output. Example: "Note: use without `2>&1` when parsing JSON output - warnings go to stderr."

### Pattern: Line-by-Line Parsing for JSONL / Streaming Formats

Never parse a multi-record text format as a single unit. Always iterate line-by-line and apply error handling per line:

```python
with open(jsonl_path, 'r') as f:
    records = []
    for lineno, line in enumerate(f, 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"Warning: [{source_name}] Skipping corrupt line {lineno}: {e}", file=sys.stderr)
```

This prevents a single malformed line from losing all subsequent data. Emit a per-line warning with file path and line number for debugging.

---

## Common Tool Patterns

### Pattern 1: CLI with File Fallback

```python
def get_status():
    try:
        # Primary: External CLI
        result = subprocess.run(['external-tool', '--json'], check=True, capture_output=True)
        return json.loads(result.stdout)
    except:
        # Fallback: Direct file read
        with open('status.json') as f:
            return json.load(f)
```

### Pattern 2: API with Cache File Fallback

```python
def fetch_data(url):
    try:
        # Primary: Fetch from API
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, requests.Timeout):
        # Fallback: Use cached file
        with open('cache.json') as f:
            return json.load(f)
```

### Pattern 3: Environment Variable with Default

```python
def get_config():
    # Primary: Environment variable
    if os.getenv('CONFIG_PATH'):
        with open(os.getenv('CONFIG_PATH')) as f:
            return json.load(f)

    # Fallback: Default location
    if os.path.exists('config.json'):
        with open('config.json') as f:
            return json.load(f)

    # Final fallback: Built-in defaults
    return DEFAULT_CONFIG
```

---

## Reliability Testing Checklist

Before deploying a tool that agents will use, verify:

- [ ] **No external CLI required** - Tool works if `PATH=""`
- [ ] **No special setup** - No venv activation, no `npm install`, no environment variables
- [ ] **Format handling tested** - Both primary and fallback formats work
- [ ] **Error messages clear** - If failures occur, guidance is actionable
- [ ] **Timeout protection** - No hanging on network calls (use timeouts)
- [ ] **Offline capability** - Works without internet/API access
- [ ] **Documentation complete** - Agents know what the tool does and how to use it

---

## Real-World Example: planning-summary.py

See `dev_notes/changes/2026-02-15_15-10-00_planning_summary_improvements.md` for a real example of implementing dual-tier reliability.

**Before (Fragile):**
```bash
source venv/bin/activate && python3 docs/system-prompts/planning-summary.py
# ❌ Requires setup
# ❌ Fails without 'bd' CLI
```

**After (Reliable):**
```bash
python3 docs/system-prompts/planning-summary.py
# ✅ Works immediately
# ✅ Automatic fallback to .beads/issues.jsonl
# ✅ No setup required
```

---

## When to Break This Rule

Fallback mechanisms aren't needed for:
- **One-time setup scripts** that run once per project (OK to require setup)
- **Developer tools** that are explicitly installed (e.g., linters, formatters)
- **Internal-only utilities** that aren't used by agents (e.g., admin scripts)

They ARE needed for:
- **Agent-facing tools** (tools that agents invoke)
- **Critical path tools** (blocking execution)
- **Tools used in production** (need reliability)

---

**Last Updated:** 2026-02-18
**Status:** Active
**Principle Introduced:** Mobile App Migration Epic (pj-5)
**Recent Updates:** 2026-02-18 - Added Multi-Source Aggregation Patterns section (per-source error isolation, source-annotated messages, stdout/stderr separation, JSONL line-by-line parsing) based on lessons from Planning Summary Submodule Integration
