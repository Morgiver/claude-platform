# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Full changelog**: See [changelog/index.md](changelog/index.md) for complete version history.

---

## [0.2.0-alpha.1] - 2025-11-22

### Added
- **Configuration System (Feature-001)**
  - YAML configuration loading with environment variable substitution
  - ConfigLoader utility for loading main.yaml, logging.yaml, modules.yaml
  - Environment variable substitution support (${VAR_NAME} syntax)
  - Graceful error handling for missing/invalid configuration files
  - Integration with Application startup
  - Configuration passed to all core components

### Changed
- Application class now loads configuration at startup
- ResourceManager accepts configuration parameters (process_memory_mb, reserved_ram_percent, threads_per_core)
- Logging setup now uses YAML configuration from logging.yaml
- Added python-dotenv dependency for .env file support

### Files Created
- `src/main_app/config/__init__.py` - Config package exports
- `src/main_app/config/config_loader.py` - YAML loader with env var substitution (162 lines)

### Files Modified
- `src/main_app/core/application.py` - Config loading integration
- `src/main_app/core/resource_manager.py` - Configuration parameters support
- `requirements.txt` - Added python-dotenv

### Testing
- Manual validation: Application starts successfully
- Configuration loaded from correct paths
- Environment variable substitution verified
- ResourceManager configured correctly from YAML

### Notes
- **Workflow**: ALPHA
- **Mission**: mission-001 (Configuration System Integration)
- **GitHub Issue**: Closes #1
- **Commit**: f0730ff
- **Full details**: [changelog/alpha/v0.2.0-alpha.1.md](changelog/alpha/v0.2.0-alpha.1.md)

---

_This file shows only the current version. Full history: [changelog/index.md](changelog/index.md)_
