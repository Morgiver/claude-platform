# Mission: Module Loading & Lifecycle Management

**Mission ID**: MISSION-004
**Feature Reference**: Feature-004 (Module Loading & Lifecycle Management)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/4
**Priority**: P2 (Core functionality - enables module system)
**Status**: Active
**Estimated Complexity**: Medium
**Estimated Effort**: 3-4 hours

---

## Objective

Wire the existing ModuleLoader into Application to enable declarative module loading from `config/modules.yaml`. Implement the module lifecycle interface (initialize/shutdown hooks) to inject EventBus into modules and manage their startup/shutdown sequences.

**What already works**:
- ✅ ModuleLoader class fully implemented (269 lines, load/unload/reload)
- ✅ Configuration system loading modules.yaml (Feature-001 completed)
- ✅ EventBus ready for injection (108 lines, thread-safe pub/sub)
- ✅ Error handling with retry decorators (Feature-003 completed)
- ✅ Centralized logging operational (Feature-002 completed)

**What's needed**:
- Wire module loading into Application.start()
- Call module.initialize(event_bus, config) after loading
- Call module.shutdown() during graceful application shutdown
- Publish lifecycle events (module.loaded, module.error)
- Isolate module failures (don't crash app)

---

## Context

### Completed Dependencies

**Feature-001 (Configuration System)**: ✅ Completed (v0.2.0-alpha.1)
- `config/modules.yaml` exists and can be loaded
- Configuration system reads YAML and substitutes env vars
- Application has access to loaded config via `self.config`

**Feature-002 (Centralized Logging)**: ✅ Completed (v0.3.0-alpha.1)
- Logger configured from config/main.yaml
- Logs written to `logs/app.log` with rotation
- Module lifecycle events can be logged

**Feature-003 (Error Handling Integration)**: ✅ Completed (v0.4.0-alpha.1)
- Retry decorators available (`@with_retry`)
- Circuit breaker available
- WebhookNotifier ready for critical errors
- Error strategies can wrap module loading

### Current Implementation State

**ModuleLoader** (`src/main_app/core/module_loader.py` - 269 lines):
- `load_module(config: ModuleConfig)` - Load single module ✅
- `load_modules(configs: List[ModuleConfig])` - Batch load ✅
- `unload_module(name: str)` - Unload module ✅
- `reload_module(name: str)` - Hot-reload module ✅
- `get_module(name: str)` - Retrieve loaded module ✅
- `get_loaded_modules()` - List all loaded modules ✅
- `shutdown()` - Clean shutdown ✅
- Hot-reload handler fully implemented with watchdog ✅

**Application** (`src/main_app/core/application.py` - 124 lines):
- `__init__()` - Initializes EventBus, ModuleLoader, ResourceManager ✅
- `start()` - Starts application, publishes app.started event ✅
- `shutdown()` - Graceful shutdown with signal handling ✅
- **Gap**: Does NOT load modules yet (integration needed)

**EventBus** (`src/main_app/core/event_bus.py` - 108 lines):
- Thread-safe pub/sub fully implemented ✅
- Error isolation in publish() ✅
- Ready for injection into modules ✅

**Configuration** (`config/modules.yaml`):
```yaml
modules: []
search_paths:
  - "../modules-backend"
```
Currently empty, but structure ready.

---

## Implementation Tasks

### Task 1: Load modules.yaml in Application (45 min)

**File to Modify**: `src/main_app/core/application.py`

**Actions**:
1. In `Application.start()`, after publishing app.started event:
   - Read `config/modules.yaml` via config loading
   - Parse modules list from YAML
   - Convert to `ModuleConfig` instances
   - Pass to ModuleLoader

2. Check if modules.yaml key exists in config
   - If missing, log warning and skip module loading
   - If empty list, log info and continue
   - If populated, proceed with loading

**Implementation Guidance**:
```python
def start(self) -> None:
    """Start the application."""
    logger.info("Starting application...")

    # Register signal handlers
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)

    # Log system resources
    resources = self.resource_manager.get_system_resources()
    logger.info(f"System resources: {resources}")

    # Publish startup event
    self.event_bus.publish("app.started", {"resources": resources})

    # Load modules from configuration
    modules_config = self.config.get("modules", [])
    if modules_config:
        self._load_modules(modules_config)
    else:
        logger.info("No modules configured, skipping module loading")

    self._running = True
    logger.info("Application started successfully")

    # Keep running
    self._run()
```

### Task 2: Implement _load_modules() method (60 min)

**File to Modify**: `src/main_app/core/application.py`

**Actions**:
1. Create new private method `_load_modules(modules_config: List[Dict])`
2. For each module configuration:
   - Create `ModuleConfig` instance
   - Skip disabled modules with log message
   - Load module via `self.module_loader.load_module(config)`
   - If successful, call module's initialize hook
   - Publish lifecycle events

3. Error handling:
   - Wrap module loading in try/except
   - Use retry decorator for transient failures
   - Log errors with full context
   - Publish module.error event
   - Continue loading other modules (isolation)

**Implementation Guidance**:
```python
def _load_modules(self, modules_config: List[Dict]) -> None:
    """
    Load modules from configuration.

    Args:
        modules_config: List of module configurations from modules.yaml
    """
    from .module_loader import ModuleConfig

    logger.info(f"Loading {len(modules_config)} modules...")

    for module_data in modules_config:
        config = ModuleConfig(
            name=module_data["name"],
            path=module_data["path"],
            enabled=module_data.get("enabled", True),
            config=module_data.get("config", {})
        )

        # Skip disabled modules
        if not config.enabled:
            logger.info(f"Module '{config.name}' is disabled, skipping")
            continue

        # Load module
        try:
            success = self.module_loader.load_module(config)

            if success:
                # Call initialize hook
                module = self.module_loader.get_module(config.name)
                if hasattr(module, "initialize"):
                    try:
                        module.initialize(self.event_bus, config.config)
                        logger.info(f"Module '{config.name}' initialized successfully")

                        # Publish success event
                        self.event_bus.publish("module.loaded", {
                            "name": config.name,
                            "path": config.path,
                            "config": config.config
                        })
                    except Exception as e:
                        logger.error(f"Failed to initialize module '{config.name}': {e}", exc_info=True)
                        self.event_bus.publish("module.error", {
                            "name": config.name,
                            "error": str(e),
                            "phase": "initialize"
                        })
                else:
                    logger.warning(f"Module '{config.name}' has no initialize() function")
            else:
                # Load failed
                logger.error(f"Failed to load module '{config.name}'")
                self.event_bus.publish("module.error", {
                    "name": config.name,
                    "error": "Module load failed",
                    "phase": "load"
                })
        except Exception as e:
            logger.error(f"Error loading module '{config.name}': {e}", exc_info=True)
            self.event_bus.publish("module.error", {
                "name": config.name,
                "error": str(e),
                "phase": "load"
            })
```

### Task 3: Integrate module shutdown (30 min)

**File to Modify**: `src/main_app/core/application.py`

**Actions**:
1. In `Application.shutdown()`, before clearing EventBus:
   - Call `self.module_loader.shutdown()`
   - This will trigger shutdown hooks in loaded modules

2. Enhance ModuleLoader.shutdown() to call module hooks
   - For each loaded module, check if it has `shutdown()` function
   - Call it and log results
   - Handle errors gracefully

**Implementation Guidance (Application.shutdown)**:
```python
def shutdown(self) -> None:
    """Shutdown application gracefully."""
    if not self._running:
        return

    logger.info("Shutting down application...")
    self._running = False

    # Publish shutdown event
    self.event_bus.publish("app.shutdown", {})

    # Shutdown modules (calls shutdown() hooks)
    logger.info("Shutting down modules...")
    self.module_loader.shutdown()

    # Clear event bus
    self.event_bus.clear()

    logger.info("Application shutdown complete")
```

**Implementation Guidance (ModuleLoader.shutdown enhancement)**:
```python
# In module_loader.py, enhance shutdown() method
def shutdown(self) -> None:
    """Shutdown module loader and all loaded modules."""
    logger.info(f"Shutting down {len(self._modules)} modules...")

    # Call shutdown hook on each module
    for name, module_data in self._modules.items():
        module = module_data["module"]
        if hasattr(module, "shutdown"):
            try:
                logger.info(f"Shutting down module '{name}'...")
                module.shutdown()
                logger.info(f"Module '{name}' shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down module '{name}': {e}", exc_info=True)
        else:
            logger.debug(f"Module '{name}' has no shutdown() hook")

    # Stop file observer
    if self._observer and self._observer.is_alive():
        self._observer.stop()
        self._observer.join(timeout=2)
        logger.info("File observer stopped")

    # Clear module registry
    self._modules.clear()
    logger.info("Module loader shutdown complete")
```

### Task 4: Manual Testing with Dummy Module (60 min)

**Test Setup**:
1. Create minimal dummy module for validation
2. Add to modules.yaml
3. Test load/initialize/shutdown cycle
4. Verify EventBus injection works
5. Verify lifecycle events published

**Dummy Module** (create temporarily at `../modules-backend/test-module/__init__.py`):
```python
"""Dummy test module for validating module loading."""
import logging

logger = logging.getLogger(__name__)

def initialize(event_bus, config):
    """
    Called by main/ when module loads.

    Args:
        event_bus: EventBus instance for pub/sub
        config: Module-specific config from modules.yaml
    """
    logger.info("Dummy module initializing...")

    # Subscribe to test event
    def handle_test(data):
        logger.info(f"Dummy module received test event: {data}")

    event_bus.subscribe("test.event", handle_test)

    # Publish ready event
    event_bus.publish("module.ready", {"module": "test-module"})

    logger.info("Dummy module initialized successfully")

def shutdown():
    """Called by main/ during shutdown."""
    logger.info("Dummy module shutting down...")
```

**Update modules.yaml**:
```yaml
modules:
  - name: "test-module"
    path: "../modules-backend/test-module/__init__.py"
    enabled: true
    config:
      test_setting: "test_value"
```

**Test Commands**:
```bash
# Test 1: Start application
python -m main_app

# Expected logs:
# INFO: Loading 1 modules...
# INFO: Module 'test-module' loaded successfully from ...
# INFO: Dummy module initializing...
# INFO: Dummy module initialized successfully
# INFO: Module 'test-module' initialized successfully
# INFO: Application started successfully

# Test 2: Verify EventBus injection
# In Application._run(), add temporary test publish:
self.event_bus.publish("test.event", {"message": "hello"})

# Expected log:
# INFO: Dummy module received test event: {'message': 'hello'}

# Test 3: Graceful shutdown
# Press Ctrl+C

# Expected logs:
# INFO: Shutting down application...
# INFO: Shutting down modules...
# INFO: Shutting down module 'test-module'...
# INFO: Dummy module shutting down...
# INFO: Module 'test-module' shutdown successfully
# INFO: Application shutdown complete
```

---

## Acceptance Criteria

**Must Have**:
- [ ] `modules.yaml` parsed and modules loaded at Application.start()
- [ ] Disabled modules (enabled: false) are skipped with log message
- [ ] `module.initialize(event_bus, config)` called after successful load
- [ ] EventBus instance injected into modules via initialize()
- [ ] Module-specific config passed to initialize()
- [ ] `module.shutdown()` called during Application.shutdown()
- [ ] EventBus publishes `module.loaded` event with module name and config
- [ ] EventBus publishes `module.error` event if module fails to load/initialize
- [ ] Module load failures are isolated (app continues with other modules)
- [ ] All lifecycle events logged with appropriate levels (INFO/ERROR)

**Nice to Have** (bonus, skip in ALPHA):
- [ ] Module dependency ordering (load A before B) - **Defer to BETA**
- [ ] Module health checks - **Defer to BETA**
- [ ] Retry failed module loads automatically - **Defer to BETA**

---

## Files to Create/Modify

### Modify:
1. **src/main_app/core/application.py** (Currently 124 lines)
   - Add `_load_modules()` method (~40 lines)
   - Update `start()` to call `_load_modules()` (~5 lines)
   - Update `shutdown()` to call module shutdown (~3 lines)
   - **Expected size**: ~170 lines (within 1500 line tolerance)

2. **src/main_app/core/module_loader.py** (Currently 269 lines)
   - Enhance `shutdown()` to call module hooks (~20 lines)
   - **Expected size**: ~290 lines (within tolerance)

### Create (Temporary - for testing only):
3. **../modules-backend/test-module/__init__.py** (NEW)
   - Minimal dummy module for validation (~20 lines)
   - **Delete after validation** or keep for future reference

4. **config/modules.yaml** (Already exists)
   - Add test-module configuration (~5 lines)
   - Can be cleared after testing

**Expected Total Changes**: ~70 lines of production code

---

## Implementation Constraints

### ALPHA Constraints:
- File size limit: 1500 lines (application.py will be ~170 lines ✅)
- Manual testing acceptable (no automated tests required)
- Prefer simplicity over completeness
- Focus on making it work, not making it perfect

### Code Quality:
- Use type hints for new methods
- Add docstrings following Google style
- Log all lifecycle events (module load, initialize, shutdown)
- Follow existing naming conventions (snake_case)

### Error Handling:
- Isolate module failures (try/except around each module load)
- Log errors with full stack trace (`exc_info=True`)
- Publish error events to EventBus
- Continue loading other modules if one fails
- Don't crash application on module errors

---

## Testing Requirements

### Manual Testing (Required):

**Test Case 1: Module Loading**
```bash
# Setup: Add test-module to modules.yaml
python -m main_app

# Expected:
# - Module loaded successfully
# - initialize() called
# - EventBus injected
# - Lifecycle events published
```

**Test Case 2: Disabled Module Skipped**
```yaml
# modules.yaml
modules:
  - name: "disabled-module"
    path: "../modules-backend/disabled-module/__init__.py"
    enabled: false
```
```bash
python -m main_app

# Expected:
# - Log: "Module 'disabled-module' is disabled, skipping"
# - Module NOT loaded
# - No initialize() call
```

**Test Case 3: Module Load Failure Isolated**
```yaml
# modules.yaml
modules:
  - name: "good-module"
    path: "../modules-backend/test-module/__init__.py"
    enabled: true
  - name: "bad-module"
    path: "../modules-backend/NONEXISTENT/__init__.py"
    enabled: true
```
```bash
python -m main_app

# Expected:
# - good-module loads successfully
# - bad-module fails with error log
# - module.error event published for bad-module
# - Application continues running with 1/2 modules
```

**Test Case 4: EventBus Communication**
```python
# In test-module initialize():
event_bus.subscribe("test.ping", lambda data: logger.info(f"Pong: {data}"))

# In Application._run() (temporary test):
self.event_bus.publish("test.ping", {"message": "hello"})
```
```bash
python -m main_app

# Expected:
# - test-module receives event
# - Log: "Pong: {'message': 'hello'}"
```

**Test Case 5: Graceful Shutdown**
```bash
python -m main_app
# Wait for startup to complete
# Press Ctrl+C

# Expected:
# - shutdown() called on all loaded modules
# - Logs show module shutdown sequence
# - Application exits cleanly
```

### Validation Method:
- Inspect `logs/app.log` for lifecycle events
- Verify module.loaded events published
- Verify module.error events for failures
- Check graceful shutdown logs
- Confirm application doesn't crash on module errors

---

## Dependencies

**Upstream**:
- Feature-001 (Configuration System) - ✅ COMPLETED (v0.2.0-alpha.1)
- Feature-003 (Error Handling Integration) - ✅ COMPLETED (v0.4.0-alpha.1)

**Downstream**:
- Feature-005 (Module Hot-Reload System) - Will enhance this
- Feature-006 (Application Integration) - Builds on this
- Feature-008 (Dummy Modules) - Will use this loading system

---

## Next Steps

### Upon Completion:
1. **Proceed to Step A8**: Manual Validation & Debug
2. **Update Feature-004 status**: Mark as "in-progress" → "completed"
3. **Prepare for Feature-005**: Hot-reload already implemented, just needs validation
4. **Clean up test module**: Remove temporary test-module or document for reuse

### Blocked Features Unblocked:
- Feature-005 (Module Hot-Reload) - Hot-reload code exists, just needs testing
- Feature-006 (Application Integration) - Will wire all components together
- Feature-008 (Dummy Modules) - Module loading foundation ready

---

## Notes

**Integration Points**:
- Application.start() → _load_modules() → ModuleLoader.load_module()
- Application.shutdown() → ModuleLoader.shutdown() → module.shutdown()
- ModuleLoader → EventBus injection → module.initialize(event_bus, config)

**Module Interface Contract** (must be documented for module developers):
```python
# Every module must implement:
def initialize(event_bus, config):
    """
    Called when module loads.

    Args:
        event_bus: EventBus instance for pub/sub
        config: Module-specific config from modules.yaml
    """
    pass

def shutdown():
    """Called when module unloads or app shuts down."""
    pass
```

**ALPHA Philosophy**:
- Get it working first (integration over perfection)
- Manual testing acceptable
- Defer advanced features (dependency ordering, health checks, auto-restart)
- Focus on core lifecycle (load → initialize → shutdown)

**Current State Reference**:
From `current-state.md`:
- ModuleLoader: 269 lines, 80% done (just needs calling)
- Application: 124 lines, orchestration ready
- EventBus: 108 lines, ready for injection
- Integration gap identified: "Components not wired together yet"

---

**Mission Created**: 2025-11-22
**Ready for @code-implementer**: Step A7 (Rapid Code Implementation)
**Workflow Version**: ALPHA
