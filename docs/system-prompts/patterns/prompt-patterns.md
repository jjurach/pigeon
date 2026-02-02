# Universal Prompt Patterns

This document defines prompt structures that work across Claude Code, Aider, Gemini, and other AI coding tools. Use these patterns to write requests that get consistent, high-quality responses regardless of which tool you're using.

**Note:** Examples in this document use placeholder names like `[your-package]`, `[project-name]`, and `[External API A]`. Replace these with your actual project names and service names.

## Pattern Categories

1. [Request Analysis](#request-analysis-pattern)
2. [Planning & Design](#planning-design-pattern)
3. [Implementation](#implementation-pattern)
4. [Verification](#verification-pattern)
5. [Debugging](#debugging-pattern)
6. [Documentation](#documentation-pattern)

---

## Request Analysis Pattern

**When:** At the start of any task, before making changes.

**Template:**
```
I need to [goal].

Current situation:
- [What exists now]
- [What's working]
- [What's broken or missing]

Acceptance criteria:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

Questions for you:
1. [Clarification question 1]
2. [Clarification question 2]
```

**Example:**
```
I need to add authentication to the login system.

Current situation:
- Login form exists in /src/auth/login.py
- No password validation
- No session management
- Tests exist but are incomplete

Acceptance criteria:
- [ ] Password validation against requirements
- [ ] Session tokens are created on successful login
- [ ] All tests pass
- [ ] No credentials in logs

Questions for you:
1. Should we use JWT or session cookies?
2. What's the password complexity requirement?
3. Do we need multi-factor authentication now or later?
```

**Why it works:**
- All tools understand structured context
- Acceptance criteria prevent ambiguous completion
- Explicit questions get direct answers
- Blocks "yes, I'll do it" without understanding

---

## Planning & Design Pattern

**When:** Before implementing non-trivial changes.

**Template:**
```
Please review this approach:

Problem: [What you're solving]

Proposed solution:
1. [Step 1 of plan]
2. [Step 2 of plan]
3. [Step 3 of plan]

Files that will change:
- [File 1] (describe change)
- [File 2] (describe change)

Risks/Concerns:
- [Potential issue 1]
- [Potential issue 2]

Is this approach sound? Any improvements?
```

**Example:**
```
Please review this approach:

Problem: Tests are failing because soundfile cleanup causes warnings

Proposed solution:
1. Add warning filters to pytest.ini
2. Create cleanup fixture in conftest.py
3. Force garbage collection after each test
4. Verify tests pass without warnings

Files that will change:
- pytest.ini (add filterwarnings)
- tests/conftest.py (add cleanup fixture)

Risks/Concerns:
- Suppressing warnings might hide real issues
- Garbage collection might slow tests slightly

Is this approach sound? Any improvements?
```

**Why it works:**
- Shows thinking before implementation
- Easy for tool to suggest improvements
- Explicit risks prevent bad decisions
- Works on all tools (no tool-specific magic)

---

## Implementation Pattern

**When:** Ready to write code, execute plan.

**Template:**
```
Next step in the plan: [Step number/description]

What to do:
- [Specific action 1]
- [Specific action 2]
- [Specific action 3]

File to [create/modify]: [path]
Current content: [Show relevant excerpt if modifying]
Changes needed: [Describe delta]

After this step:
- Run: [Command to verify]
- Check: [What to look for in output]
```

**Example:**
```
Next step in the plan: Add pytest configuration

What to do:
- Create pytest.ini in project root
- Configure test discovery
- Add warning filters
- Verify pytest can find tests

File to create: pytest.ini
Changes needed: Define pytest section with test discovery rules

After this step:
- Run: pytest --collect-only
- Check: Should find 94 tests in tests/ directory
```

**Why it works:**
- Clear scope for each step
- Tool knows what to verify
- Easy to spot mistakes in output
- Works for all tools

---

## Verification Pattern

**When:** After completing a step or feature.

**Template:**
```
Please verify this is complete:

Requirements from spec:
- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

What I've done:
1. [Action 1]
2. [Action 2]
3. [Action 3]

How to verify:
```bash
[Command to verify requirement 1]
[Command to verify requirement 2]
[Command to verify requirement 3]
```

[Expected output for each command]
```

Is this complete? Anything missing?
```

**Example:**
```
Please verify this is complete:

Requirements from spec:
- [ ] pytest installed
- [ ] 94 tests pass
- [ ] No warnings during test run
- [ ] Coverage report generated

What I've done:
1. Installed pytest, pytest-cov, requests-mock
2. Created pytest.ini with configuration
3. Created conftest.py with fixtures
4. Created test_config.py, test_processor.py, test_recorder.py
5. Ran full test suite

How to verify:
```bash
pytest -v
pytest --cov=src/[your-package-name]
pytest -q
```

Expected: All tests pass, 49% coverage shown, no warnings

Is this complete? Anything missing?
```

**Why it works:**
- Clear acceptance criteria
- Shows work done
- Provides verification commands
- Works on all tools

---

## Debugging Pattern

**When:** Tests fail, errors appear, unexpected behavior.

**Template:**
```
Something isn't working as expected.

What I tried: [Describe action]
What I expected: [What should happen]
What actually happened: [Error message or unexpected behavior]

Error message (if any):
```
[Full error text, not summarized]
```

File involved: [path]
Relevant code:
```
[Show 5-10 lines of context around problem]
```

I think the issue might be: [Your hypothesis, if any]
```

**Example:**
```
Something isn't working as expected.

What I tried: Run pytest tests/test_recorder.py
What I expected: 24 tests to pass
What actually happened: 2 tests failed

Error message:
AssertionError: assert '/tmp/tmpti75la4g/tmp-audio-1769366994.wav' != '/tmp/tmpti75la4g/tmp-audio-1769366994.wav'

File involved: tests/test_recorder.py line 159
Relevant code:
```python
def test_temp_path_includes_timestamp(self, temp_dir):
    recorder = AudioRecorder(config)
    path1 = recorder._create_temp_audio_path()
    time.sleep(0.01)
    path2 = recorder._create_temp_audio_path()
    assert path1 != path2  # Line 159 - FAILS
```

I think the issue might be: The timestamp resolution is too coarse - both paths
get created in the same second, so they have the same timestamp.
```

**Why it works:**
- Full error context
- Shows your reasoning
- Makes tool's job easier
- Works on all tools

---

## Documentation Pattern

**When:** Writing docs, comments, or docstrings.

**Template:**
```
Please write documentation for [component/function/module]:

Purpose: [One sentence - what is this?]
Key responsibilities: [List main jobs]
Parameters/Inputs:
- [Param 1]: [Type] - [Description]
- [Param 2]: [Type] - [Description]

Returns:
- [Type] - [Description of return value]

Example usage:
```python
[Show real example from code]
```

Edge cases/gotchas:
- [Edge case 1]
- [Edge case 2]

Any warnings or notes:
- [Important note 1]
- [Important note 2]
```

**Example:**
```
Please write docstring for AudioRecorder._calculate_rms():

Purpose: Calculate audio amplitude from waveform data
Key responsibilities:
- Compute RMS (Root Mean Square)
- Normalize to 0.0-1.0 range
- Return float value

Parameters:
- audio_data: numpy.ndarray - Audio samples (any shape)

Returns:
- float - Normalized amplitude (0.0 to 1.0)

Example usage:
```python
import numpy as np
audio = np.array([0.1, -0.1, 0.05])
rms = recorder._calculate_rms(audio)  # Returns ~0.275
```

Edge cases:
- Empty array returns 0.0
- Very loud audio is clamped to 1.0
- Different dtypes are handled safely

Notes:
- Normalization uses 5x sensitivity factor
- Matches real-world mic sensitivity
```

**Why it works:**
- All tools understand structured doc requests
- Gives context without being verbose
- Clear examples prevent misunderstanding
- Works on all tools

---

## Code Review Pattern

**When:** Asking AI to review code quality.

**Template:**
```
Please review this code for:
1. Correctness - Does it do what it should?
2. Style - Does it match project conventions?
3. Error handling - Are errors handled properly?
4. Tests - Are there sufficient tests?
5. Performance - Any obvious inefficiencies?
6. Security - Any vulnerabilities?

Code to review:
```
[Paste code, up to 50 lines]
```

Context:
- This is in [file name]
- It handles [what it does]
- Project style: [Brief description of conventions]

What concerns me:
- [Your specific concern 1]
- [Your specific concern 2]

What should I pay attention to?
```

**Example:**
```
Please review this code for correctness, style, error handling, and tests:

Code to review:
```python
def save_context(self, context: str, max_context_length: int = 1000):
    temp_dir = self.config.get('temp_dir', './tmp')
    context_path = os.path.join(temp_dir, 'tmp-context.txt')
    truncated_context = context[-max_context_length:]
    with open(context_path, 'w') as f:
        f.write(truncated_context)
```

Context:
- In `src/[project-name]/core/processor.py` (or equivalent)
- Saves conversation history to temp file
- Project style: Type hints, docstrings, error handling for file ops

What concerns me:
- What if context is None?
- What if temp_dir doesn't exist?
- Should this be tested?

What should I pay attention to?
```

**Why it works:**
- Specific dimensions to review
- Shows your thinking
- All tools can do this
- Produces actionable feedback

---

## Refactoring Pattern

**When:** Making code cleaner without changing behavior.

**Template:**
```
I need to refactor [component] for [reason].

Current approach: [Brief description]
Problems with current:
- [Problem 1]
- [Problem 2]

Goals for refactoring:
- [ ] [Goal 1]
- [ ] [Goal 2]
- [ ] [Goal 3]

Constraints:
- Must not change external API
- Must pass all existing tests
- Must not reduce performance

Proposed changes:
1. [Change 1]
2. [Change 2]
3. [Change 3]

Is this a good refactoring? Any concerns?
```

**Example:**
```
I need to refactor AudioRecorder for readability and maintainability.

Current approach: All recording logic in one class with 170+ lines

Problems:
- __init__ has too many responsibilities
- start_recording has complex callback logic
- Resource cleanup spread across __del__ and stop_recording

Goals for refactoring:
- [ ] Separate concerns (recording, amplitude, file I/O)
- [ ] Reduce __init__ to 20 lines
- [ ] Clear resource lifecycle
- [ ] Easier to test in isolation

Constraints:
- Public API must not change
- All 24 tests must pass
- No performance regression

Proposed changes:
1. Extract amplitude calculation to AmplitudeCalculator class
2. Extract file I/O to AudioFileManager class
3. Create ResourceManager for cleanup
4. Keep AudioRecorder as facade

Is this a good refactoring? Any concerns?
```

**Why it works:**
- Clear goals prevent over-engineering
- Constraints prevent mistakes
- All tools understand this structure
- Works on all tools

---

## Testing Pattern

**When:** Writing new tests or fixing test failures.

**Template:**
```
I need to write a test for [component/function]:

What to test:
- [ ] [Behavior 1]
- [ ] [Behavior 2]
- [ ] [Error case 1]

Test file: [path]
Test framework: [pytest/unittest/etc]

Example inputs:
```python
[Show example inputs or fixtures]
```

Expected behavior:
```
[For each "what to test" item, describe expected output]
```

Dependencies to mock:
- [Dependency 1]
- [Dependency 2]

Anything tricky:
- [Edge case 1]
- [Any unusual setup needed]
```

**Example:**
```
I need to write tests for ConfigurationManager loading:

What to test:
- [ ] Loads defaults when no config file exists
- [ ] Merges file config with defaults
- [ ] Environment variables override file config
- [ ] Precedence: env > file > defaults

Test file: tests/test_config.py
Test framework: pytest

Example inputs:
```python
config = ConfigurationManager()
config_with_file = ConfigurationManager('/path/to/config.json')
```

Expected behavior:
- No file: All defaults are used
- With file: File values override defaults
- With env var: Env values override file
- All three: Env > file > defaults

Dependencies to mock:
- os.path.exists (to simulate missing files)
- os.environ (to set env variables)

Anything tricky:
- Config uses expanduser() for home dir
- Must mock pathlib.Path.mkdir to avoid creating real dirs
```

**Why it works:**
- Clear test structure
- Easy to verify completeness
- Shows mocking needs upfront
- Works on all tools

---

## Integration/System Pattern

**When:** Testing how components work together.

**Template:**
```
I need to write an integration test for [system]:

End-to-end flow:
1. [User action 1]
2. [System process 1]
3. [User action 2]
4. [System process 2]

Components involved:
- [Component 1] - [Brief role]
- [Component 2] - [Brief role]
- [Component 3] - [Brief role]

Success criteria:
- [ ] [Final state 1]
- [ ] [Final state 2]
- [ ] [No side effect violations]

What to mock:
- [External service 1]
- [External service 2]

What NOT to mock:
- [Internal component 1] - It should actually run
- [Internal component 2]

Failure scenarios to test:
- What if [failure 1]?
- What if [failure 2]?
```

**Example:**
```
I need to write integration tests for transcription + LLM pipeline:

End-to-end flow:
1. User provides audio file
2. Transcriber processes it (mocked [External API A])
3. Processor receives text
4. LLM processes text (mocked [External API B])
5. Result returned to user

Components involved:
- AIProcessor - Main orchestrator
- AudioRecorder - (mocked, file provided)
- [External API A] - (mocked, returns transcript)
- [External API B] - (mocked, returns response)

Success criteria:
- [ ] Transcript received from [External API A] mock
- [ ] LLM receives correct prompt
- [ ] Final response returned
- [ ] Context saved if requested

What to mock:
- [External API A] endpoint
- [External API B] endpoint

What NOT to mock:
- AIProcessor.transcribe()
- AIProcessor.process_text()

Failure scenarios:
- What if [External API A] returns error?
- What if [External API B] is unreachable?
- What if audio file is invalid?
```

**Why it works:**
- Shows full user journey
- Clear component boundaries
- Explicit mock/real divisions
- Failure modes documented

---

## Pattern Selection Guide

| Situation | Use Pattern |
|-----------|---|
| Starting any task | Request Analysis |
| Before coding | Planning & Design |
| Writing code | Implementation |
| After each step | Verification |
| Bugs appear | Debugging |
| Writing docs | Documentation |
| Code quality check | Code Review |
| Improving code | Refactoring |
| Unit tests | Testing |
| Multiple components | Integration |

---

## Multi-Pattern Tasks

Complex tasks often use multiple patterns:

```
Task: Add database migration system

1. Request Analysis Pattern
   → Understand requirements, clarify scope

2. Planning & Design Pattern
   → Design migration architecture

3. Implementation Pattern (repeated)
   → Create migration runner
   → Create migration templates
   → Add CLI commands

4. Testing Pattern (repeated)
   → Unit tests for migration runner
   → Integration tests for actual migrations

5. Documentation Pattern
   → Write migration guide
   → Document command syntax

6. Verification Pattern
   → Confirm all requirements met
   → Check acceptance criteria
```

---

## Tool-Specific Adaptations

These patterns work on all tools, but may look slightly different:

### Claude Code
- Use step numbers: "Next step:", "After this step:"
- Use tool names explicitly: "Read tool will show...", "Run: pytest"
- Use structured outputs (JSON, YAML)

### Aider
- Use conversational tone: "Let me test this...", "I'll create..."
- Ask for confirmation: "Should I proceed?"
- Use diffs naturally: Aider will show them

### Gemini/Codex
- Same as Claude Code (until tool-specific patterns emerge)
- May need simpler language
- Might need smaller examples

---

## Anti-Patterns to Avoid

**Don't do:**
```
❌ Vague requests: "Make it work"
❌ Implicit goals: "Fix the tests" (which tests? what's broken?)
❌ No context: "Add authentication" (what kind? where?)
❌ Mixed concerns: "Fix bug AND add feature AND refactor" (one at a time)
❌ No verification: "I'm done" (how do you know?)
```

**Do instead:**
```
✅ Clear requests with context and criteria
✅ Explicit goals and requirements
✅ Rich context (what, where, why)
✅ One concern per request
✅ Verification commands and expected output
```

---

## Creating Your Own Patterns

If you find yourself repeating a prompt structure:

1. Identify the **template structure** (what's common)
2. Identify **variable parts** (what changes per use)
3. Document with **before/after examples**
4. Get feedback on what works
5. Submit a PR to add to this guide

Good patterns are reusable across projects and tools.
