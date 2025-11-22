# Feature-008: Dummy Modules for Validation

**Status**: 🎯 planned
**Scope**: Medium
**Complexity**: Low
**Priority**: P4 (Validation - proves the system works)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/8

---

## Description

Create two simple dummy modules (producer and consumer) that communicate via EventBus to validate the entire orchestration system. These modules serve as examples and testing tools to ensure module loading, event bus communication, and lifecycle management work correctly.

---

## Objectives

1. **Create Dummy Producer Module**
   - Create `../modules-backend/mod-dummy-producer/`
   - Implement `initialize(event_bus, config)` hook
   - Publish `test.ping` event periodically (configurable interval)
   - Include data payload: `{"message": "hello from producer", "timestamp": ...}`
   - Implement `shutdown()` hook to stop publishing

2. **Create Dummy Consumer Module**
   - Create `../modules-backend/mod-dummy-consumer/`
   - Implement `initialize(event_bus, config)` hook
   - Subscribe to `test.ping` event
   - Log received events with full data
   - Implement `shutdown()` hook to unsubscribe

3. **Add Module Tests**
   - Implement `get_tests()` in both modules
   - Create basic unit tests for each module
   - Test event publishing (producer)
   - Test event subscription (consumer)

4. **Configure Modules**
   - Add both modules to `config/modules.yaml`
   - Configure producer interval (5 seconds default)
   - Configure consumer event subscriptions
   - Both enabled by default

---

## Expected Outcomes

**Files Created**:
- `../modules-backend/mod-dummy-producer/__init__.py` (producer implementation)
- `../modules-backend/mod-dummy-producer/tests/test_producer.py` (producer tests)
- `../modules-backend/mod-dummy-consumer/__init__.py` (consumer implementation)
- `../modules-backend/mod-dummy-consumer/tests/test_consumer.py` (consumer tests)

**Files Modified**:
- `config/modules.yaml` (add module declarations)

**Functionality Delivered**:
- Producer publishes events periodically
- Consumer receives and logs events
- EventBus successfully delivers events between modules
- Module lifecycle hooks work correctly
- Test mode discovers and runs module tests

---

## Dependencies

**Upstream**:
- Feature-004 (Module Loading) - MUST be completed
- Feature-006 (Application Integration) - MUST be completed
- Feature-007 (Test Mode) - Recommended for full validation

**Downstream**:
- Feature-009 (Demo Scenario) uses these modules

---

## Acceptance Criteria

**Must Have**:
1. Producer module loads successfully
2. Consumer module loads successfully
3. Producer publishes `test.ping` event every 5 seconds (or configured interval)
4. Consumer receives `test.ping` events and logs them
5. Event data includes message and timestamp
6. Both modules implement `initialize()` and `shutdown()` hooks
7. Both modules implement `get_tests()` function
8. Both modules have basic unit tests
9. Modules configured in `modules.yaml`
10. Running `python -m main_app` shows producer/consumer communication in logs

**Nice to Have** (bonus, not required):
- Producer publishes multiple event types - **Skip in ALPHA**
- Consumer tracks event statistics - **Skip in ALPHA**
- Integration tests between producer/consumer - **Optional in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Module Loading**
```bash
python -m main_app
# Expected logs:
#   "Module 'mod-dummy-producer' loaded successfully"
#   "Module 'mod-dummy-producer' initialized"
#   "Module 'mod-dummy-consumer' loaded successfully"
#   "Module 'mod-dummy-consumer' initialized"
#   "Published event: module.loaded" (x2)
```

**Test Case 2: Event Bus Communication**
```bash
python -m main_app
# Expected logs (repeating every 5 seconds):
#   [Producer] "Publishing test.ping event"
#   [Consumer] "Received test.ping: {'message': 'hello from producer', 'timestamp': 1234567890}"
# Events flow: Producer → EventBus → Consumer
```

