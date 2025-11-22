# Feature-010: BaseModule Abstract Class

**Status**: 🚧 in-progress
**Type**: Developer Experience Enhancement
**Priority**: P2 (Medium)
**Complexity**: Medium
**Target Version**: v0.12.0-alpha.1
**GitHub Issue**: TBD (will create during mission planning)

---

## Overview

Create a `BaseModule` abstract class to standardize module construction and provide a clear, type-safe interface for module developers. This will improve developer experience, reduce boilerplate, and enforce best practices.

---

## Motivation

**Current State**:
- Modules implement interface functions (`initialize`, `shutdown`, `get_tests`) manually
- No type enforcement or IDE autocomplete guidance
- Repetitive boilerplate for threading, logging, config management
- No standard patterns for common module operations

**Desired State**:
- Abstract base class with clear contract
- Type hints for better IDE support
- Built-in helpers for common patterns (threading, logging, EventBus)
- Enforced implementation of required methods
- Reduced boilerplate code

---

## Objectives

### Primary Goals
1. Create `BaseModule` abstract class in `src/main_app/core/base_module.py`
2. Provide abstract methods: `on_initialize()`, `on_shutdown()`
3. Provide optional method: `get_tests()` with default implementation
4. Include built-in helpers for common patterns
5. Update existing dummy modules to use `BaseModule`
6. Update CLAUDE.md documentation with new usage pattern

### Success Criteria
- ✅ BaseModule class created with proper ABC inheritance
- ✅ Type hints and docstrings for all methods
- ✅ mod-dummy-producer refactored to use BaseModule
- ✅ mod-dummy-consumer refactored to use BaseModule
- ✅ Both modules still work correctly (validated with demo.py)
- ✅ CLAUDE.md updated with BaseModule usage examples
- ✅ No breaking changes to module loading system

---

## Technical Specification

### BaseModule Abstract Class

**File**: `src/main_app/core/base_module.py`

**Features**:
- Inherit from `abc.ABC` for proper abstract class behavior
- Abstract methods: `on_initialize()`, `on_shutdown()`
- Concrete methods: `initialize()`, `shutdown()`, `get_tests()`
- Built-in properties: `event_bus`, `config`, `logger`, `name`
- Helper methods: `start_background_thread()`, `stop_background_threads()`
- Automatic thread lifecycle management

**Interface**:
```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
import threading
import logging

class BaseModule(ABC):
    """Abstract base class for all modules."""

    def __init__(self):
        self._event_bus = None
        self._config = {}
        self._logger = None
        self._name = ""
        self._threads = []
        self._stop_event = threading.Event()

    @property
    def event_bus(self):
        """Get the EventBus instance."""
        return self._event_bus

    @property
    def config(self):
        """Get module configuration."""
        return self._config

    @property
    def logger(self):
        """Get module logger."""
        return self._logger

    @property
    def name(self) -> str:
        """Get module name."""
        return self._name

    def initialize(self, event_bus, config: dict) -> None:
        """
        Initialize the module (called by ModuleLoader).

        Args:
            event_bus: EventBus instance for pub/sub
            config: Module configuration from modules.yaml
        """
        self._event_bus = event_bus
        self._config = config
        self._name = config.get('name', self.__class__.__name__)
        self._logger = logging.getLogger(self._name)

        self.logger.info(f"Initializing {self.name}")
        self.on_initialize()

    @abstractmethod
    def on_initialize(self) -> None:
        """
        Module-specific initialization logic.

        This method is called after base initialization is complete.
        Override this method to implement your module's startup logic.
        """
        pass

    def shutdown(self) -> None:
        """
        Shutdown the module (called by ModuleLoader).

        Automatically stops all background threads and calls on_shutdown().
        """
        self.logger.info(f"Shutting down {self.name}")

        # Stop all background threads
        self._stop_event.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2)

        # Call module-specific shutdown
        self.on_shutdown()

        self.logger.info(f"{self.name} shutdown complete")

    @abstractmethod
    def on_shutdown(self) -> None:
        """
        Module-specific shutdown logic.

        Override this method to implement your module's cleanup logic.
        Background threads are already stopped before this is called.
        """
        pass

    def get_tests(self) -> list[str]:
        """
        Get list of test files for this module.

        Returns:
            list[str]: List of test file paths (relative to module directory)

        Override this method if your module has tests.
        """
        return []

    def start_background_thread(
        self,
        target: Callable,
        name: Optional[str] = None,
        daemon: bool = True
    ) -> threading.Thread:
        """
        Start a background thread with automatic lifecycle management.

        Args:
            target: Function to run in background thread
            name: Thread name (optional, defaults to function name)
            daemon: Whether thread should be daemon (default: True)

        Returns:
            threading.Thread: The started thread

        The thread will be automatically stopped during shutdown.
        """
        thread_name = name or target.__name__
        thread = threading.Thread(
            target=target,
            name=f"{self.name}.{thread_name}",
            daemon=daemon
        )
        self._threads.append(thread)
        thread.start()
        self.logger.debug(f"Started background thread: {thread_name}")
        return thread

    @property
    def is_stopping(self) -> bool:
        """Check if module is being stopped."""
        return self._stop_event.is_set()

    def wait_interruptible(self, timeout: float) -> bool:
        """
        Interruptible sleep that responds to shutdown signals.

        Args:
            timeout: Time to wait in seconds

        Returns:
            bool: True if interrupted, False if timeout completed
        """
        return self._stop_event.wait(timeout=timeout)
```

