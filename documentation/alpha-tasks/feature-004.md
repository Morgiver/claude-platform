# Feature-004: Module Loading & Lifecycle Management

**Status**: ✅ completed
**Scope**: Medium
**Complexity**: Medium
**Priority**: P2 (Core functionality after foundation)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/4
**Version Completed**: v0.5.0-alpha.1
**Completion Date**: 2025-11-22

---

## Description

Integrate the existing ModuleLoader with the configuration system and EventBus to enable declarative module loading from `config/modules.yaml`. Implement the module interface contract (initialize/shutdown hooks) and ensure modules receive EventBus access for pub/sub communication.

---

## Objectives

1. **Load Modules from Configuration**
   - Read `config/modules.yaml` to get module list
   - Parse module configurations (name, path, enabled, config)
   - Use ModuleLoader to load enabled modules
   - Skip disabled modules with log message

2. **Implement Module Interface**
   - Call `initialize(event_bus, config)` on each loaded module
   - Pass EventBus instance to modules for pub/sub
   - Pass module-specific config from YAML
   - Call `shutdown()` on modules during application shutdown

3. **EventBus Integration**
   - Ensure modules can subscribe to events via event_bus
   - Ensure modules can publish events via event_bus
   - Publish lifecycle events: `module.loaded`, `module.unloaded`, `module.error`

