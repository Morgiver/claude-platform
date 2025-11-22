# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Full changelog**: See [changelog/index.md](changelog/index.md) for complete version history.

---

## [0.3.0-alpha.1] - 2025-11-22

### Added
- **Centralized Logging Setup (Feature-002)**
  - Enhanced logging utilities to use YAML configuration from config/main.yaml
  - Implemented rotating file handlers with configurable size limits and backup counts
  - Automatic logs directory creation if missing
  - Dual logging: console output AND rotating file output (logs/app.log)
  - Configurable log levels from YAML (DEBUG in ALPHA mode)
  - Log format with timestamps, module names, levels, and messages

### Changed
- `setup_logging()` function now accepts full config dict instead of hardcoded parameters
- Application logging configuration simplified to pass full config to setup_logging()
- Logging setup now reads from config["logging"] section in main.yaml

### Files Modified
- `src/main_app/logging/logger.py` - Enhanced setup_logging() to accept config dict
- `src/main_app/core/application.py` - Simplified logging setup call

### Testing
- Manual validation: Application starts with logging configured correctly
- Logs written to both console and logs/app.log
- Log rotation verified (file size, backup count)
- Logs directory auto-creation confirmed
- Log format verified (timestamp, module, level, message)

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-002 (Centralized Logging Setup)
- **GitHub Issue**: Closes #2
- **Commit**: 797d1ec
- **Full details**: [changelog/alpha/v0.3.0-alpha.1.md](changelog/alpha/v0.3.0-alpha.1.md)

---

_This file shows only the current version. Full history: [changelog/index.md](changelog/index.md)_
