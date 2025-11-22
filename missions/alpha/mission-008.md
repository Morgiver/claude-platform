# Mission: Dummy Modules for Validation

**Mission ID**: MISSION-008
**Feature Reference**: Feature-008 (Dummy Modules for Validation)
**Priority**: P4 (Validation - proves the system works)
**Status**: Active
**Estimated Complexity**: Low
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/8

## Objective

Create two simple dummy modules (producer and consumer) that communicate via EventBus to validate the entire orchestration system works correctly. These modules serve as examples and testing tools to ensure module loading, event bus communication, lifecycle management, and test mode (Feature-007) function properly.

## Context

### Required Knowledge

**Completed Features**:
- Feature-001: Configuration System (config loading from YAML)
- Feature-002: Centralized Logging Setup
- Feature-003: Error Handling Integration
- Feature-004: Module Loading & Lifecycle Management (ModuleLoader with hot-reload)
- Feature-007: Test Mode Implementation (`--test` flag discovers and runs module tests)

**Module System Architecture**:
- Modules implement 3 hooks: `initialize(event_bus, config)`, `shutdown()`, `get_tests()`
- Modules receive EventBus instance and config dict during initialization
- ModuleLoader calls hooks during module lifecycle
- Test mode discovers tests via `get_tests()` function

**EventBus Pattern**:
- `event_bus.publish(event_type, data)` - publish event with data payload
- `event_bus.subscribe(event_type, handler)` - subscribe to event type
- `event_bus.unsubscribe(event_type, handler)` - unsubscribe from event

### Module Locations

**Producer Module**: `../modules-backend/mod-dummy-producer/`
**Consumer Module**: `../modules-backend/mod-dummy-consumer/`
**Configuration**: `config/modules.yaml` (add module declarations)

### Dependencies Met

- Feature-004 completed: Module loading and lifecycle management ready
- Feature-007 completed: Test mode implementation ready to discover module tests
- EventBus fully functional for pub/sub communication

## Specifications

### Input Requirements

**Producer Module Requirements**:
- Publish `test.ping` event periodically (configurable interval, default 5 seconds)
- Event payload: `{"message": "hello from producer", "timestamp": <unix_timestamp>, "counter": <int>}`
- Run publisher in background thread (daemon)
- Implement interruptible sleep using `threading.Event.wait(timeout=interval)`

**Consumer Module Requirements**:
- Subscribe to `test.ping` event (configurable via `subscribe_events` list)
- Log received events with full data payload
- Track event subscriptions for proper cleanup

**Module Tests Requirements**:
- Both modules must implement `get_tests()` returning `["tests/"]`
- Producer test: verify events published to mock EventBus
- Consumer test: verify subscriptions registered on mock EventBus
- Consumer test: verify unsubscribe called on shutdown

### Output Deliverables

**Files to Create**:
1. `../modules-backend/mod-dummy-producer/__init__.py` (~75 lines)
2. `../modules-backend/mod-dummy-producer/tests/test_producer.py` (~35 lines)
3. `../modules-backend/mod-dummy-consumer/__init__.py` (~65 lines)
4. `../modules-backend/mod-dummy-consumer/tests/test_consumer.py` (~30 lines)

**Files to Modify**:
1. `config/modules.yaml` - add producer and consumer module declarations

**Expected Functionality**:
- Producer publishes events every N seconds in background thread
- Consumer receives and logs events via EventBus
- Both modules implement lifecycle hooks correctly
- Test mode discovers and runs 4 tests (2 per module)
- Graceful shutdown stops publisher thread and unsubscribes consumer

### Acceptance Criteria

- [ ] Producer module created with `initialize()`, `shutdown()`, `get_tests()` hooks
- [ ] Producer publishes `test.ping` event periodically using background thread
- [ ] Producer uses `threading.Event` for interruptible sleep (clean shutdown)
- [ ] Consumer module created with `initialize()`, `shutdown()`, `get_tests()` hooks
- [ ] Consumer subscribes to configured events during initialization
- [ ] Consumer logs received event data with logger
- [ ] Consumer unsubscribes from all events during shutdown
- [ ] Producer tests verify event publishing to mock EventBus
- [ ] Consumer tests verify subscription/unsubscription on mock EventBus
- [ ] Both modules added to `config/modules.yaml` with appropriate configuration
- [ ] Running `python -m main_app` loads both modules and shows communication logs
- [ ] Running `python -m main_app --test` discovers and runs all 4 tests successfully
- [ ] Graceful shutdown (Ctrl+C) stops publisher and unsubscribes consumer without errors

## Implementation Constraints

### Code Organization

