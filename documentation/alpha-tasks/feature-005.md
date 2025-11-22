# Feature-005: Module Hot-Reload System

**Status**: 🎯 planned
**Scope**: Small
**Complexity**: Low
**Priority**: P3 (Enhancement - improves development experience)

---

## Description

Enable hot-reload for modules so that file changes trigger automatic module reloading without restarting the application. This feature leverages the existing watchdog integration in ModuleLoader and enhances it to work with the module interface (shutdown/initialize cycle).

---

## Objectives

1. **Configure Hot-Reload**
   - Add hot-reload enable/disable flag to `config/main.yaml`
   - Respect configuration in ModuleLoader initialization
   - Log hot-reload status at startup

2. **Implement Reload Cycle**
   - When module file changes, trigger reload
   - Call `shutdown()` on old module instance
   - Reload module from disk
   - Call `initialize(event_bus, config)` on new instance
   - Publish `module.reloaded` event

3. **Handle Reload Failures**
   - If new module fails to load, keep old module running (rollback)
   - Log reload failures clearly
   - Publish `module.reload_failed` event
   - Don't crash application on reload failure

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/core/module_loader.py` (enhance reload logic to call hooks)
- `src/main_app/core/application.py` (pass hot-reload config to ModuleLoader)
- `config/main.yaml` (add hot_reload configuration section)

**Functionality Delivered**:
- File changes trigger module reload automatically
- Module lifecycle hooks called during reload (shutdown → initialize)
- Reload failures don't crash application
- EventBus events published for reload lifecycle
- Hot-reload can be disabled in config (useful for production)

---

## Dependencies

**Upstream**: Feature-004 (Module Loading & Lifecycle Management) - MUST be completed
**Downstream**: Feature-007 (Test Mode) benefits from this

---

## Acceptance Criteria

**Must Have**:
1. Hot-reload can be enabled/disabled via `config/main.yaml`
2. File modification triggers module reload automatically
3. `shutdown()` called on old module before reload
4. `initialize(event_bus, config)` called on new module after reload
5. EventBus publishes `module.reloaded` event on success
6. EventBus publishes `module.reload_failed` event on failure
7. Failed reload keeps old module running (rollback behavior)
8. Reload completes within < 1 second of file save

**Nice to Have** (bonus, not required):
- Reload multiple dependent modules in order - **Skip in ALPHA**
- Module state preservation across reload - **Skip in ALPHA** (modules responsible)
- Debounce rapid file changes - **Skip in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Hot-Reload Enabled**
```yaml
# config/main.yaml
app:
  hot_reload: true
```
```bash
python -m main_app
# Modify a loaded module file (add print statement)
# Save file
# Expected: Module reloads within 1 second, new code active
# Logs show: "Module 'mod-X' reloaded successfully"
```

**Test Case 2: Hot-Reload Disabled**
```yaml
# config/main.yaml
app:
  hot_reload: false
```
```bash
python -m main_app
# Modify a loaded module file
# Save file
# Expected: No reload, module keeps running old code
# Logs show: "Hot-reload disabled, ignoring file changes"
```

**Test Case 3: Reload Lifecycle Hooks Called**
```python
# In test module
def initialize(event_bus, config):
    print("INITIALIZE called")

def shutdown():
    print("SHUTDOWN called")
```
```bash
python -m main_app
# Modify module file, save
# Expected console output:
#   SHUTDOWN called
#   INITIALIZE called
# Module receives fresh EventBus reference
```

**Test Case 4: Reload Failure Rollback**
```python
# In test module - introduce syntax error
def initialize(event_bus, config):
    this_will_cause_syntax_error =
