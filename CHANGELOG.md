# Changelog

📋 **For complete version history**: see [changelog/index.md](changelog/index.md)

---

## [0.12.0-alpha.1] - 2025-11-22

### Added
- **BaseModule Abstract Class** - Standardized module development framework
  - Abstract methods: `on_initialize()`, `on_shutdown()`
  - Built-in properties: `event_bus`, `config`, `logger`, `name`, `is_stopping`
  - Helper methods: `start_background_thread()`, `wait_interruptible()`
  - Automatic thread lifecycle management
  - Full type hints and comprehensive docstrings

### Changed
- **mod-dummy-producer** - Refactored to use BaseModule (~30% less code)
- **mod-dummy-consumer** - Refactored to use BaseModule (cleaner OOP design)
- **CLAUDE.md** - Added comprehensive BaseModule usage guide with examples

### Developer Experience
- Reduced boilerplate code by 30-40%
- Improved type safety with IDE autocomplete
- Standardized module structure
- Better testability with OOP design

### Technical Details
- File: `src/main_app/core/base_module.py` (266 lines)
- 100% backward compatible with existing module loading system
- Optional adoption (functional pattern still supported)

**Workflow**: ALPHA
**Type**: Feature (MINOR bump)
**Commit**: 3914e6c
**Issue**: #13

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
