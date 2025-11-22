# Changelog

For complete version history: see [changelog/index.md](changelog/index.md)

---

## [0.11.0-alpha.1] - 2025-11-22

### Added
- **Multi-Platform Compatibility** (Windows, Linux, macOS)
- Platform detection module (`platform_utils.py`)
- Platform information logging at startup (OS, architecture, Python version)
- Platform-aware signal handler registration
  - Windows: SIGINT, SIGTERM, SIGBREAK
  - Linux/macOS: SIGINT, SIGTERM, SIGHUP, SIGQUIT
- Platform-optimized resource limits
  - Windows: Max 32 processes, 128 threads (conservative)
  - Linux: Max 128 processes, 512 threads (aggressive)
  - macOS: Max 64 processes, 256 threads (moderate)
- Platform information in `--version` output

### Changed
- Exit code validation is now platform-aware
  - Windows: Accepts exit codes 0 and 1 (TerminateProcess API)
  - Linux/macOS: Accepts exit codes 0, -15, 143 (SIGTERM)
- Demo script displays platform in success messages
- Resource manager logs platform-specific reasoning

### Fixed
- Windows exit code 1 no longer treated as error (platform behavior)
- Signal coverage expanded for better graceful shutdown
- Resource limits optimized per platform capabilities

**Platform Support**: Windows ✅ | Linux ✅ | macOS ✅

**Workflow**: ALPHA Feature
**Mission**: mission-012.md (Refinement-003)
**GitHub Issue**: #12

---

*This file shows only the current version. Full history: [changelog/](changelog/)*
