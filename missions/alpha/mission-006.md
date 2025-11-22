# Mission: Application Startup & Integration

**Mission ID**: MISSION-006
**Feature Reference**: FEATURE-006 (from alpha-tasks/feature-006.md)
**Priority**: P2
**Status**: Active
**Estimated Complexity**: Medium

## Objective

Complete the application startup and shutdown flow by integrating all core components (configuration loading, logging setup, module loading, error handling) into a cohesive orchestration system. This mission ties together all existing components into a fully functional application lifecycle.

## Context

### Required Knowledge

**Completed Features (Dependencies Met)**:
- ✅ Feature-001: Configuration System (config_loader, main.yaml, modules.yaml)
- ✅ Feature-002: Centralized Logging (setup_logging, log rotation)
- ✅ Feature-003: Error Handling (retry strategies, circuit breaker)
- ✅ Feature-004: Module Loading (ModuleLoader with hot-reload, lifecycle hooks)

**Existing Components Available**:
- EventBus (109 lines) - event delivery system
- ModuleLoader (270 lines) - module lifecycle with hot-reload
- ResourceManager (172 lines) - system resource calculations
- Application stub (125 lines) - basic lifecycle management
- Config loader - YAML configuration loading
- Logging utilities - setup_logging(config)

**What's Missing**:
- Application class needs complete integration logic
- Config loading during Application.__init__
- Logging setup from config during initialization
- Module initialization with EventBus injection
- Resource monitoring in main loop
- Signal handlers for graceful shutdown
- CLI argument parsing (__main__.py)

### Architecture Integration Points

1. **Startup Sequence** (Application.start()):
   - Load config → Setup logging → Initialize EventBus → Initialize ResourceManager → Initialize ModuleLoader → Load modules → Publish app.started → Enter main loop

2. **Module Loading** (Application._load_modules()):
   - Read modules config from self.config
   - Create ModuleConfig for each module
   - Call ModuleLoader.load_module()
   - Inject EventBus via module.initialize(event_bus, config)
   - Publish module.loaded or module.error events

3. **Main Loop** (Application._run()):
   - Resource monitoring every 60 seconds
   - Log RAM/CPU usage and active module count
   - Sleep 1 second to avoid busy-wait
   - Handle KeyboardInterrupt gracefully

4. **Shutdown Sequence** (Application.shutdown()):
   - Publish app.shutdown event
   - Call ModuleLoader.shutdown() (unloads all modules)
   - Clear EventBus subscriptions
   - Log shutdown completion

### File References

**Files to Modify**:
- `src/main_app/core/application.py` (complete integration)
- `src/main_app/__main__.py` (add CLI argument parsing)

**Files to Read** (for integration):
- `src/main_app/config/config_loader.py` (load_all_configs function)
- `src/main_app/logging/logger.py` (setup_logging function)
- `src/main_app/core/event_bus.py` (EventBus API)
- `src/main_app/core/module_loader.py` (ModuleLoader, ModuleConfig)
- `src/main_app/core/resource_manager.py` (ResourceManager API)

## Specifications

### Input Requirements

**Configuration Files** (already exist from Feature-001):
- `config/main.yaml` - app settings, hot_reload flag, resources config
- `config/modules.yaml` - module list with name, path, enabled, config

**Expected Config Structure**:
```yaml
# config/main.yaml
app:
  hot_reload: true
  log_level: "INFO"

resources:
  process_memory_mb: 512

logging:
  level: "INFO"
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  file: "logs/app.log"
  rotation:
    max_bytes: 10485760
    backup_count: 5
```

### Output Deliverables

**Modified Files**:

1. **src/main_app/core/application.py** (complete implementation):
   - Load config in __init__ using load_all_configs(config_dir)
   - Call setup_logging(self.config) after loading config
   - Initialize EventBus, ResourceManager, ModuleLoader in __init__
   - Implement complete start() method with signal handlers
   - Implement _load_modules() with EventBus injection
   - Implement _run() with resource monitoring every 60s
   - Implement shutdown() with event publishing and cleanup
   - Add _signal_handler() for SIGINT/SIGTERM

2. **src/main_app/__main__.py** (CLI argument parsing):
   - Add argparse for command-line options
   - Support --config-dir (default: "config")
   - Support --version (print version and exit)
   - Support --test flag (placeholder for Feature-007)
   - Create Application instance with config_dir
   - Call app.start() with proper error handling
   - Handle KeyboardInterrupt gracefully

