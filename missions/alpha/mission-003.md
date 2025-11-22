# Mission: Error Handling Integration

**Mission ID**: MISSION-003
**Feature Reference**: Feature-003 (Error Handling Integration)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/3
**Priority**: P1 (Critical path - needed for robust module loading)
**Status**: Active
**Estimated Complexity**: Simple
**Estimated Effort**: 1-2 hours

---

## Objective

Integrate the existing error handling strategies (retry decorators, circuit breaker) with the Application configuration system and prepare webhook notifications for critical errors. This feature ensures robust error handling is available for the upcoming module loading system (Feature-004).

**What exists**:
- ✅ Error decorators (`@with_retry`, `@with_circuit_breaker`) fully implemented in `strategies.py`
- ✅ WebhookNotifier class implemented in `webhook_notifier.py` with async HTTP support
- ✅ Configuration system operational (Feature-001 completed)
- ✅ Centralized logging operational (Feature-002 completed)

**What's needed**:
- Wire WebhookNotifier with Application
- Load webhook URL from configuration/environment variables
- Demonstrate error strategy usage with examples
- Integrate error notifications with logging

---

## Context

### Completed Dependencies

**Feature-001 (Configuration System)**: ✅ Completed (v0.2.0-alpha.1)
- Configuration loading from YAML files working
- Environment variable substitution operational
- Can load webhook URL from config/env

**Feature-002 (Centralized Logging)**: ✅ Completed (v0.3.0-alpha.1)
- Rotating file handlers configured
- Logger utilities ready
- Error messages can be logged centrally

### Current Implementation State

**Error Strategies** (`src/main_app/error_handling/strategies.py` - 167 lines):
- `@with_retry` decorator: Exponential backoff retry logic
- `@with_circuit_breaker` decorator: Circuit breaker pattern
- `ErrorStrategy.critical_operation()`: Combined retry + circuit breaker
- All using tenacity and pybreaker libraries
- **Status**: Production-ready, just needs configuration wiring

**WebhookNotifier** (`src/main_app/error_handling/webhook_notifier.py` - 174 lines):
- Async webhook notification via httpx
- Payload building with error context
- Enable/disable toggle
- **Status**: Implemented but not integrated with Application

**Configuration** (`config/main.yaml`):
```yaml
error_handling:
  retry_max_attempts: 3
  retry_wait_min: 1.0
  retry_wait_max: 10.0
  circuit_breaker_fail_max: 5
  circuit_breaker_reset_timeout: 60

webhooks:
  critical_errors_url: "${WEBHOOK_URL}"
```

---

## Specifications

### Input Requirements

1. **Configuration Files** (already exist):
   - `config/main.yaml` with error_handling and webhooks sections
   - `.env` with WEBHOOK_URL environment variable

2. **Existing Components**:
   - Application class with config loading
   - WebhookNotifier class
   - Error strategy decorators

### Output Deliverables

**Files to Modify**:
1. `src/main_app/error_handling/strategies.py` (optional: add usage examples in docstrings)
2. `src/main_app/error_handling/webhook_notifier.py` (wire with config)
3. `src/main_app/core/application.py` (integrate WebhookNotifier)

**Files to Create** (optional - for demonstration):
4. `examples/error_handling_demo.py` (demonstrate retry/circuit breaker usage)

**Functionality to Deliver**:
- WebhookNotifier initialized in Application with config URL
- Error strategies configurable from YAML (already supported by decorators)
- Critical errors logged AND sent via webhook
- Clear examples of decorator usage documented

---

## Acceptance Criteria

### Must Have

- [ ] **WebhookNotifier Integration**: Application initializes WebhookNotifier with webhook URL from config
- [ ] **Config Loading**: Webhook URL loaded from `config/main.yaml` (with env var substitution)
- [ ] **Error Strategy Docs**: Decorator usage documented with examples in docstrings
- [ ] **Example Code**: At least one example showing retry decorator usage
- [ ] **Example Code**: At least one example showing circuit breaker usage
- [ ] **Webhook Toggle**: WebhookNotifier can be enabled/disabled via config
- [ ] **Logging Integration**: Critical errors logged AND sent to webhook

