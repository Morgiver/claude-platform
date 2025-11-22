# Changelog

📋 **For complete version history**: see [changelog/index.md](changelog/index.md)

---

## [0.6.0-alpha.1] - 2025-11-22

### Added
- **Application Startup & Integration (Feature-006)**
  - Resource monitoring in main loop (60-second interval)
    - RAM usage percentage tracking via ResourceManager
    - CPU usage percentage tracking via ResourceManager
    - Active module count from ModuleLoader
    - Metrics logged to console and file
    - Metrics published to EventBus as `app.monitor` events
  - CLI argument parsing with argparse
    - `--version`: Display version information and exit
    - `--config-dir PATH`: Specify custom configuration directory
    - `--test`: Placeholder for Feature-007 (Test Mode)
    - `--help`: Automatic help message from argparse

### Changed
- Enhanced `src/main_app/core/application.py` with `_run()` method improvements (304 lines, +30)
- Complete rewrite of `src/main_app/__main__.py` with CLI argument parser (65 lines, +58)

### Integration
- ✅ Configuration System (Feature-001) fully integrated
- ✅ Centralized Logging (Feature-002) fully integrated
- ✅ Error Handling (Feature-003) fully integrated
- ✅ Module Loading (Feature-004) fully integrated
- Complete startup sequence: config → logging → EventBus → modules → main loop
- Complete shutdown sequence: signal → app.shutdown event → module shutdown → cleanup

### Files Modified
- `src/main_app/core/application.py` (304 lines, +30)
- `src/main_app/__main__.py` (65 lines, +58)

### Testing
- Manual validation: All 5 test scenarios PASS
  - ✅ CLI --version argument
  - ✅ CLI --test placeholder
  - ✅ Complete startup sequence (< 1 second)
  - ✅ Resource monitoring logs (60s intervals)
  - ✅ CLI --config-dir argument

### Performance
- **Startup time**: < 1 second (for 1 module)
- **Monitoring interval**: 60 seconds (configurable in code)
- **Resource overhead**: Minimal (0.1s CPU sampling)

### Dependencies
- **Requires**: Feature-001, Feature-002, Feature-003, Feature-004
- **Unblocks**: Feature-007 (Test Mode), Feature-008 (Dummy Modules), Feature-009 (Demo Scenario)

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-006
- **GitHub Issue**: #6
- **Commit**: 6eec644
- **Full details**: [changelog/alpha/v0.6.0-alpha.1.md](changelog/alpha/v0.6.0-alpha.1.md)

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