**Expected Functionality**:
- Application starts with all components initialized
- Modules loaded and initialized with EventBus
- Resource monitoring logs every 60 seconds
- Graceful shutdown on Ctrl+C or signals
- CLI arguments parsed and respected
- Clear logging throughout startup/shutdown

### Acceptance Criteria

- [ ] Application loads config from config/ directory on startup
- [ ] Logging setup completed before component initialization
- [ ] EventBus, ResourceManager, ModuleLoader initialized in correct order
- [ ] Modules loaded after core components ready
- [ ] Each module's initialize() called with EventBus and config
- [ ] app.started event published with resource info
- [ ] Main loop monitors resources every 60 seconds (RAM%, CPU%, active modules)
- [ ] SIGINT/SIGTERM trigger graceful shutdown
- [ ] app.shutdown event published before component shutdown
- [ ] All modules' shutdown() called via ModuleLoader.shutdown()
- [ ] EventBus cleared during shutdown
- [ ] CLI arguments parsed: --config-dir, --version, --test (placeholder)
- [ ] Startup completes in < 2 seconds for 5 modules
- [ ] No crashes during normal startup/shutdown flow

## Implementation Constraints

### Code Organization
- File type: Class (Application) + Script (__main__)
- Application.py size limit: < 400 lines (ALPHA tolerance: < 600 lines)
- __main__.py size limit: < 100 lines
- Architecture rule: 1 class = 1 file (Application in application.py)

### Technical Requirements

**Integration Pattern**:
```python
# Application.__init__
self.config = load_all_configs(config_dir)
setup_logging(self.config)
self.event_bus = EventBus()
self.resource_manager = ResourceManager(...)
self.module_loader = ModuleLoader(watch_reload=...)
```

**Module Initialization Pattern**:
```python
# Application._load_modules
module = self.module_loader.get_module(config.name)
if hasattr(module, "initialize"):
    module.initialize(self.event_bus, config.config or {})
```

**Signal Handling**:
```python
signal.signal(signal.SIGINT, self._signal_handler)
signal.signal(signal.SIGTERM, self._signal_handler)
```

**Resource Monitoring**:
```python
ram_usage = self.resource_manager.get_memory_usage_percent()
cpu_usage = self.resource_manager.get_cpu_usage_percent(interval=0.1)
active_modules = len(self.module_loader.get_loaded_modules())
```

### Performance Requirements
- Startup time: < 2 seconds (for 5 modules)
- Resource monitoring interval: 60 seconds (not blocking)
- Shutdown time: < 1 second

## Testing Requirements

### Test Specifications

**Manual Test Cases**:

1. **Complete Startup Sequence**:
   - Run: `python -m main_app`
   - Verify logs show correct initialization order
   - Check app.started event published
   - Confirm startup time < 2 seconds

2. **Graceful Shutdown (SIGINT)**:
   - Run: `python -m main_app`
   - Press Ctrl+C
   - Verify shutdown event published
   - Check all modules unloaded
   - Confirm clean exit (code 0)

3. **Resource Monitoring**:
   - Run: `python -m main_app`
   - Wait 2+ minutes
   - Verify resource logs every 60 seconds
   - Check RAM%, CPU%, module count logged

4. **CLI Arguments**:
   - Test: `python -m main_app --version`
   - Test: `python -m main_app --config-dir /custom/path`
   - Test: `python -m main_app --test` (should show "not implemented")
   - Verify correct behavior for each

5. **Startup Failure Handling**:
   - Remove config/main.yaml
   - Run: `python -m main_app`
   - Verify error logged, graceful exit (code 1)

### Validation Method

**Success Indicators**:
- All test cases pass
- Application starts and shuts down cleanly
- Logs show complete startup/shutdown sequences
- No crashes or unhandled exceptions
- Resource monitoring works continuously
- CLI arguments respected

## Next Steps

### Upon Completion

**Immediate Actions**:
1. Manual validation of all test cases
2. Update feature-006.md with completion status
3. Proceed to Step A8 (Manual Validation & Debug)

**Follow-Up Tasks**:
- Archive this mission to missions/alpha-archived/
- Update alpha-tasks/index.md: Feature-006 → completed
- Prepare for Step A9 (Feedback Checkpoint)
- User demonstration of integrated application

### Blocked Features

**Features Unblocked by This Mission**:
- Feature-007: Test Mode Implementation (builds on --test flag)
- Feature-008: Dummy Modules for Validation (needs running app)
- Feature-009: Demo Scenario Execution (requires complete integration)

---

**Mission Context Size**: ~195 lines
**Estimated Implementation Time**: 3-4 hours
**ALPHA Constraints**: Focus on integration, manual testing acceptable
