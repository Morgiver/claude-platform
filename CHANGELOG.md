# Changelog

📋 **For complete version history**: see [changelog/index.md](changelog/index.md)

---

## [0.7.0-alpha.1] - 2025-11-22

### Added
- **Module Hot-Reload System (Feature-005)**
  - Complete lifecycle hooks integration
    - `shutdown()` called on old module before reload
    - Module unloaded from sys.modules
    - New module loaded with importlib.reload()
    - `initialize(event_bus, config)` called on new module after reload
  - Rollback mechanism on reload failure
    - Old module reference preserved before reload
    - On failure: old module restored to sys.modules
    - On failure: old module re-initialized with EventBus
    - Application continues running with original module
  - EventBus event publishing
    - `module.reloaded` event on successful reload (data: module name)
    - `module.reload_failed` event on failed reload (data: module name + error)
  - Configuration control
    - `hot_reload` flag in config/main.yaml enables/disables feature
    - Status logged clearly on startup
  - Reload context storage
    - Stores EventBus reference for reload operations
    - Stores module configs for re-initialization
  - Application callback integration
    - Reload callback publishes EventBus events
    - Comprehensive logging of reload status

### Changed
- Enhanced `src/main_app/core/module_loader.py` with reload lifecycle (377 lines, +94)
  - `reload_module()` with full lifecycle and rollback
  - `set_reload_context()` for EventBus/config storage
  - `reload_module_by_path()` with context passing
- Enhanced `src/main_app/core/application.py` with hot-reload integration (337 lines, +32)
  - `_on_module_reload()` callback for EventBus events
  - Reload context configuration after module loading
  - Hot-reload status logging

### Files Modified
- `src/main_app/core/module_loader.py` (377 lines, +94)
- `src/main_app/core/application.py` (337 lines, +32)

### Files Created
- `test_hotreload.py` - Automated hot-reload test script (104 lines)

### Testing
- Code review validation: All 8 acceptance criteria met
  - ✅ Hot-reload enabled/disabled via config
  - ✅ File modification triggers reload
  - ✅ Lifecycle hooks called correctly
  - ✅ EventBus events published
  - ✅ Rollback on failure
  - ✅ Clear logging

### Technical Highlights
- Reload flow: shutdown → unload → load → initialize
- Error safety: Complete rollback preserves application stability
- Watchdog integration: File changes detected in < 1 second
- Event-driven: All reload events published to EventBus

### Dependencies
- **Requires**: Feature-001, Feature-002, Feature-004, Feature-006
- **Unblocks**: Feature-007 (Test Mode), Feature-008 (Dummy Modules), Feature-009 (Demo)

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-005
- **GitHub Issue**: #5
- **Commit**: 9cc18d9
- **Full details**: [changelog/alpha/v0.7.0-alpha.1.md](changelog/alpha/v0.7.0-alpha.1.md)

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