**Test Case 3: Configuration Respected**
```yaml
# config/modules.yaml
modules:
  - name: "mod-dummy-producer"
    config:
      publish_interval: 2  # Changed from 5 to 2 seconds
```
```bash
python -m main_app
# Expected: Events published every 2 seconds instead of 5
```

**Test Case 4: Graceful Shutdown**
```bash
python -m main_app
# Wait for a few events
# Press Ctrl+C
# Expected logs:
#   "Received signal 2"
#   [Producer] "Stopping event publisher"
#   "Module 'mod-dummy-producer' unloaded"
#   [Consumer] "Unsubscribing from events"
#   "Module 'mod-dummy-consumer' unloaded"
#   "Application shutdown complete"
# No errors or warnings
```

**Test Case 5: Test Mode**
```bash
python -m main_app --test
# Expected:
#   "Discovered tests from 'mod-dummy-producer': .../tests/"
#   "Discovered tests from 'mod-dummy-consumer': .../tests/"
#   pytest runs all tests
#   "X passed in Y.YYs"
#   Exit code 0
```

**Test Case 6: Hot-Reload (if Feature-005 completed)**
```bash
python -m main_app
# Modify producer message: "hello from producer" → "hello world"
# Save file
# Expected:
#   "Module 'mod-dummy-producer' reloaded successfully"
#   Next event shows new message: "hello world"
```

---

## Implementation Notes

**Producer Module Structure**:

```python
# modules-backend/mod-dummy-producer/__init__.py

import logging
import threading
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Module state
_publisher_thread = None
_stop_event = threading.Event()


def initialize(event_bus: Any, config: Dict[str, Any]) -> None:
    """
    Initialize producer module.

    Args:
        event_bus: EventBus instance for publishing events
        config: Module configuration from modules.yaml
    """
    global _publisher_thread, _stop_event

    logger.info("Initializing mod-dummy-producer")

    publish_interval = config.get("publish_interval", 5)
    event_type = config.get("event_type", "test.ping")

    def publish_events():
        """Background thread to publish events periodically."""
        counter = 0
        while not _stop_event.is_set():
            counter += 1
            data = {
                "message": "hello from producer",
                "timestamp": time.time(),
                "counter": counter
            }
            logger.info(f"Publishing {event_type} event #{counter}")
            event_bus.publish(event_type, data)

            # Sleep with interruptible wait
            _stop_event.wait(timeout=publish_interval)

    # Start publisher thread
    _stop_event.clear()
    _publisher_thread = threading.Thread(target=publish_events, daemon=True)
    _publisher_thread.start()

    logger.info(f"Producer initialized (interval={publish_interval}s, event={event_type})")


def shutdown() -> None:
    """Shutdown producer module."""
    global _publisher_thread, _stop_event

    logger.info("Shutting down mod-dummy-producer")

    # Stop publisher thread
    _stop_event.set()
    if _publisher_thread:
        _publisher_thread.join(timeout=2)

    logger.info("Producer shutdown complete")


def get_tests() -> list[str]:
    """Return test paths for --test mode."""
    return ["tests/"]
```

**Consumer Module Structure**:

```python
# modules-backend/mod-dummy-consumer/__init__.py

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Module state
_event_bus = None
_subscribed_events = []


def initialize(event_bus: Any, config: Dict[str, Any]) -> None:
    """
    Initialize consumer module.

    Args:
        event_bus: EventBus instance for subscribing to events
        config: Module configuration from modules.yaml
    """
    global _event_bus, _subscribed_events

    logger.info("Initializing mod-dummy-consumer")

    _event_bus = event_bus
    subscribe_events = config.get("subscribe_events", ["test.ping"])

    def handle_event(data: Any) -> None:
        """Handle received events."""
        logger.info(f"Received event: {data}")
        # In a real module, process the data here

    # Subscribe to configured events
    for event_type in subscribe_events:
        event_bus.subscribe(event_type, handle_event)
        _subscribed_events.append((event_type, handle_event))
        logger.info(f"Subscribed to event: {event_type}")

    logger.info(f"Consumer initialized (subscriptions: {len(subscribe_events)})")


def shutdown() -> None:
    """Shutdown consumer module."""
    global _event_bus, _subscribed_events

    logger.info("Shutting down mod-dummy-consumer")

    # Unsubscribe from all events
    for event_type, handler in _subscribed_events:
        if _event_bus:
            _event_bus.unsubscribe(event_type, handler)
            logger.info(f"Unsubscribed from event: {event_type}")

    _subscribed_events.clear()
    logger.info("Consumer shutdown complete")


def get_tests() -> list[str]:
    """Return test paths for --test mode."""
    return ["tests/"]
```