4. **Error Handling**
   - Use retry decorator for module loading (from Feature-003)
   - Isolate module load failures (one failure doesn't crash app)
   - Log detailed errors for debugging
   - Continue loading other modules if one fails

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/core/application.py` (add module loading in `start()`)
- `src/main_app/core/module_loader.py` (add EventBus injection to modules)
- `config/modules.yaml` (populate with module declarations - can be empty list initially)

**Functionality Delivered**:
- Modules loaded declaratively from `modules.yaml`
- Modules receive EventBus for communication
- Modules receive their specific configuration
- Module lifecycle managed (initialize on load, shutdown on app exit)
- Lifecycle events published to EventBus
- Failed module loads don't crash application

---

## Dependencies

**Upstream**:
- Feature-001 (Configuration System) - MUST be completed
- Feature-003 (Error Handling Integration) - MUST be completed

**Downstream**:
- Feature-005 (Hot-Reload) will enhance this
- Feature-006 (Application Integration) builds on this

---

## Acceptance Criteria

**Must Have**:
1. `modules.yaml` parsed and modules loaded at startup
2. `initialize(event_bus, config)` called on each loaded module
3. Modules can subscribe to events: `event_bus.subscribe("event.type", callback)`
4. Modules can publish events: `event_bus.publish("event.type", data)`
5. `shutdown()` called on all modules during graceful shutdown
6. EventBus publishes `module.loaded` event with module name and config
7. EventBus publishes `module.error` event if module fails to load
8. Disabled modules (enabled: false) are skipped with log message
9. Missing module files produce error log, continue loading others

**Nice to Have** (bonus, not required):
- Module dependency ordering (load order based on dependencies) - **Skip in ALPHA**
- Module health checks - **Skip in ALPHA**
- Auto-restart failed modules - **Skip in ALPHA** (BETA feature)

---

## Validation Approach (Manual Testing)

**Test Case 1: Load Modules from Config**
```yaml
# config/modules.yaml
modules:
  - name: "test-module-1"
    path: "../modules-backend/mod-test-1/__init__.py"
    enabled: true
    config:
      setting: "value"
```
```bash
python -m main_app
# Expected: Module loaded, initialize() called, logs show success
```

**Test Case 2: Module Receives EventBus**
```python
# In test module's __init__.py
def initialize(event_bus, config):
    event_bus.subscribe("test.event", lambda data: print(f"Got: {data}"))
    event_bus.publish("module.ready", {"module": "test-module-1"})
```
```bash
python -m main_app
# Expected: Module subscribes successfully, publishes event
```

**Test Case 3: Disabled Module Skipped**
```yaml
# config/modules.yaml
modules:
  - name: "disabled-module"
    path: "../modules-backend/mod-disabled/__init__.py"
    enabled: false
```
```bash
python -m main_app
# Expected: Log shows "Module 'disabled-module' is disabled, skipping"
# Module not loaded, no initialize() call
```

**Test Case 4: Module Load Failure Isolated**
```yaml
# config/modules.yaml
modules:
  - name: "good-module"
    path: "../modules-backend/mod-good/__init__.py"
    enabled: true
  - name: "bad-module"
    path: "../modules-backend/DOES_NOT_EXIST/__init__.py"
    enabled: true
  - name: "another-good-module"
    path: "../modules-backend/mod-good2/__init__.py"
    enabled: true
```
```bash
python -m main_app
# Expected: good-module loads, bad-module fails (logged), another-good-module loads
# EventBus publishes module.error for bad-module
# Application continues running with 2/3 modules
```

**Test Case 5: Shutdown Calls Module Hooks**
```python
# In test module
def shutdown():
    print("Module shutting down...")
    # Cleanup resources
```
```bash
python -m main_app
# Press Ctrl+C
# Expected: shutdown() called on all loaded modules
# Logs show "Module 'test-module-1' unloaded"
```

---

## Implementation Notes

**Module Interface Contract**:

Every module MUST implement:
```python
# module __init__.py or main.py

def initialize(event_bus, config):
    """
    Called by main/ when module is loaded.

    Args:
        event_bus: EventBus instance for pub/sub communication
        config: Module-specific config from modules.yaml
    """
    # Subscribe to events
    event_bus.subscribe("some.event", handle_event)

    # Publish ready event
    event_bus.publish("module.ready", {"module": __name__})

    # Use config
    setting = config.get("setting", "default")

def shutdown():
    """Called by main/ when module is unloaded or app shuts down."""
    # Cleanup resources
    # Unsubscribe from events if needed
    pass
```

**Application Integration**:
```python
# In application.py

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

    # Load modules from config
    modules_config = self.config.get("modules", [])
    self._load_modules(modules_config)

    self._running = True
    logger.info("Application started successfully")

    # Keep running
    self._run()

def _load_modules(self, modules_config: List[Dict]) -> None:
    """Load modules from configuration."""
    for module_data in modules_config:
        config = ModuleConfig(
            name=module_data["name"],
            path=module_data["path"],
            enabled=module_data.get("enabled", True),
            config=module_data.get("config", {})
        )

        # Load module
        success = self.module_loader.load_module(config)

        if success:
            # Call initialize hook
            module = self.module_loader.get_module(config.name)
            if hasattr(module, "initialize"):
                try:
                    module.initialize(self.event_bus, config.config)
                    self.event_bus.publish("module.loaded", {
                        "name": config.name,
                        "config": config.config
                    })
                except Exception as e:
                    logger.error(f"Failed to initialize module '{config.name}': {e}")
                    self.event_bus.publish("module.error", {
                        "name": config.name,
                        "error": str(e)
                    })
        else:
            self.event_bus.publish("module.error", {
                "name": config.name,
                "error": "Failed to load"
            })

def shutdown(self) -> None:
    """Shutdown application gracefully."""
    if not self._running:
        return

    logger.info("Shutting down application...")
    self._running = False

    # Publish shutdown event
    self.event_bus.publish("app.shutdown")

    # Shutdown modules (calls shutdown() hook)
    self.module_loader.shutdown()

    # Clear event bus
    self.event_bus.clear()

    logger.info("Application shutdown complete")
```

**Config Structure**:
```yaml
# config/modules.yaml
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
      subscribe_events: ["test.ping"]
```

**Error Isolation**:
- Wrap module.initialize() in try/except
- Log errors with full stack trace
- Publish module.error event
- Continue loading other modules
- Don't unload module if initialize fails (allow manual debugging)

---

## Rough Effort Estimate

**Time**: 3-4 hours (including testing)

**Breakdown**:
- Implement _load_modules() in Application: 1 hour
- Add initialize/shutdown hooks calling: 30 minutes
- EventBus lifecycle event publishing: 30 minutes
- Error handling and isolation: 30 minutes
- Manual testing with dummy modules: 1-1.5 hours

---

## Success Metrics

**Functional**:
- All enabled modules load successfully
- Modules receive EventBus and can communicate
- Lifecycle events published correctly
- Module failures isolated (don't crash app)
- Graceful shutdown calls all module hooks

**Quality**:
- Clear error messages for module load failures
- Comprehensive logging of module lifecycle
- Code follows project conventions
- No breaking changes to existing ModuleLoader

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.1.0-alpha.1 or v0.2.0-alpha.1
**Previous Feature**: Feature-003 (Error Handling Integration)
**Next Feature**: Feature-005 (Module Hot-Reload System)