### Nice to Have (Bonus)

- [ ] Comprehensive demo script showing all error patterns
- [ ] Integration test validating webhook payload
- [ ] Performance test for retry/circuit breaker overhead

---

## Implementation Tasks

### Task 1: Wire WebhookNotifier to Application (30 minutes)

**File**: `src/main_app/core/application.py`

**Actions**:
1. Import WebhookNotifier in Application class
2. In `Application.__init__()`, after loading config:
   - Get webhook URL from `self.config["webhooks"]["critical_errors_url"]`
   - Initialize WebhookNotifier with URL
   - Store as `self.webhook_notifier`
3. In `Application.start()`, enable webhook notifier if URL configured
4. In `Application.shutdown()`, disable webhook notifier

**Example Integration**:
```python
from ..error_handling.webhook_notifier import WebhookNotifier

class Application:
    def __init__(self, config_dir: Path = None):
        # ... existing config loading ...

        # Initialize webhook notifier
        webhook_url = self.config.get("webhooks", {}).get("critical_errors_url")
        self.webhook_notifier = WebhookNotifier(webhook_url=webhook_url)

        # ... existing component initialization ...

    def start(self):
        # ... existing startup ...

        # Enable webhook notifications if configured
        if self.webhook_notifier.webhook_url:
            self.webhook_notifier.enable()
            logger.info(f"Webhook notifications enabled: {self.webhook_notifier.webhook_url}")
```

### Task 2: Document Error Strategy Usage (20 minutes)

**File**: `src/main_app/error_handling/strategies.py`

**Actions**:
1. Enhance docstrings with configuration examples
2. Add usage examples showing config-driven parameters
3. Document when to use retry vs circuit breaker vs combined

**Example Documentation**:
```python
def with_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff.

    Usage with config:
        config = load_all_configs(Path("config"))
        retry_config = config["error_handling"]

        @with_retry(
            max_attempts=retry_config["retry_max_attempts"],
            wait_min=retry_config["retry_wait_min"],
            wait_max=retry_config["retry_wait_max"]
        )
        def flaky_operation():
            # Your code here
            pass

    Args:
        max_attempts: Maximum retry attempts
        wait_min: Minimum wait time between retries (seconds)
        wait_max: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to catch
    """
```

### Task 3: Create Error Handling Examples (30 minutes)

**File**: `examples/error_handling_demo.py` (NEW)

**Actions**:
1. Create examples directory if not exists
2. Write demo script showing:
   - Retry decorator with simulated failures
   - Circuit breaker with threshold triggering
   - Combined strategy (ErrorStrategy.critical_operation)
   - Webhook notification on critical error

**Demo Script Structure**:
```python
"""
Error Handling Demo - Showcases retry, circuit breaker, and webhook notifications.

Run: python -m examples.error_handling_demo
"""

from pathlib import Path
from main_app.config import load_all_configs
from main_app.error_handling import with_retry, with_circuit_breaker, ErrorStrategy
import random

# Load config
config = load_all_configs(Path("config"))
error_config = config["error_handling"]

# Example 1: Retry decorator
@with_retry(max_attempts=error_config["retry_max_attempts"])
def flaky_function():
    """Simulates a flaky operation that fails randomly."""
    if random.random() < 0.7:
        raise ConnectionError("Simulated connection failure")
    return "Success!"

# Example 2: Circuit breaker
breaker = CircuitBreaker(
    fail_max=error_config["circuit_breaker_fail_max"],
    reset_timeout=error_config["circuit_breaker_reset_timeout"]
)

@with_circuit_breaker(breaker)
def external_api_call():
    """Simulates external API call with failures."""
    raise TimeoutError("API timeout")

# Example 3: Combined strategy
@ErrorStrategy.critical_operation(
    max_attempts=3,
    fail_max=5,
    reset_timeout=60
)
def critical_operation():
    """Critical operation with both retry and circuit breaker."""
    # Your critical code here
    pass

if __name__ == "__main__":
    # Run demos...
```