**Module Tests**:

```python
# modules-backend/mod-dummy-producer/tests/test_producer.py

import time
from unittest.mock import Mock
import sys
from pathlib import Path

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import __init__ as producer


def test_producer_publishes_events():
    """Test that producer publishes events."""
    mock_bus = Mock()
    config = {"publish_interval": 0.1, "event_type": "test.event"}

    # Initialize
    producer.initialize(mock_bus, config)

    # Wait for at least one event
    time.sleep(0.2)

    # Check event was published
    assert mock_bus.publish.called
    assert mock_bus.publish.call_args[0][0] == "test.event"

    # Shutdown
    producer.shutdown()


def test_producer_shutdown_stops_publishing():
    """Test that shutdown stops event publishing."""
    mock_bus = Mock()
    config = {"publish_interval": 0.1}

    producer.initialize(mock_bus, config)
    call_count_before = mock_bus.publish.call_count

    # Shutdown
    producer.shutdown()

    # Wait a bit
    time.sleep(0.3)

    # No new calls after shutdown
    assert mock_bus.publish.call_count == call_count_before
```

```python
# modules-backend/mod-dummy-consumer/tests/test_consumer.py

from unittest.mock import Mock
import sys
from pathlib import Path

# Add module to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import __init__ as consumer


def test_consumer_subscribes_to_events():
    """Test that consumer subscribes to configured events."""
    mock_bus = Mock()
    config = {"subscribe_events": ["test.ping", "test.pong"]}

    # Initialize
    consumer.initialize(mock_bus, config)

    # Check subscriptions
    assert mock_bus.subscribe.call_count == 2

    # Shutdown
    consumer.shutdown()


def test_consumer_unsubscribes_on_shutdown():
    """Test that consumer unsubscribes on shutdown."""
    mock_bus = Mock()
    config = {"subscribe_events": ["test.ping"]}

    consumer.initialize(mock_bus, config)
    consumer.shutdown()

    # Check unsubscribe called
    assert mock_bus.unsubscribe.called
```

**Configuration**:

```yaml
# config/modules.yaml
modules:
  - name: "mod-dummy-producer"
    path: "../modules-backend/mod-dummy-producer/__init__.py"
    enabled: true
    config:
      publish_interval: 5        # Publish event every 5 seconds
      event_type: "test.ping"    # Event type to publish

  - name: "mod-dummy-consumer"
    path: "../modules-backend/mod-dummy-consumer/__init__.py"
    enabled: true
    config:
      subscribe_events:          # Events to subscribe to
        - "test.ping"
```

---

## Rough Effort Estimate

**Time**: 3-4 hours (including testing)

**Breakdown**:
- Create producer module: 1 hour
- Create consumer module: 1 hour
- Create module tests: 1 hour
- Manual testing and validation: 1-2 hours

---

## Success Metrics

**Functional**:
- Producer and consumer communicate via EventBus
- Events published and received successfully
- Module lifecycle hooks work correctly
- Graceful shutdown with no errors
- Tests pass in test mode

**Quality**:
- Each module < 200 lines
- Clear, simple code (serves as example)
- Comprehensive logging
- Tests provide good coverage

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.5.0-alpha.1 or v0.6.0-alpha.1
**Previous Feature**: Feature-007 (Test Mode Implementation)
**Next Feature**: Feature-009 (Demo Scenario Execution)
