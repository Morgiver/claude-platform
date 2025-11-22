# Mission 013: Implement BaseModule Abstract Class

**Feature**: Feature-010 - BaseModule Abstract Class
**Type**: Developer Experience Enhancement
**Status**: 🚧 in-progress
**Complexity**: Medium
**Started**: 2025-11-22

---

## Mission Objective

Implement a `BaseModule` abstract class that standardizes module construction and provides built-in helpers for common patterns (threading, logging, EventBus integration).

---

## Context

Currently, all modules implement the interface functions (`initialize`, `shutdown`, `get_tests`) manually with repetitive boilerplate. This mission creates a base class that:
- Provides a clear, type-safe contract for module developers
- Includes built-in helpers for threading and logging
- Reduces boilerplate code
- Enforces best practices through abstract methods

---

## Scope

### In Scope
- Create `BaseModule` abstract class in `src/main_app/core/base_module.py`
- Implement abstract methods: `on_initialize()`, `on_shutdown()`
- Provide concrete methods: `initialize()`, `shutdown()`, `get_tests()`
- Include built-in properties: `event_bus`, `config`, `logger`, `name`
- Add helper methods: `start_background_thread()`, `wait_interruptible()`, `is_stopping`
- Automatic thread lifecycle management
- Full type hints and docstrings

### Out of Scope
- Migrating existing modules (will be separate missions)
- Breaking changes to module loading system
- Advanced features (metrics, health checks) - defer to BETA

---

## Technical Requirements

### BaseModule Class Structure

**File**: `src/main_app/core/base_module.py`

**Required Components**:

1. **Imports**:
   - `abc.ABC`, `abc.abstractmethod` for abstract class
   - `threading` for thread management
   - `logging` for logger
   - `typing` for type hints

2. **Class Definition**:
   - Inherit from `abc.ABC`
   - Initialize internal state in `__init__()`

3. **Properties** (read-only):
   - `event_bus` - EventBus instance
   - `config` - Module configuration dict
   - `logger` - Logger instance for this module
   - `name` - Module name
   - `is_stopping` - Boolean flag for shutdown state

4. **Concrete Methods**:
   - `initialize(event_bus, config)` - Called by ModuleLoader
   - `shutdown()` - Called by ModuleLoader
   - `get_tests()` - Returns empty list by default
   - `start_background_thread(target, name, daemon)` - Helper for threading
   - `wait_interruptible(timeout)` - Interruptible sleep using Event

5. **Abstract Methods** (must be implemented by subclasses):
   - `on_initialize()` - Module-specific initialization
   - `on_shutdown()` - Module-specific cleanup

### Implementation Pattern

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
import threading
import logging


