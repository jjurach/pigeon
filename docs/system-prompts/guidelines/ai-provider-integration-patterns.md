# AI Provider Library Integration Patterns: Observed Failure Modes & Self-Healing Guidance

**Purpose:** Document real failure patterns encountered during AI provider library integration across multiple modules (module-a, module-b, module-c) and provide targeted guidance to prevent recurrence.

**Basis:** Synthesized from Phase 1-8 library development and integration documentation (proj-xxx, proj-yyy, proj-zzz, proj-aaa).

**Status:** Self-healing prompt based on observed integration experience

---

## 1. Global Config State Management

### Observed Failure

**Pattern:** Multiple modules initialize `ai_provider_lib.get_config()` with different config chains, leading to unpredictable credential resolution and provider availability.

**Example from module-a Phase 3:**
```python
# Module A initializes global config
config = get_config(config_chain=['/path/to/moduleA/config.yaml', ai_provider_lib_config_path])

# Later, Module B needs config but gets Module A's cached version
# Different credential priority means Module B sees wrong keys/timeouts
```

**Impact:** Credentials work in one context, fail silently in another. Fallback chains break unexpectedly.

### Self-Healing Guidance

**✅ DO:**
- Call `get_config(config_chain=[...])` exactly once per application lifecycle, at initialization
- Document the config chain order in module-specific docstrings
- Include fallback paths explicitly: app-specific settings FIRST, then shared ai-provider-lib config
- For library modules, defer config initialization to the calling application (don't call `get_config()` at module import time)

**Example:**
```python
# In AIProcessor.__init__()
from ai_provider_lib import SyncProviderClient, get_config

# Set up global config ONCE, with clear chain order
if not hasattr(AIProcessor, '_provider_configured'):
    get_config(config_chain=[
        '~/.config/mymodule/settings.json',  # App-specific first
        '~/.config/ai-provider-lib/config.yaml'          # Fallback to shared library
    ])
    AIProcessor._provider_configured = True

# Now SyncProviderClient uses this global config
self.client = SyncProviderClient()
```

**Documentation requirement:** Add a comment explaining why config chain order matters and what each entry provides.

---

## 2. Provider Availability Checking & Graceful Degradation

### Observed Failure

**Pattern:** AI provider library returns `None` when credentials are missing rather than raising exceptions. Consuming code doesn't check for `None`, assuming provider initialization always succeeds.

**Example from module-b integration:**
```python
# Assumed this always returns a provider
provider = get_provider('groq')
text = provider.transcribe(audio_file)  # ❌ AttributeError if provider is None
```

**Impact:** Silent `NoneType` errors at runtime. Provider fallback chains don't trigger because the chain never started.

### Self-Healing Guidance

**✅ DO:**
- Always check `provider is not None` before calling methods
- Implement explicit fallback chains for providers
- Log which providers are available vs unavailable at startup
- Use `provider.is_available()` property before attempting operations

**Example:**
```python
def transcribe_with_fallback(audio_file):
    """Transcribe using available STT providers, with fallback chain."""
    providers_to_try = ['groq', 'local_whisper']

    for provider_name in providers_to_try:
        provider = get_provider(provider_name)

        if provider is None:
            logger.info(f"STT provider '{provider_name}' not available (missing credentials)")
            continue

        if not provider.is_available():
            logger.info(f"STT provider '{provider_name}' configured but not accessible")
            continue

        try:
            result = provider.transcribe(audio_file)
            logger.info(f"Transcription succeeded using {provider_name}")
            return result
        except Exception as e:
            logger.warning(f"Transcription failed with {provider_name}: {e}")
            continue

    logger.error("All STT providers exhausted without successful transcription")
    return None
```

---

## 3. Test Mocking: Abstraction Layers & HTTP Interception

### Observed Failure

**Pattern:** Tests use `requests_mock` to mock raw HTTP calls. When code is refactored to use ai-provider-lib (which abstracts HTTP), the mocks don't intercept, tests fail with actual API calls or 404s.

**Example from module-a tests:**
```python
# Old test (working)
@requests_mock.Mocker()
def test_transcribe(m):
    m.post('http://localhost:9000/transcribe', json={'text': 'hello'})
    result = _transcribe_local_whisper('audio.wav')
    assert result == 'hello'

# After ai-provider-lib integration, same test fails because:
# - ai-provider-lib wraps the HTTP call
# - requests_mock sees SyncProviderClient's HTTP call, not the raw one
# - Mock expectations don't match library's exact request format
```

**Impact:** 9 out of 232 tests fail after library integration. Test suite doesn't catch regression during integration work.

### Self-Healing Guidance

**✅ DO:**
- After integrating ai-provider-lib, update mocks to target library's HTTP layer
- Create fixture factories for provider implementations (mock implementations)
- Test provider interfaces, not HTTP details
- Separate unit tests (mock providers) from integration tests (real providers)

**Example:**
```python
# fixtures.py - reusable mock providers
@pytest.fixture
def mock_local_whisper_provider():
    """Mock LocalWhisperProvider for testing."""
    from unittest.mock import Mock
    from ai_provider_lib import STTResponse

    provider = Mock()
    provider.is_available.return_value = True
    provider.name = "local_whisper"
    provider.transcribe.return_value = STTResponse(
        text="mock transcription",
        language="en",
        duration=1.5,
        provider="local_whisper"
    )
    return provider

# test_processor.py - using mock providers
def test_transcribe_with_mock(mock_local_whisper_provider, monkeypatch):
    """Test transcription without touching real API."""
    from mymodule.core.processor import AIProcessor
    from ai_provider_lib import get_provider

    # Replace get_provider globally
    monkeypatch.setattr('ai_provider_lib.get_provider',
                       lambda name: mock_local_whisper_provider if name == 'local_whisper' else None)

    processor = AIProcessor()
    result = processor._transcribe_local_whisper('test.wav')
    assert result == "mock transcription"
```

**Documentation requirement:** Update test README with before/after patterns for HTTP mocking -> provider mocking migration.

---

## 4. Config Chain & Credential Priority Resolution

### Observed Failure

**Pattern:** Modules don't understand ai-provider-lib's credential resolution priority. They expect credentials in a specific file location, but library checks ENV > keyring > config file. Code passes one credential but library uses a different one from the chain.

**Example from Phase 5 implementation:**
```
Expected flow:
1. App sets GROQ_API_KEY env var
2. Code uses that key

Actual ai-provider-lib flow:
1. Check GROQ_API_KEY (found, use it) ✓
2. If not found, check system keyring
3. If not found, check ~/.config/ai-provider-lib/config.yaml
4. If not found, return None and provider is unavailable
```

**Impact:** Developers can't predict which credential will be used. Testing becomes flaky (env vs keyring vs file conflicts).

### Self-Healing Guidance

**✅ DO:**
- Document ai-provider-lib's credential priority chain in every module that uses it
- Provide clear setup instructions: "Set GROQ_API_KEY or add credentials to ~/.config/ai-provider-lib/config.yaml"
- In tests, explicitly set only ONE credential source to avoid confusion
- Add debug logging: "Using credential source: env|keyring|config"

**Example:**
```python
# In module documentation
"""
AI Provider Library Credentials

ai-provider-lib resolves credentials in this priority order:
1. Environment variable (e.g., GROQ_API_KEY, LOCAL_WHISPER_URL)
2. System keyring (if configured)
3. Config file (~/.config/ai-provider-lib/config.yaml)

To use Groq STT:
  export GROQ_API_KEY="sk-..."

To use LocalWhisper:
  export LOCAL_WHISPER_URL="http://localhost:9000"
  export LOCAL_WHISPER_TIMEOUT="30"

To verify credentials are detected:
  python -m ai_provider_lib health-check
"""

# In code
from ai_provider_lib import ProviderManager
manager = ProviderManager()
provider = manager.get_stt_provider('groq')

if provider and provider.is_available():
    logger.debug(f"Groq provider initialized and available")
else:
    logger.warning("Groq provider not available - check GROQ_API_KEY env var or ~/.config/ai-provider-lib/config.yaml")
```

---

## 5. Subprocess Lifecycle & Timeout Management

### Observed Failure

**Pattern:** When ai-provider-lib or other agents are spawned as subprocesses, timeout handling varies. 5-minute timeout may be too short for complex tasks, or too long for quick checks.

**Example from module-c Epic 2:**
```python
# 5-minute timeout set globally
process = subprocess.Popen(cmd, timeout=300)
# Task takes 6 minutes -> process killed mid-execution
# No graceful shutdown, partial state left behind
```

**Impact:** Long-running library tasks (batch transcriptions, multiple provider health checks) timeout unexpectedly.

### Self-Healing Guidance

**✅ DO:**
- Make timeouts configurable, not hardcoded
- Document why a specific timeout is chosen (based on expected workload)
- Implement graceful shutdown: send SIGTERM, wait, then SIGKILL
- Log timeout events with context (task type, elapsed time, resources used)
- For ai-provider-lib: implement per-operation timeouts, not global timeouts

**Example:**
```python
# config.yaml
providers:
  groq:
    transcribe_timeout: 60  # Groq STT typically takes 5-30s
    health_check_timeout: 5  # Health check should be quick
  local_whisper:
    transcribe_timeout: 300  # Local processing can take longer
    health_check_timeout: 2

# Code
from ai_provider_lib import get_config
config = get_config()
timeout = config.providers['groq'].get('transcribe_timeout', 60)

try:
    result = provider.transcribe(audio_file, timeout=timeout)
except TimeoutError as e:
    logger.error(f"Transcription timed out after {timeout}s: {e}")
    # Implement fallback (try different provider, skip, etc.)
```

---

## 6. Per-Source Error Isolation in Multi-Provider Scenarios

### Observed Failure

**Pattern:** When multiple providers are available (Groq + LocalWhisper), a failure in one provider's health check or transcription breaks the entire fallback chain rather than moving to the next provider.

**Example:**
```python
providers = ['groq', 'local_whisper', 'azure_stt']
for provider_name in providers:
    provider = get_provider(provider_name)
    if not provider:
        continue  # Missing credentials, try next
    try:
        return provider.transcribe(audio_file)
    except RequestException:
        # ❌ BUG: Don't continue, just raise
        raise  # Should log and continue to next provider
```

**Impact:** First provider error stops the chain, never tries fallbacks.

### Self-Healing Guidance

**✅ DO:**
- Catch and log exceptions per provider, don't re-raise immediately
- Continue to next provider after any failure
- Accumulate error context from all providers (useful for debugging)
- Return detailed error info if ALL providers fail

**Example:**
```python
def transcribe_with_all_providers(audio_file):
    """Attempt transcription with all available providers."""
    providers_to_try = ['groq', 'local_whisper', 'azure_stt']
    errors = {}

    for provider_name in providers_to_try:
        provider = get_provider(provider_name)

        if not provider:
            errors[provider_name] = "Not configured (missing credentials)"
            continue

        try:
            logger.info(f"Attempting transcription with {provider_name}")
            result = provider.transcribe(audio_file)
            logger.info(f"✓ Transcription succeeded with {provider_name}")
            return result
        except (RequestException, TimeoutError) as e:
            error_msg = f"API error: {e}"
            logger.warning(f"✗ {provider_name} failed: {error_msg}")
            errors[provider_name] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {e}"
            logger.warning(f"✗ {provider_name} failed: {error_msg}")
            errors[provider_name] = error_msg

    # All providers exhausted
    logger.error(f"All STT providers failed: {errors}")
    return None  # Or raise with detailed error context
```

---

## Integration Checklist

When integrating ai-provider-lib into a new module, verify:

- [ ] Config chain initialized once at module load, documented with priority order
- [ ] All provider access wrapped in `is None` and `is_available()` checks
- [ ] Test suite updated: old HTTP mocks replaced with provider mocks
- [ ] Fallback chains implemented for critical providers (not just "try one")
- [ ] Timeout values documented and configurable per provider/operation
- [ ] Per-provider error isolation: failures don't cascade to block other providers
- [ ] Credentials documented: which env vars, config file locations, keyring usage
- [ ] Debug logging added for provider selection and credential resolution
- [ ] Documentation updated: setup instructions, credential priority, troubleshooting

---

## Examples by Module

### module-a Phase 3 (STT Integration)
- ✅ Config chain in AIProcessor.__init__()
- ✅ Global config set once
- ⚠️ Tests need updating (9 tests failing due to mock mismatch)
- ✅ Fallback to None documented in code

**Next:** Update tests to mock providers instead of HTTP

### module-b integration
- ✅ Uses ai-provider-lib imports
- ⚠️ No null check before provider.transcribe()
- ⚠️ No fallback chain if provider fails

**Next:** Add null checks and fallback to alternative providers

### module-c Epic 2 (Provider Abstraction)
- ✅ Per-source error isolation pattern used
- ✅ Clear subprocess timeout (5 minutes) set
- ⚠️ No graceful shutdown (SIGTERM before SIGKILL)

**Next:** Add graceful process shutdown, make timeout configurable

---

## Related Documentation

- **[Tool Reliability & Fallback Mechanisms](./tool-reliability.md)** — Dual-tier architecture patterns
- **[Multi-Project Error Handling](./multi-project-error-handling.md)** — Per-source error isolation
- **[Self-Healing System Prompts](../principles/self-healing.md)** — How to update these docs

---

**Last Updated:** 2026-02-22
**Basis:** Synthesis of ai-provider-lib Phases 1-8 change documentation and real integration patterns
**Status:** Active ✓ — Guides future library integrations across all modules
