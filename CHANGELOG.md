# Changelog

📋 **For complete version history**: see [changelog/index.md](changelog/index.md)

---

## [0.8.0-alpha.1] - 2025-11-22

### Added
- **Test Mode Implementation (Feature-007)**
  - Test mode triggered by `--test` CLI flag
  - pytest integration with consolidated test execution
  - Test discovery from modules via optional `get_tests()` function
  - Automatic inclusion of main/tests/ directory
  - Exit codes: 0 (pass), 1 (fail), 2 (error)
  - Modules loaded but Application.start() not called in test mode
  - Hot-reload disabled in test mode (watch_reload=False)

### Files Created
- `src/main_app/testing/__init__.py` - Test package initialization (5 lines)
- `src/main_app/testing/test_runner.py` - Test discovery and execution (206 lines)
- `tests/test_example.py` - Example tests for validation (20 lines)

### Files Modified
- `src/main_app/__main__.py` - Test mode implementation (119 lines, +52)

### Testing
- Manual validation: All 5 test scenarios PASS
  - ✅ Basic test execution
  - ✅ Test mode initialization
  - ✅ Test discovery
  - ✅ Module without get_tests()
  - ✅ pytest integration

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-007
- **GitHub Issue**: #7
- **Commit**: 7393b14

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
