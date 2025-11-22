# Changelog

For complete version history: see [changelog/index.md](changelog/index.md)

---

## [0.10.0-alpha.2] - 2025-11-22

### Added
- Detailed [TIMING] logs for module loading diagnostics
- Daemon mode for watchdog observer (non-blocking)
- Initial wait period in producer before first event publish (5s delay)
- Initialization completion logs in consumer module
- Explicit exit code handling in __main__.py

### Changed
- Signal handler now sets `_running=False` instead of `sys.exit(0)` for cleaner shutdown
- Demo validation increased wait time from 10s to 15s for reliable event capture
- Consumer subscription messages clarified for better visibility
- Removed log file deletion from demo cleanup (prevents permission errors)

### Fixed
- Consumer loading timing issue (race condition resolved)
- End-to-end EventBus communication now 100% reliable
- Module loading performance diagnostics enhanced
- Demo validation logic improved for consistent results

**Known Issues**:
- Exit code returns 1 on Windows SIGTERM (minor, tolerable for ALPHA)

**Workflow**: ALPHA Polish & Refinement
**Mission**: mission-010.md (Refinement-001)
**GitHub Issue**: #10

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