class BaseModule(ABC):
    """
    Abstract base class for all modules.

    Provides common functionality and enforces implementation of required methods.

    Example:
        class MyModule(BaseModule):
            def on_initialize(self):
                # Start background work
                self.start_background_thread(self._worker)

            def _worker(self):
                while not self.is_stopping:
                    # Do work
                    self.wait_interruptible(5)

            def on_shutdown(self):
                # Cleanup (threads already stopped)
                pass
    """

    def __init__(self):
        """Initialize base module state."""
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
    def config(self) -> dict:
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

    @property
    def is_stopping(self) -> bool:
        """Check if module is being stopped."""
        return self._stop_event.is_set()

    def initialize(self, event_bus, config: dict) -> None:
        """
        Initialize the module (called by ModuleLoader).

        This method sets up the base module infrastructure and then calls
        on_initialize() for module-specific setup.

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

        Use self.event_bus, self.config, self.logger as needed.
        Start background threads with self.start_background_thread().
        """
        pass

    def shutdown(self) -> None:
        """
        Shutdown the module (called by ModuleLoader).

        This method automatically stops all background threads and then
        calls on_shutdown() for module-specific cleanup.
        """
        self.logger.info(f"Shutting down {self.name}")

        # Stop all background threads
        self._stop_event.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2)
                if thread.is_alive():
                    self.logger.warning(
                        f"Thread {thread.name} did not stop within timeout"
                    )

        # Call module-specific shutdown
        self.on_shutdown()

        self.logger.info(f"{self.name} shutdown complete")

    @abstractmethod
    def on_shutdown(self) -> None:
        """
        Module-specific shutdown logic.

        This method is called after all background threads have been stopped.
        Override this method to implement your module's cleanup logic.

        Note: Background threads are already stopped before this is called.
        """
        pass

    def get_tests(self) -> list[str]:
        """
        Get list of test files for this module.

        Returns:
            list[str]: List of test file paths (relative to module directory)

        Override this method if your module has tests:
            def get_tests(self):
                return ['tests/test_my_module.py']
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

        The thread will be automatically stopped during module shutdown.

        Args:
            target: Function to run in background thread
            name: Thread name (optional, defaults to function name)
            daemon: Whether thread should be daemon (default: True)

        Returns:
            threading.Thread: The started thread

        Example:
            def on_initialize(self):
                self.start_background_thread(self._worker)

            def _worker(self):
                while not self.is_stopping:
                    # Do work
                    self.wait_interruptible(5)
        """
        thread_name = name or target.__name__
        full_name = f"{self.name}.{thread_name}"

        thread = threading.Thread(
            target=target,
            name=full_name,
            daemon=daemon
        )
        self._threads.append(thread)
        thread.start()
        self.logger.debug(f"Started background thread: {thread_name}")
        return thread

    def wait_interruptible(self, timeout: float) -> bool:
        """
        Interruptible sleep that responds immediately to shutdown signals.

        Use this instead of time.sleep() in loops to ensure responsive shutdown.

        Args:
            timeout: Time to wait in seconds

        Returns:
            bool: True if interrupted by shutdown, False if timeout completed

        Example:
            while not self.is_stopping:
                # Do work
                if self.wait_interruptible(10):
                    break  # Shutting down
        """
        return self._stop_event.wait(timeout=timeout)
```

---

## Implementation Steps

1. **Create File**: `src/main_app/core/base_module.py`

2. **Add Imports**:
   - `from abc import ABC, abstractmethod`
   - `from typing import Any, Callable, Optional`
   - `import threading`
   - `import logging`

3. **Implement BaseModule Class**:
   - Class definition with ABC inheritance
   - `__init__()` method
   - Properties (event_bus, config, logger, name, is_stopping)
   - Concrete methods (initialize, shutdown, get_tests)
   - Helper methods (start_background_thread, wait_interruptible)
   - Abstract methods (on_initialize, on_shutdown)

4. **Add Comprehensive Docstrings**:
   - Class docstring with example usage
   - Method docstrings with Args, Returns, Examples
   - Explain the pattern clearly for module developers

5. **Update core/__init__.py**:
   - Export BaseModule for easy import

---

## Constraints (ALPHA)

- **File Size**: Max 1500 lines (target: ~200 lines)
- **Complexity**: Keep it simple - no advanced features
- **Compatibility**: Must work with existing ModuleLoader
- **No Breaking Changes**: Existing modules should still work
- **Type Hints**: Use type hints for better IDE support
- **Docstrings**: Google-style docstrings for all public methods

---

## Success Criteria

- ✅ BaseModule class created with ABC inheritance
- ✅ All abstract methods defined (on_initialize, on_shutdown)
- ✅ All concrete methods implemented (initialize, shutdown, get_tests)
- ✅ All properties implemented (event_bus, config, logger, name, is_stopping)
- ✅ Helper methods implemented (start_background_thread, wait_interruptible)
- ✅ Full type hints on all methods
- ✅ Comprehensive docstrings with examples
- ✅ File size < 250 lines
- ✅ No syntax errors, imports work correctly
- ✅ Exported in core/__init__.py

---

## Testing Strategy (ALPHA - Manual)

**Validation**:
1. File imports without errors
2. Can create a test subclass that implements abstract methods
3. Type checking passes (if using mypy)
4. Will be fully validated when dummy modules are migrated

---

## Notes

- This is a **foundation** for future module development
- **Backward compatible** - doesn't break existing modules
- **Optional** - modules can still use traditional function-based approach
- Focuses on **developer experience** and **reducing boilerplate**

---

## Related Files

**Created**:
- `src/main_app/core/base_module.py` (new)

**Modified**:
- `src/main_app/core/__init__.py` (export BaseModule)

---

**Mission Created**: 2025-11-22
**Workflow**: ALPHA
**Target Version**: v0.12.0-alpha.1
