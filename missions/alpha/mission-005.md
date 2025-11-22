# Mission: Module Hot-Reload System

**Mission ID**: MISSION-005
**Feature Reference**: Feature-005 (from alpha-tasks/feature-005.md)
**Priority**: P3 (Enhancement)
**Status**: Active
**Estimated Complexity**: Low

---

## Objective

Enable automatic hot-reload functionality for modules when their source files change, allowing developers to see code changes instantly without restarting the application. This mission enhances the existing ModuleLoader watchdog integration to properly call module lifecycle hooks during reload and implement rollback on failure.

---

## Context

### Completed Prerequisites
- Feature-001: Configuration System (v0.2.0-alpha.1)
- Feature-002: Centralized Logging (v0.3.0-alpha.1)
- Feature-003: Error Handling (v0.4.0-alpha.1)
- Feature-004: Module Loading & Lifecycle Management (v0.5.0-alpha.1)

### Current State
ModuleLoader already includes watchdog integration (lines 47-65) and a basic `reload_module()` method, but it doesn't:
- Call module lifecycle hooks (`shutdown()` → `initialize()`)
- Pass EventBus and config to reloaded modules
- Publish reload events to EventBus
- Implement rollback on reload failure
- Respect configuration to enable/disable hot-reload

### Files to Modify
1. `src/main_app/core/module_loader.py` - Enhance reload logic with hooks
2. `src/main_app/core/application.py` - Integrate hot-reload config
3. `config/main.yaml` - Add hot_reload configuration flag

---

## Specifications

### Input Requirements

**Configuration**:
```yaml
# config/main.yaml
app:
  name: "main-orchestrator"
  version: "0.6.0-alpha.1"
  hot_reload: true  # Enable/disable hot-reload
```

**Module Interface** (already established by Feature-004):
```python
def initialize(event_bus, config):
    """Called when module loads or reloads"""
    pass

def shutdown():
    """Called before module unloads or reloads"""
    pass
```

### Output Deliverables

**Enhanced reload_module() Method**:
- Accept `event_bus` and `module_config` parameters
- Call `shutdown()` on old module instance before unload
- Call `initialize(event_bus, config)` on new module after load
- Implement rollback: restore old module if reload fails
- Return boolean success/failure status

**Application Integration**:
- Read `hot_reload` flag from config
- Pass flag to ModuleLoader constructor (`watch_reload` parameter)
- Setup reload callback that publishes EventBus events
- Store module configs for reload hook calls

**EventBus Events**:
- `module.reloaded` - Published on successful reload
  - Data: `{"name": str}`
- `module.reload_failed` - Published on failed reload
  - Data: `{"name": str, "error": str}`

### Acceptance Criteria

**Must Pass**:
- [ ] Hot-reload can be enabled/disabled via `config/main.yaml`
- [ ] File modification triggers module reload automatically (< 1 second)
- [ ] `shutdown()` called on old module before reload
- [ ] `initialize(event_bus, config)` called on new module after reload
- [ ] EventBus publishes `module.reloaded` event on success
- [ ] EventBus publishes `module.reload_failed` event on failure
- [ ] Failed reload keeps old module running (rollback behavior)
- [ ] Application logs reload status clearly

---

## Implementation Constraints

### Code Organization
- File type: Enhancement to existing classes
- Maintain existing ModuleLoader structure (270 lines currently)
- ALPHA tolerance: Keep under 1500 lines total

### Technical Requirements
- Use existing watchdog observer infrastructure
- Preserve module instance references for rollback
- Handle exceptions gracefully (no application crashes)
- Log all reload operations (success, failure, rollback)

### Implementation Pattern

**module_loader.py Enhancement**:
```python
def reload_module(self, module_name: str, event_bus=None, module_config=None) -> bool:
    """
    Reload a module with full lifecycle hooks.

    Args:
        module_name: Name of module to reload
        event_bus: EventBus instance for initialize() hook
        module_config: Config dict for initialize() hook

    Returns:
        True if reload successful, False if rollback occurred
    """
    # 1. Get old module instance for rollback
    # 2. Call shutdown() hook on old module
    # 3. Unload old module from sys.modules
    # 4. Load new module version
    # 5. Call initialize() hook on new module
    # 6. Return success
    # 7. On exception: rollback to old module, re-initialize, return False
```

**application.py Integration**:
```python
def __init__(self, config: Dict[str, Any]) -> None:
    hot_reload = config.get("app", {}).get("hot_reload", True)
    self.module_loader = ModuleLoader(watch_reload=hot_reload)
    logger.info(f"Hot-reload: {'enabled' if hot_reload else 'disabled'}")

def _setup_hot_reload_callbacks(self) -> None:
    # Wrap reload_module to pass event_bus and publish events
    # Store module configs for hook calls
```

---

## Testing Requirements

### Manual Test Scenarios

**Test 1: Successful Reload**
```bash
1. Start app: python -m main_app
2. Modify a module file (add print statement)
3. Save file
4. Expected: Console shows "SHUTDOWN called" → "INITIALIZE called"
5. Expected: Module runs new code
6. Expected: Logs show "Module 'mod-X' reloaded successfully"
```

**Test 2: Failed Reload with Rollback**
```bash
1. Start app: python -m main_app
2. Modify module file to introduce syntax error
3. Save file
4. Expected: Logs show "Failed to reload module 'mod-X': SyntaxError"
5. Expected: Old module still running (not crashed)
6. Expected: EventBus publishes module.reload_failed
```

**Test 3: Hot-Reload Disabled**
```yaml
# config/main.yaml
app:
  hot_reload: false
```
```bash
1. Start app
2. Modify module file, save
3. Expected: No reload, module keeps old code
4. Expected: Logs show "Hot-reload disabled"
```

**Test 4: EventBus Events Published**
```python
# Subscribe to events in a test module
event_bus.subscribe("module.reloaded", lambda d: print(f"Reloaded: {d}"))
event_bus.subscribe("module.reload_failed", lambda d: print(f"Failed: {d}"))
```
```bash
1. Start app
2. Modify module successfully → expect "Reloaded: {'name': '...'}"
3. Introduce error → expect "Failed: {'name': '...', 'error': '...'}"
```

### Success Indicators
- Reload completes within 1 second of file save
- No application crashes during reload (success or failure)
- Clear logging for all operations
- Lifecycle hooks called in correct order

---

## Next Steps

### Upon Completion
- Update `alpha-tasks/feature-005.md` with status: ✅ completed
- Update `alpha-tasks/index.md` to mark Feature-005 completed
- Tag version in mission file: `version_completed: v0.X.0-alpha.Y`
- Proceed to Step A8 (Manual Validation & Debug)

### Unblocked Features
- Feature-007: Test Mode Implementation (benefits from hot-reload)
- Feature-008: Dummy Modules for Validation (can use hot-reload in testing)

---

## Implementation Guidance

**Approach**:
1. Start with `module_loader.py` reload_module() enhancement
2. Test reload with a simple test module
3. Add rollback logic and test failure cases
4. Integrate config flag in application.py
5. Add EventBus event publishing
6. Run all 4 manual test scenarios

**Key Principle**: Don't crash the application - always rollback on reload failure.

**Estimated Time**: 2-3 hours (including manual testing)