### Task 4: Integration Testing (20 minutes)

**Manual Validation**:
1. Start Application and verify webhook notifier initialized
2. Check logs for webhook URL loading
3. Trigger critical error and verify webhook attempt logged
4. Test retry decorator with simulated failures
5. Test circuit breaker state transitions

---

## Implementation Constraints

### Code Organization
- Keep error handling code in `error_handling/` module
- Keep examples in separate `examples/` directory
- No new files in core (just modifications)

### ALPHA Constraints
- File size: All files < 1500 lines (current: well under)
- Focus: Make it work, demonstrate usage
- Tests: Manual testing acceptable
- Technical Debt: Can skip async webhook in demo (log only is OK)

### Technical Requirements
- Python 3.10+ async/await syntax
- Type hints on all new/modified functions
- Docstrings following Google style
- Error logging with `exc_info=True`

---

## Testing Requirements

### Test Specifications

**Manual Test 1: Webhook Configuration Loading**
```bash
# Set webhook URL
export WEBHOOK_URL="https://hooks.example.com/critical-errors"

# Start application
python -m main_app

# Expected logs:
# INFO: Config loaded: webhooks.critical_errors_url = https://hooks.example.com/critical-errors
# INFO: Webhook notifications enabled: https://hooks.example.com/critical-errors
```

**Manual Test 2: Retry Decorator**
```bash
# Run demo
python -m examples.error_handling_demo

# Expected output:
# Attempting flaky_function... (attempt 1/3)
# ConnectionError: Simulated connection failure
# Retrying in 1.2 seconds...
# Attempting flaky_function... (attempt 2/3)
# Success!
```

**Manual Test 3: Circuit Breaker**
```bash
# Run demo with circuit breaker test
# Expected output:
# Calling external_api_call... (1/5 failures)
# Calling external_api_call... (2/5 failures)
# ...
# Calling external_api_call... (5/5 failures)
# Circuit breaker OPEN - rejecting calls
```

### Validation Method

**Success Indicators**:
- Application starts without errors
- Webhook URL loaded from config
- Retry decorator retries up to max_attempts
- Circuit breaker opens after fail_max failures
- Critical errors logged with full context

**Integration Verification**:
- Check `logs/app.log` for webhook initialization
- Verify error strategies work with config parameters
- Confirm examples run without crashes

---

## Next Steps

### Upon Completion

1. **Archive Mission**: Move mission-003.md to `missions/archived/alpha/`
2. **Update Feature Status**: Mark Feature-003 as ✅ completed in `alpha-tasks/index.md`
3. **Version Bump**: Run `@version-manager` to bump version (v0.4.0-alpha.1)
4. **GitHub Update**: Update issue #3 with completion status
5. **Proceed to Feature-004**: Module Loading & Lifecycle Management

### Blocked Tasks

**These features depend on Feature-003 completion**:
- ✅ Feature-004 (Module Loading): Will use retry decorator for module load failures
- ✅ Feature-006 (Application Integration): Will use webhook notifier for critical app errors

---

## Files Reference

**Read These Files** (for context):
- `src/main_app/error_handling/strategies.py` (167 lines) - Existing decorators
- `src/main_app/error_handling/webhook_notifier.py` (174 lines) - Existing notifier
- `src/main_app/core/application.py` (124 lines) - Integration point
- `config/main.yaml` (error_handling + webhooks sections)

**Modify These Files**:
- `src/main_app/core/application.py` (add WebhookNotifier initialization)
- `src/main_app/error_handling/strategies.py` (enhance docstrings - optional)

**Create These Files** (optional):
- `examples/error_handling_demo.py` (demonstration script)

---

**Mission Ready**: This mission is ready for @code-implementer in Step A7.
**Context Budget**: ~150 lines (mission) + ~465 lines (3 source files) = 615 lines total
**ALPHA Compliance**: ✅ Feature-level scope, practical acceptance, manual testing OK