### Module Migration Pattern

**Before (mod-dummy-producer/__init__.py)**:
```python
import threading
import logging

_event_bus = None
_config = {}
_stop_event = threading.Event()
_publish_thread = None

logger = logging.getLogger(__name__)

def initialize(event_bus, config):
    global _event_bus, _config, _publish_thread
    _event_bus = event_bus
    _config = config
    logger.info("Initializing mod-dummy-producer")
    _publish_thread = threading.Thread(target=_publish_events, daemon=True)
    _publish_thread.start()

def shutdown():
    global _publish_thread
    logger.info("Shutting down mod-dummy-producer")
    _stop_event.set()
    if _publish_thread and _publish_thread.is_alive():
        _publish_thread.join(timeout=2)
```

**After (mod-dummy-producer/__init__.py)**:
```python
import time
from main_app.core.base_module import BaseModule

class DummyProducer(BaseModule):
    """Dummy producer module that publishes periodic events."""

    def __init__(self):
        super().__init__()
        self._event_counter = 0

    def on_initialize(self):
        """Start the producer thread."""
        self.start_background_thread(self._publish_events)

    def _publish_events(self):
        """Background thread that publishes events periodically."""
        publish_interval = self.config.get("publish_interval", 5)
        event_type = self.config.get("event_type", "test.ping")

        # Wait before first publish
        self.logger.info(f"Waiting {publish_interval}s before first publish...")
        self.wait_interruptible(timeout=publish_interval)

        while not self.is_stopping:
            self._event_counter += 1
            self.event_bus.publish(event_type, {
                "message": "hello from producer",
                "timestamp": time.time(),
                "counter": self._event_counter
            })
            self.logger.info(f"Published {event_type} event #{self._event_counter}")
            self.wait_interruptible(timeout=publish_interval)

    def on_shutdown(self):
        """Cleanup (threads already stopped by base class)."""
        self.logger.info("Producer cleanup complete")

# Module instance (required for ModuleLoader)
_module = DummyProducer()

# Interface functions (required for ModuleLoader compatibility)
def initialize(event_bus, config):
    _module.initialize(event_bus, config)

def shutdown():
    _module.shutdown()

def get_tests():
    return _module.get_tests()
```

---

## Benefits

### For Module Developers
- **Less Boilerplate**: No need to manually manage global state, threading, logger
- **Type Safety**: IDE autocomplete and type checking for all methods
- **Guided Development**: Abstract methods force implementation of required logic
- **Best Practices**: Built-in helpers encourage correct patterns
- **Simplified Threading**: Automatic thread lifecycle management

### For Main Application
- **No Breaking Changes**: Existing interface (`initialize`, `shutdown`, `get_tests`) unchanged
- **Better Maintainability**: Standardized module structure
- **Easier Testing**: Mock-friendly object-oriented design
- **Future Extensibility**: Easy to add new common features to base class

---

## Implementation Plan

### Phase 1: Core BaseModule Class
1. Create `src/main_app/core/base_module.py`
2. Implement BaseModule with abstract methods
3. Add built-in helpers (threading, logging, properties)
4. Add type hints and comprehensive docstrings

### Phase 2: Migrate Existing Modules
1. Update mod-dummy-producer to use BaseModule
2. Update mod-dummy-consumer to use BaseModule
3. Maintain backward compatibility (keep interface functions)

### Phase 3: Validation & Documentation
1. Run demo.py to validate both modules still work
2. Update CLAUDE.md with BaseModule usage guide
3. Add code examples showing before/after migration

---

## Testing Strategy (ALPHA - Manual Validation)

### Test Scenarios
1. **Module Loading**: Both modules load successfully
2. **EventBus Communication**: Producer publishes, consumer receives
3. **Thread Lifecycle**: Threads start and stop cleanly
4. **Graceful Shutdown**: Exit code 0 on Ctrl+C
5. **Logging**: Module logs appear with correct logger names

### Validation Command
```bash
cd main
python demo.py
```

**Expected Output**:
- ✅ All demo validation steps pass
- ✅ No errors in logs
- ✅ Clean exit (code 0 on manual Ctrl+C, code 1 on Windows proc.terminate())

---

## Files Modified

### New Files
- `src/main_app/core/base_module.py` (BaseModule class)

### Modified Files
- `modules-backend/mod-dummy-producer/__init__.py` (use BaseModule)
- `modules-backend/mod-dummy-consumer/__init__.py` (use BaseModule)
- `CLAUDE.md` (updated documentation)

---

## Risks & Mitigation

### Risk: Breaking Existing Modules
**Mitigation**: Keep interface functions (`initialize`, `shutdown`, `get_tests`) unchanged

### Risk: Performance Overhead
**Mitigation**: BaseModule is lightweight, minimal overhead from OOP design

### Risk: Complexity for Simple Modules
**Mitigation**: Still allow traditional function-based modules, BaseModule is optional

---

## Future Enhancements (Post-ALPHA)

Potential additions to BaseModule in BETA/PRODUCTION:
- Built-in health check method
- Automatic metrics collection
- Event subscription helpers with auto-unsubscribe
- Configuration validation (schema-based)
- Dependency injection for services

---

## Notes

- This is an **ALPHA feature** - focus on functionality over perfection
- BaseModule is **optional** - traditional function-based modules still supported
- **No breaking changes** to existing module loading system
- Migration path is **incremental** - can migrate modules one at a time

---

**Created**: 2025-11-22
**Workflow**: ALPHA
**Target Version**: v0.12.0-alpha.1
