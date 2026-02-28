# Error Handling Patterns for Multi-Project Tools

**Purpose:** Standardize error handling approach for tools that process multiple projects, files, or data sources to prevent cascade failures and improve debugging.

**Applicable To:** Tools that iterate over multiple items (projects, files, records) and need to continue processing when individual items fail.

**Status:** Formalized from Mellona-Pigeon epic (2026-02-20)

---

## Three Core Patterns

### Pattern 1: Per-Source Exception Isolation

**Problem:** A single source failure (corrupt data, permission error, API failure) cascades and prevents processing of all other sources.

**Solution:** Wrap each source's processing in its own try-catch block. Store errors in a result dict and continue processing.

**Implementation:**

```python
def process_multiple_sources(sources: List[Source]) -> ProcessingResults:
    """Process multiple sources, isolating failures per source."""
    results = {
        'succeeded': [],
        'failed': [],
        'errors': {}
    }

    for source in sources:
        try:
            data = source.read()
            processed = process_data(data)
            results['succeeded'].append(source.name)
        except PermissionError as e:
            results['failed'].append(source.name)
            results['errors'][source.name] = f"Permission denied: {str(e)}"
        except ValueError as e:
            results['failed'].append(source.name)
            results['errors'][source.name] = f"Invalid data: {str(e)}"
        except Exception as e:
            results['failed'].append(source.name)
            results['errors'][source.name] = f"Unexpected error: {type(e).__name__}: {str(e)}"

    return results
```

**Benefits:**
- One source failure doesn't block other sources
- Complete visibility into which sources succeeded/failed
- Errors can be reported per-source for targeted remediation
- Allows graceful degradation in batch processing

**When to use:**
- Processing multiple files in a directory
- Processing multiple git submodules
- Processing multiple records in a data file
- API calls to multiple endpoints

---

### Pattern 2: Context-Rich Error Messages

**Problem:** Generic error messages ("Failed to process file") don't identify which project/file/source caused the error, making debugging difficult at scale.

**Solution:** Always include source/project context in error output. Use consistent format that enables easy filtering and parsing.

**Implementation:**

```python
def log_error_with_context(project: str, file: str, error: Exception):
    """Log error with complete context for easy identification."""
    logger.error(
        f"Processing failed",
        extra={
            'project': project,
            'file': file,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
    )
    # Output format for humans:
    print(f"ERROR [project={project}] [file={file}]: {error}")
```

**Error Message Format:**

```
ERROR [project=pigeon] [file=spec.md]: PermissionError: Cannot read /path/to/file
WARNING [project=myproject] [file=config.yaml]: YAML parse error at line 42
```

**Benefits:**
- Easy to identify which project/file failed
- Supports filtering/grepping error logs
- Machine-readable format (can be parsed programmatically)
- Facilitates automatic error reporting and aggregation

**When to use:**
- Any multi-project or multi-file processing tool
- Tools that output structured data (JSON, CSV)
- Tools integrated into larger workflows

---

### Pattern 3: Stdout/Stderr Separation

**Problem:** Diagnostic messages mixed into stdout corrupt machine-readable output (JSON, CSV) when users redirect output with `>` or `2>&1`.

**Solution:** Enforce strict separation:
- **stderr:** All diagnostic output (warnings, verbose logs, progress info)
- **stdout:** Machine-readable output only (JSON, CSV, formatted results)

**Implementation:**

```python
import sys
import json

def output_results(results: dict):
    """Output machine-readable results to stdout only."""
    # ALL diagnostic output goes to stderr
    sys.stderr.write("Processing complete. ")
    sys.stderr.write(f"Processed {len(results['items'])} items.\n")

    # ONLY machine-readable output on stdout
    json.dump(results, sys.stdout, indent=2)
    sys.stdout.write('\n')

# Usage:
# This works correctly and produces clean JSON:
# $ python script.py > output.json 2>/dev/null
# output.json contains only valid JSON, no diagnostic text
```

**Safe Redirection Examples:**

```bash
# Get clean JSON output, discard diagnostics:
$ python tool.py > output.json 2>/dev/null

# Get clean JSON with stderr warnings in separate file:
$ python tool.py > output.json 2> warnings.log

# Process JSON with jq, ignoring diagnostic output:
$ python tool.py 2>/dev/null | jq '.results[]'
```

**Benefits:**
- Tools output can be safely piped to other commands
- Automation scripts don't need to parse stderr
- Users can redirect output without corruption
- Clear separation of concerns (diagnostics vs. data)

**When to use:**
- Any tool that outputs structured data (JSON, CSV, YAML)
- Tools designed for automation/scripting
- Tools with verbose logging

---

## Implementation Checklist

When implementing a multi-project tool, ensure:

- [ ] **Per-Source Isolation:** Each source/file/project wrapped in try-catch, errors stored in result dict
- [ ] **Context-Rich Errors:** All error messages include project/file/source identification
- [ ] **Error Categories:** Different exception types for different error conditions (PermissionError, ValueError, etc.)
- [ ] **Result Aggregation:** Results dict includes both successes and failures with detailed error info
- [ ] **Stdout/Stderr Separation:** Diagnostic output on stderr, machine-readable output on stdout only
- [ ] **Machine-Readable Format:** Consider JSON output for tool results (for automated processing)
- [ ] **Testing:** Include tests for error paths, not just happy path

---

## Testing Error Paths

Always include tests for error conditions:

```python
def test_processing_continues_on_corrupt_file():
    """Verify processing continues when one file is corrupt."""
    sources = [
        MockSource('project1', data='valid'),
        MockSource('project2', data='{invalid json}'),  # Corrupt
        MockSource('project3', data='valid'),
    ]

    results = process_multiple_sources(sources)

    # Verify successes
    assert 'project1' in results['succeeded']
    assert 'project3' in results['succeeded']

    # Verify failure is recorded
    assert 'project2' in results['failed']
    assert 'Invalid data' in results['errors']['project2']
```

---

## Real-World Examples

### Example 1: Multi-Project Spec Processing

From Mellona-Pigeon epic (Phase 13):

```python
def route_specs_to_projects(specs: List[SpecFile]) -> RoutingResults:
    results = {'routed': [], 'errors': {}}

    for spec in specs:
        try:
            project = detect_project_from_spec(spec)
            copy_to_project_inbox(spec, project)
            results['routed'].append({
                'spec': spec.path,
                'project': project
            })
        except ProjectNotFoundError as e:
            results['errors'][spec.path] = f"Project not found: {str(e)}"
        except PermissionError as e:
            results['errors'][spec.path] = f"Cannot copy to project inbox: {str(e)}"

    return results
```

---

## Related Concepts

- **Circuit Breaker Pattern:** For APIs, stop retrying after N consecutive failures
- **Retry Logic:** Exponential backoff for transient failures
- **Dead Letter Queue:** Store failed items for later inspection
- **Logging Strategy:** Use structured logging (JSON) for machine analysis

---

## References

**Source:** Mellona-Pigeon Epic Workflow Analysis (2026-02-20)

**Originally Discovered In:**
- Phase 2 (Mellona): Error handling for multi-provider scenarios
- Phase 13 (Pigeon): Multi-project routing with submodule discovery
- Phase 14 (Pigeon): Integration with error resilience requirements

**Lessons That Led to This Guide:**
- Per-source exception isolation prevented cascade failures when one project inbox was inaccessible
- Context-rich errors reduced debugging time from 15+ minutes to <2 minutes per incident
- Stdout/stderr separation became critical when JSON output was piped to other tools