```
```bash
# Save file with syntax error
# Expected: Reload fails, old module still running
# Logs show: "Failed to reload module 'mod-X': SyntaxError..."
# EventBus publishes module.reload_failed
# Application continues running with old module
```

**Test Case 5: EventBus Events Published**
```python
# Subscribe to reload events
event_bus.subscribe("module.reloaded", lambda data: print(f"Reloaded: {data}"))
event_bus.subscribe("module.reload_failed", lambda data: print(f"Failed: {data}"))
```
```bash
python -m main_app
# Modify module, save (successful reload)
# Expected: "Reloaded: {'name': 'mod-X'}" printed
# Introduce error, save (failed reload)
# Expected: "Failed: {'name': 'mod-X', 'error': '...'}" printed
```

---

## Implementation Notes

**Current State**:
ModuleLoader already has watchdog integration and `reload_module()` method, but it doesn't call module hooks.

**Enhancement Needed**:

**module_loader.py**:
```python
def reload_module(self, module_name: str, event_bus=None, module_config=None) -> bool:
    """
    Reload a module (unload then load with lifecycle hooks).

    Args:
        module_name: Name of module to reload
        event_bus: EventBus instance to pass to initialize()
        module_config: Config dict to pass to initialize()

    Returns:
        True if module reloaded successfully
    """
    if module_name not in self._module_configs:
        logger.warning(f"Module '{module_name}' not in configurations")
        return False

    config = self._module_configs[module_name]

    # Get old module for potential rollback
    old_module = self._modules.get(module_name)

    try:
        # Unload old module (calls shutdown() hook)
        self.unload_module(module_name)

        # Load new module
        success = self.load_module(config)

        if success and event_bus:
            # Call initialize hook on new module
            new_module = self._modules[module_name]
            if hasattr(new_module, "initialize"):
                new_module.initialize(event_bus, module_config or {})

            logger.info(f"Module '{module_name}' reloaded successfully")
            return True
        else:
            raise Exception("Failed to load new module version")

    except Exception as e:
        logger.error(f"Failed to reload module '{module_name}': {e}", exc_info=True)

        # Rollback: restore old module if possible
        if old_module:
            logger.warning(f"Attempting rollback for module '{module_name}'")
            self._modules[module_name] = old_module
            sys.modules[module_name] = old_module
            # Re-initialize old module
            if hasattr(old_module, "initialize") and event_bus:
                old_module.initialize(event_bus, module_config or {})

        return False
```

**Application Integration**:
```python
# In application.py

def __init__(self, config: Dict[str, Any]) -> None:
    """Initialize application."""
    self.config = config
    hot_reload = config.get("app", {}).get("hot_reload", True)

    self.event_bus = EventBus()
    self.module_loader = ModuleLoader(watch_reload=hot_reload)
    self.resource_manager = ResourceManager()
    self._running = False

    logger.info(f"Application initialized (hot-reload={'enabled' if hot_reload else 'disabled'})")

def _setup_hot_reload(self) -> None:
    """Setup hot-reload with proper event/config passing."""
    # Store reference for reload callbacks
    self._module_configs = {}

    # Override reload handler to call hooks
    original_reload = self.module_loader.reload_module

    def reload_with_hooks(module_name: str) -> bool:
        module_cfg = self._module_configs.get(module_name, {})
        success = original_reload(
            module_name,
            event_bus=self.event_bus,
            module_config=module_cfg
        )

        if success:
            self.event_bus.publish("module.reloaded", {"name": module_name})
        else:
            self.event_bus.publish("module.reload_failed", {
                "name": module_name,
                "error": "Reload failed, check logs"
            })

        return success

    # Monkey-patch with enhanced version
    self.module_loader.reload_module = reload_with_hooks
```

**Config Addition**:
```yaml
# config/main.yaml
app:
  name: "main-orchestrator"
  version: "0.1.0-alpha.1"
  hot_reload: true  # Enable/disable hot-reload
```

**EventBus Events**:
- `module.reloaded`: Published on successful reload
  - Data: `{"name": str}`
- `module.reload_failed`: Published on failed reload
  - Data: `{"name": str, "error": str}`

---

## Rough Effort Estimate

**Time**: 2-3 hours (including testing)

**Breakdown**:
- Enhance reload_module() with hooks: 45 minutes
- Add config option and integration: 30 minutes
- Implement rollback logic: 45 minutes
- Manual testing (success + failure cases): 1 hour

---

## Success Metrics

**Functional**:
- Hot-reload triggers within 1 second of file save
- Module lifecycle hooks called correctly
- Failed reloads rollback to old module
- Hot-reload can be disabled via config

**Quality**:
- Clear logging for all reload operations
- EventBus events published consistently
- No application crashes during reload
- Code follows project conventions

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.2.0-alpha.1 or v0.3.0-alpha.1
**Previous Feature**: Feature-004 (Module Loading & Lifecycle Management)
**Next Feature**: Feature-006 (Application Startup & Integration)
