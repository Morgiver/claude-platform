# Changelog

📋 **For complete version history**: see [changelog/index.md](changelog/index.md)

---

## [0.5.0-alpha.1] - 2025-11-22

### Added
- **Module Loading & Lifecycle Management (Feature-004)**
  - Declarative module loading from `config/modules.yaml`
  - Module interface contract: `initialize(event_bus, config)` and `shutdown()` hooks
  - EventBus injection into all loaded modules for pub/sub communication
  - Module-specific config injection from YAML configuration
  - Lifecycle event publishing (`module.loaded`, `module.error`)
  - Error isolation - module failures don't crash application
  - Hot-reload file observer for module directories
  - Disabled module skipping with log messages
  - Test module validation in `modules-backend/test-module/`

### Changed
- Enhanced `src/main_app/core/application.py` with `_load_modules()` method (273 lines, +73)
- Enhanced `src/main_app/core/module_loader.py` with shutdown lifecycle hooks (282 lines, +13)

### Fixed
- Config merge error in `config_loader.py` when loading `modules.yaml` (dict.update with list)
- Module path resolution (using absolute paths in config for now, relative paths deferred to BETA)

### Files Modified
- `src/main_app/core/application.py` (273 lines, +73)
- `src/main_app/core/module_loader.py` (282 lines, +13)
- `src/main_app/config/config_loader.py` (+3 lines)

### Files Created
- `modules-backend/test-module/__init__.py` (35 lines) - Test module demonstrating interface
- `config/modules.yaml` - Module loading configuration

### Testing
- Manual validation: All 7 test scenarios PASS
  - ✅ Module loading from configuration
  - ✅ Initialize hook with EventBus injection
  - ✅ Config passed to module
  - ✅ EventBus communication (subscribe/publish)
  - ✅ Lifecycle events published
  - ✅ Hot-reload observer started
  - ✅ Error isolation verified

### Dependencies
- **Requires**: Feature-001 (Config System), Feature-002 (Logging), Feature-003 (Error Handling)
- **Unblocks**: Feature-005 (Hot-Reload), Feature-006 (Application Integration), Feature-008/009 (Dummy Modules & Demo)

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-004
- **GitHub Issue**: #4
- **Commit**: badaa8d
- **Full details**: [changelog/alpha/v0.5.0-alpha.1.md](changelog/alpha/v0.5.0-alpha.1.md)

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
