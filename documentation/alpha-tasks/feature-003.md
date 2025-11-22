# Feature-003: Error Handling Integration

**Status**: 🎯 planned
**Scope**: Small
**Complexity**: Low
**Priority**: P1 (Critical path - needed for robust module loading)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/3

---

## Description

Integrate the existing error handling strategies (retry decorators, circuit breaker) into the application configuration and ensure they're ready for use in module loading and event bus operations.

---

## Objectives

1. **Configure Error Strategies**
   - Load retry and circuit breaker settings from `config/main.yaml`
   - Make decorators configurable (currently hardcoded defaults)
   - Add configuration to Application initialization

2. **Test Error Strategies**
   - Validate retry decorator with exponential backoff
   - Validate circuit breaker state transitions
   - Document usage patterns for module developers

3. **Prepare Webhook Notifier** (Basic skeleton only)
   - Create basic webhook notification function (not fully implemented)
   - Use config for webhook URL
   - Log critical errors (actual webhook sending is bonus)

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/error_handling/strategies.py` (make configurable from dict)
- `src/main_app/error_handling/webhook_notifier.py` (load webhook URL from config)

**Functionality Delivered**:
- Retry decorator accepts config parameters
- Circuit breaker accepts config parameters
- Error strategies use config from `main.yaml`
- Webhook URL loaded from config (function skeleton ready, actual sending optional)
- Clear examples of how to use decorators in code

---

## Dependencies

**Upstream**: Feature-001 (Configuration System) - MUST be completed first
**Downstream**: Feature-004 (Module Loading) will use these strategies

---

## Acceptance Criteria

**Must Have**:
1. `with_retry()` decorator accepts config dict for max_attempts, wait times
2. `CircuitBreaker` class accepts config dict for fail_max, reset_timeout
3. Error handling config loaded from `config/main.yaml`
4. Existing strategies work with default values if config not provided
5. Webhook notifier loads URL from config (skeleton function, actual sending optional)

**Nice to Have** (bonus, not required):
- Actual webhook sending implementation - **Optional in ALPHA**
- Async retry support - **Skip in ALPHA**
- Custom exception handling per module - **Skip in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Retry Decorator with Config**
```python
# Create test script
from main_app.error_handling import with_retry
from main_app.config import load_all_configs

config = load_all_configs(Path("config"))
error_config = config["error_handling"]

@with_retry(max_attempts=error_config["retry_max_attempts"])
def flaky_function():
    import random
    if random.random() < 0.7:
        raise ConnectionError("Simulated failure")
    return "Success"

# Run multiple times
# Expected: Retries up to 3 times with exponential backoff
```

**Test Case 2: Circuit Breaker with Config**
```python
from main_app.error_handling import CircuitBreaker

config = load_all_configs(Path("config"))
breaker = CircuitBreaker(
    fail_max=config["error_handling"]["circuit_breaker_fail_max"],
    reset_timeout=config["error_handling"]["circuit_breaker_reset_timeout"]
)

def call_external_api():
    # Simulate failures
    raise TimeoutError("API timeout")

# Call until circuit opens
# Expected: Circuit opens after 5 failures, rejects calls
# Wait 60 seconds
# Expected: Circuit moves to half-open, accepts test call
```

**Test Case 3: Webhook Configuration**
```python
from main_app.error_handling.webhook_notifier import notify_critical_error

config = load_all_configs(Path("config"))
# Check webhook URL loaded from config
# Expected: URL is from config/main.yaml or .env substitution
```

---

## Implementation Notes

**Current State**:
- `strategies.py` has decorators with hardcoded defaults
- `webhook_notifier.py` exists but may be skeleton only

**Enhancement Needed**:

**strategies.py**:
```python
def with_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator with exponential backoff.

    Can be configured from config dict:
        config = load_all_configs(...)
        retry_config = config["error_handling"]

        @with_retry(
            max_attempts=retry_config["retry_max_attempts"],
            wait_min=retry_config["retry_wait_min"],
            wait_max=retry_config["retry_wait_max"]
        )
        def my_function():
            pass
    """
    # Existing implementation, just add docstring and defaults from config
    pass

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Can be configured from config dict:
        config = load_all_configs(...)
        breaker = CircuitBreaker(
            fail_max=config["error_handling"]["circuit_breaker_fail_max"],
            reset_timeout=config["error_handling"]["circuit_breaker_reset_timeout"]
        )
    """
    pass
```

**webhook_notifier.py** (Basic skeleton):
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def notify_critical_error(
    error_message: str,
    context: Dict[str, Any],
    webhook_url: str | None = None
) -> None:
    """
    Send critical error notification via webhook.

    Args:
        error_message: Error description
        context: Additional context (module name, stack trace, etc.)
        webhook_url: Webhook URL (from config)

    Note:
        ALPHA: Logs error, actual webhook sending is optional bonus
    """
    # Log the error
    logger.critical(f"Critical error: {error_message}", extra=context)

    # ALPHA: Actual webhook sending is optional
    if webhook_url:
        logger.info(f"Would send webhook to: {webhook_url}")
        # TODO BETA: Implement actual HTTP POST
        # import httpx
        # response = httpx.post(webhook_url, json={...})
```

**Config Usage**:
From `config/main.yaml`:
```yaml
error_handling:
  retry_max_attempts: 3
  retry_wait_min: 1.0       # seconds
  retry_wait_max: 10.0      # seconds
  circuit_breaker_fail_max: 5
  circuit_breaker_reset_timeout: 60  # seconds

webhooks:
  critical_errors_url: "${WEBHOOK_URL}"  # From .env
```

**Usage Examples** (Document in docstrings):
```python
# Example 1: Retry on module load failure
from main_app.error_handling import with_retry

@with_retry(max_attempts=3, exceptions=(ImportError, FileNotFoundError))
def load_module(path):
    # Load module from path
    pass

# Example 2: Circuit breaker for external API
from main_app.error_handling import CircuitBreaker

api_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

def call_external_api():
    with api_breaker:
        # Make API call
        pass
```

---

## Rough Effort Estimate

**Time**: 1-2 hours (including testing)

**Breakdown**:
- Document decorator configuration: 15 minutes
- Enhance webhook_notifier skeleton: 30 minutes
- Create test examples: 30 minutes
- Manual testing: 30-45 minutes

---

## Success Metrics

**Functional**:
- Retry decorator configurable from config
- Circuit breaker configurable from config
- Webhook URL loaded from config
- Error strategies work with defaults if config missing

**Quality**:
- Clear documentation in docstrings
- Usage examples documented
- Code follows project conventions
- No breaking changes to existing code

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.1.0-alpha.1
**Previous Feature**: Feature-002 (Centralized Logging Setup)
**Next Feature**: Feature-004 (Module Loading & Lifecycle Management)
