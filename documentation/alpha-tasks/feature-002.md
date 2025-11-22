# Feature-002: Centralized Logging Setup

**Status**: ✅ completed
**Scope**: Small
**Complexity**: Low
**Priority**: P1 (Critical path - needed before module loading)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/2
**Version Completed**: v0.3.0-alpha.1

---

## Description

Enhance the existing logging utilities to use configuration from `config/main.yaml` and implement rotating file handlers with proper formatting. Replace the basic logging in `Application` with the centralized logger setup.

---

## Objectives

1. **Enhance Logger Setup**
   - Modify `logging/logger.py` to accept configuration dict
   - Implement rotating file handler based on config (max size, backup count)
   - Create logs directory automatically if it doesn't exist
   - Support configurable log levels per module (future enhancement, basic version now)

2. **Integrate with Application**
   - Replace `logging.basicConfig()` in `application.py` with `setup_logging(config)`
   - Ensure all loggers use centralized configuration
   - Log application startup with full configuration details

3. **Add Log Rotation**
   - Implement RotatingFileHandler with size limits from config
   - Console output remains active (dual logging: console + file)
   - Format logs with timestamps, module names, levels

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/logging/logger.py` (enhance `setup_logging()` to use config)
- `src/main_app/core/application.py` (replace basicConfig with centralized setup)

**Files Created**:
- `logs/` directory (auto-created on first run)
- `logs/app.log` (main log file, rotating)

**Functionality Delivered**:
- Logs written to both console and rotating files
- Log files rotate at configured size limit (10MB default)
- Backup count maintained (5 backups default)
- Log format: `YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message`
- Debug level active in ALPHA mode

---

## Dependencies

**Upstream**: Feature-001 (Configuration System) - MUST be completed first
**Downstream**: All features will use this logging system

---

## Acceptance Criteria

**Must Have**:
1. `setup_logging(config)` accepts config dict and configures logging
2. Logs written to `logs/app.log` with rotation enabled
3. Console output remains active (dual logging)
4. Log format includes timestamp, module, level, message
5. Log level respects config setting (DEBUG in ALPHA)
6. Logs directory created automatically if missing
7. Rotating file handler rotates at 10MB (or configured size)
8. Backup count maintained (max 5 old files)

**Nice to Have** (bonus, not required):
- Per-module log level configuration - **Skip in ALPHA**
- Separate log files per module - **Skip in ALPHA**
- JSON log format option - **Skip in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Basic Logging to File**
```bash
python -m main_app
# Expected: logs/app.log created with startup logs
# Check file contains: timestamp, module name, log level, message
```

**Test Case 2: Console and File Dual Output**
```bash
python -m main_app
# Expected: Logs appear in console AND written to logs/app.log
# Both should have same content and format
```

**Test Case 3: Log Rotation**
```bash
# Generate large log output (add debug logs in Application)
# Run until logs/app.log exceeds 10MB
# Expected: app.log.1 appears, app.log resets to 0 bytes
# Maximum 5 backup files (app.log.1 through app.log.5)
```

**Test Case 4: Log Level Configuration**
```bash
# Modify config/main.yaml: logging.level = "INFO"
python -m main_app
# Expected: DEBUG logs not written, INFO and above appear
# Modify back to DEBUG
# Expected: All levels appear
```

**Test Case 5: Missing Logs Directory**
```bash
# Delete logs/ directory
python -m main_app
# Expected: logs/ directory created automatically, logging works
```

---

## Implementation Notes

**Existing Code to Enhance**:
The current `logger.py` has basic structure:
```python
def setup_logging() -> None:
    """Setup logging configuration."""
    pass

def get_logger(name: str) -> logging.Logger:
    """Get logger for a module."""
    pass
```

**Enhanced Version**:
```python
def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup centralized logging with rotating file handlers.

    Args:
        config: Configuration dict from config/main.yaml
    """
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "DEBUG"))
    log_dir = Path(log_config.get("directory", "logs"))
    max_bytes = log_config.get("max_file_size_mb", 10) * 1024 * 1024
    backup_count = log_config.get("backup_count", 5)

    # Create logs directory
    log_dir.mkdir(exist_ok=True)

    # Setup format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

**Application Integration**:
```python
# In application.py main() function:
def main() -> None:
    """Main entry point."""
    # Load config
    config = load_all_configs(Path("config"))

    # Setup logging with config
    setup_logging(config)

    # Create app
    app = Application(config=config)
    app.start()
```

**Config Usage**:
From `config/main.yaml`:
```yaml
logging:
  level: "DEBUG"           # Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  directory: "logs"        # Log directory
  max_file_size_mb: 10    # Max log file size before rotation
  backup_count: 5         # Number of backup files to keep
```

---

## Rough Effort Estimate

**Time**: 1-2 hours (including testing)

**Breakdown**:
- Enhance logger.py: 30 minutes
- Integrate with Application: 15 minutes
- Manual testing: 30-45 minutes
- Log rotation testing: 15-30 minutes

---

## Success Metrics

**Functional**:
- All logs written to console and rotating file
- Log rotation works correctly (file size, backup count)
- Logs directory created automatically
- Log format is clear and consistent

**Quality**:
- logger.py remains < 200 lines
- Clear logging throughout application startup
- No logging errors or warnings during operation
- Code follows project conventions

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.1.0-alpha.1
**Previous Feature**: Feature-001 (Configuration System)
**Next Feature**: Feature-003 (Error Handling Integration)