**Producer Module Structure**:
- File: `__init__.py` in `mod-dummy-producer/` directory
- Module-level globals: `_publisher_thread`, `_stop_event`
- Functions: `initialize()`, `shutdown()`, `get_tests()`, internal `publish_events()`
- Size limit: ~75 lines (simple and clean)

**Consumer Module Structure**:
- File: `__init__.py` in `mod-dummy-consumer/` directory
- Module-level globals: `_event_bus`, `_subscribed_events`
- Functions: `initialize()`, `shutdown()`, `get_tests()`, internal `handle_event()`
- Size limit: ~65 lines (simple and clean)

**Test Files Structure**:
- Test files: `test_producer.py`, `test_consumer.py` in respective `tests/` directories
- Use `unittest.mock.Mock` for EventBus mocking
- Each test file: 2-3 test functions
- Total size: ~30-35 lines per test file

### Technical Requirements

**Threading (Producer)**:
- Use `threading.Thread(target=..., daemon=True)` for background publishing
- Use `threading.Event()` for clean shutdown signaling
- Wait with timeout: `_stop_event.wait(timeout=publish_interval)`
- Join thread on shutdown: `_publisher_thread.join(timeout=2)`

**Event Subscription Tracking (Consumer)**:
- Store subscriptions: `_subscribed_events = [(event_type, handler), ...]`
- Iterate during shutdown to unsubscribe all handlers

**Configuration Access**:
- Get values with defaults: `config.get("publish_interval", 5)`
- Producer config keys: `publish_interval` (int), `event_type` (str)
- Consumer config keys: `subscribe_events` (list of str)

**YAML Configuration Format**:
```yaml
modules:
  - name: "mod-dummy-producer"
    path: "../modules-backend/mod-dummy-producer/__init__.py"
    enabled: true
    config:
      publish_interval: 5
      event_type: "test.ping"

  - name: "mod-dummy-consumer"
    path: "../modules-backend/mod-dummy-consumer/__init__.py"
    enabled: true
    config:
      subscribe_events:
        - "test.ping"
```

## Testing Requirements

### Test Specifications

**Producer Tests** (`test_producer.py`):
1. `test_producer_publishes_events()` - verify events published to mock EventBus
2. `test_producer_shutdown_stops_publishing()` - verify thread stops after shutdown

**Consumer Tests** (`test_consumer.py`):
1. `test_consumer_subscribes_to_events()` - verify subscribe called for each configured event
2. `test_consumer_unsubscribes_on_shutdown()` - verify unsubscribe called on shutdown

**Mock EventBus Pattern**:
```python
from unittest.mock import Mock

mock_bus = Mock()
# Test calls like: mock_bus.publish(...), mock_bus.subscribe(...)
# Verify with: assert mock_bus.publish.called
```

### Validation Method (Manual Testing)

**Test Case 1: Module Loading**
```bash
python -m main_app
# Expected: Both modules load and initialize successfully
# Logs: "Module 'mod-dummy-producer' initialized"
#       "Module 'mod-dummy-consumer' initialized"
```

**Test Case 2: Event Communication**
```bash
python -m main_app
# Expected: Producer publishes every 5 seconds, consumer receives and logs
# Logs: [Producer] "Publishing test.ping event #1"
#       [Consumer] "Received event: {'message': 'hello from producer', ...}"
```

**Test Case 3: Test Mode**
```bash
python -m main_app --test
# Expected: 4 tests discovered and passed
# Output: "Discovered tests from 'mod-dummy-producer': .../tests/"
#         "Discovered tests from 'mod-dummy-consumer': .../tests/"
#         "4 passed in X.XXs"
```

**Test Case 4: Graceful Shutdown**
```bash
python -m main_app
# Wait for events, then press Ctrl+C
# Expected: Clean shutdown with no errors
# Logs: [Producer] "Shutting down mod-dummy-producer"
#       [Consumer] "Shutting down mod-dummy-consumer"
```

## Next Steps

### Upon Completion

1. Update `documentation/alpha-tasks/feature-008.md` with completion timestamp
2. Update `documentation/alpha-tasks/index.md` status: 🎯 planned → ✅ completed
3. Archive mission file to `missions/alpha-archived/mission-008.md`
4. Proceed to Step A8 (Manual Validation & Debug) - run all 4 test cases above
5. Proceed to Step A9 (Feedback Checkpoint) - demo producer/consumer communication to user
6. Proceed to Step A10 (GitHub Issue Sync) - update issue #8 with completion status
7. Proceed to Step A11 (Version Bump) - bump to v0.9.0-alpha.1

### Blocked Features

**Feature-009** (Demo Scenario Execution) - will use these dummy modules for end-to-end demo
