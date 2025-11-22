# Mission: Centralized Logging Setup

**Mission ID**: MISSION-002
**Feature Reference**: Feature-002 (Centralized Logging Setup)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/2
**Priority**: P1 (Critical - Foundation for module loading)
**Status**: Active
**Estimated Complexity**: Low
**Estimated Effort**: 1-2 hours

---

## Objective

Enhance the existing logging utilities to use configuration from `config/main.yaml` and implement rotating file handlers with proper formatting. Replace the basic logging in `Application` with the centralized logger setup.

**Success Criteria**: All logs written to both console and rotating files with configurable levels from YAML config.

---

## Context

### What Already Exists

**Configuration System** (Feature-001 complete):
- `config/main.yaml` exists with logging configuration section
- `config_loader.py` loads YAML with environment variable substitution
- `Application` loads config at startup via `load_all_configs()`
- Configuration available in `self.config` dict

**Logging Utilities** (`logging/logger.py`):
- Basic `setup_logging()` function exists (87 lines)
- `get_logger(name)` function for module-level loggers
- **Current limitation**: Hardcoded parameters, doesn't use config

**Application Integration**:
- `Application.__init__()` calls `setup_logging()` with hardcoded parameters
- Config loaded but not passed to logging setup

### What's Needed

1. **Enhance setup_logging() Function**
   - Accept `config: Dict[str, Any]` parameter
   - Parse logging config from `config["logging"]`
   - Create logs directory automatically if missing
   - Configure rotating file handler based on config
   - Support both console and file output

2. **Update Application Integration**
   - Pass config to `setup_logging()` instead of hardcoded params
   - Ensure logging configured AFTER config loading

3. **Logging Configuration**
   - From `config/main.yaml`:
     ```yaml
     logging:
       level: "DEBUG"
       directory: "logs"
       max_file_size_mb: 10
       backup_count: 5
     ```

---

## Implementation Tasks

### Task 1: Enhance setup_logging() Function (30-45 min)

**File to Modify**: `src/main_app/logging/logger.py`

**Current Signature**:
```python
def setup_logging(
    log_dir: Path = Path("logs"),
    log_file: str = "app.log",
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
```

**New Signature**:
```python
def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup centralized logging with rotating file handlers.

    Args:
        config: Configuration dict from config/main.yaml (full config, not just logging section)
    """
```

**Implementation Steps**:
1. Extract logging config: `log_config = config.get("logging", {})`
2. Parse parameters with defaults:
   - `level = getattr(logging, log_config.get("level", "DEBUG"))`
   - `log_dir = Path(log_config.get("directory", "logs"))`
   - `max_bytes = log_config.get("max_file_size_mb", 10) * 1024 * 1024`
   - `backup_count = log_config.get("backup_count", 5)`
3. Create logs directory: `log_dir.mkdir(exist_ok=True)`
4. Setup formatters (timestamp, module, level, message)
5. Configure console handler with formatter
6. Configure RotatingFileHandler with formatter
7. Attach handlers to root logger
8. Set log level on root logger

**Example Implementation**:
```python
from pathlib import Path
from typing import Dict, Any
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(config: Dict[str, Any]) -> None:
    """Setup centralized logging with rotating file handlers."""
    log_config = config.get("logging", {})

    # Parse config
    level = getattr(logging, log_config.get("level", "DEBUG"))
    log_dir = Path(log_config.get("directory", "logs"))
    max_bytes = log_config.get("max_file_size_mb", 10) * 1024 * 1024
    backup_count = log_config.get("backup_count", 5)

    # Create logs directory
    log_dir.mkdir(exist_ok=True)

    # Setup formatter
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

    root_logger.info("Logging configured successfully")
```

**Expected Changes**:
- Remove all default parameters from function signature
- Add config dict parsing
- Add `mkdir()` call for logs directory
- Keep existing handler logic (already works)

### Task 2: Update Application Integration (15-30 min)

**File to Modify**: `src/main_app/core/application.py`

**Current Code** (in `Application.__init__()`):
```python
# Setup logging with config
from ..logging import setup_logging
logging_config = self.config.get("logging", {})
setup_logging(
    log_dir=Path(logging_config.get("directory", "logs")),
    level=logging_config.get("level", "INFO"),
    max_bytes=logging_config.get("max_file_size_mb", 10) * 1024 * 1024,
    backup_count=logging_config.get("backup_count", 5),
)
```

**New Code**:
```python
# Setup logging with config
from ..logging import setup_logging
setup_logging(self.config)  # Pass full config dict
```

**Changes**:
- Simplify call to `setup_logging()` to pass full config
- Remove manual parameter extraction
- Let `setup_logging()` handle all config parsing

**Validation**:
- Ensure config is loaded BEFORE calling `setup_logging()`
- Verify logs written to `logs/app.log` after startup
- Check console output shows same logs

### Task 3: Manual Testing (30-45 min)

**Test Case 1: Basic Logging to File**
```bash
cd E:\claude\main
python -m main_app

# Expected:
# - logs/app.log created
# - File contains: timestamp, module name, log level, message
# - Console shows same output
```

**Test Case 2: Log Level Configuration**
```bash
# Modify config/main.yaml: logging.level = "INFO"
python -m main_app

# Expected:
# - DEBUG logs not written
# - INFO and above appear in logs/app.log and console
```

**Test Case 3: Log Rotation**
```bash
# Add debug logs in Application to generate output
# Run until logs/app.log exceeds 10MB (or modify config to 1MB for testing)

# Expected:
# - app.log.1 appears when app.log exceeds max size
# - app.log resets to 0 bytes
# - Maximum 5 backup files (app.log.1 through app.log.5)
```

**Test Case 4: Missing Logs Directory**
```bash
# Delete logs/ directory
rmdir /s /q logs

python -m main_app

# Expected:
# - logs/ directory created automatically
# - Logging works without errors
```

**Test Case 5: Invalid Log Level**
```bash
# Modify config/main.yaml: logging.level = "INVALID"
python -m main_app

# Expected:
# - Error message or fallback to DEBUG
# - Application doesn't crash
```

---

## Acceptance Criteria

**Must Have**:
- [ ] `setup_logging(config)` accepts config dict and configures logging
- [ ] Logs written to `logs/app.log` with rotation enabled
- [ ] Console output remains active (dual logging)
- [ ] Log format includes timestamp, module, level, message
- [ ] Log level respects config setting (DEBUG in ALPHA)
- [ ] Logs directory created automatically if missing
- [ ] Rotating file handler rotates at configured size (10MB default)
- [ ] Backup count maintained (max 5 old files default)
- [ ] Application startup logs show "Logging configured successfully"

**Nice to Have** (bonus, skip in ALPHA):
- [ ] Per-module log level configuration
- [ ] Separate log files per module
- [ ] JSON log format option

---

## Files to Create/Modify

### Modify:
1. **src/main_app/logging/logger.py**
   - Enhance `setup_logging()` to accept config dict
   - Add directory creation logic
   - Keep existing RotatingFileHandler implementation

2. **src/main_app/core/application.py**
   - Simplify `setup_logging()` call to pass full config
   - Remove manual parameter extraction

**Expected Total Changes**:
- logger.py: ~20-30 lines modified
- application.py: ~5-10 lines simplified
- Total: ~30-40 lines of code changes

---

## Implementation Constraints

### ALPHA Constraints:
- Prefer simplicity over completeness
- Manual testing acceptable (no automated tests required)
- Basic error handling sufficient (no strict schema validation)
- File size limit: 1500 lines (current logger.py: 87 lines, well below)

### Code Quality:
- Use type hints for function signature
- Update docstrings for `setup_logging()`
- Log all setup steps (directory creation, handler attachment)
- Follow existing naming conventions (snake_case)

### Error Handling:
- Invalid log level: Fallback to DEBUG with warning
- Missing config section: Use defaults with warning
- Directory creation failure: Log error, raise exception
- Handler creation failure: Log error, raise exception

---

## Testing Requirements

### Manual Testing (Required):
1. Start application with valid config
2. Verify logs written to console AND file
3. Check log format is correct
4. Test log rotation (simulate large log output)
5. Test missing logs directory (auto-creation)

### Validation Method:
- Inspect `logs/app.log` for entries
- Verify log format: `YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message`
- Check rotation: `app.log.1`, `app.log.2`, etc. appear when size exceeded
- Verify console output matches file output

---

## Dependencies

**Upstream**: Feature-001 (Configuration System) - COMPLETED in v0.2.0-alpha.1
**Downstream**: All future features will use this logging system

**Configuration Available**:
- `self.config` loaded in Application.__init__()
- `config["logging"]` section available from main.yaml
- Config loading working correctly (Feature-001 validated)

---

## Next Steps

### Upon Completion:
1. **Proceed to Step A8**: Manual Validation & Debug
2. **Update Feature-002 status**: Mark as "in-progress" → "completed"
3. **Prepare for Feature-003**: Error Handling Integration (will use centralized logging)

### Blocked Features Unblocked:
- Feature-003 (Error Handling) - Will use centralized logging
- Feature-004 (Module Loading) - Will log module lifecycle events
- All future features - Logging foundation established

---

## Notes

**Quick Wins**:
- Logger utilities already exist (87 lines)
- Config loading already working (Feature-001 complete)
- RotatingFileHandler logic already implemented
- Just need to wire config into existing function

**Complexity Assessment**:
- Low complexity (configuration integration only)
- Clear implementation path
- Well-defined success criteria

**ALPHA Philosophy**:
- Focus on making it work, not making it perfect
- Skip per-module log levels (can add in BETA)
- Skip JSON format (can add in BETA)
- Manual testing acceptable

**Current State Reference**:
From `current-state.md`:
- Logger utilities exist at 87 lines
- Application already calls `setup_logging()` with hardcoded params
- Config system working (Feature-001 complete)
- Just need integration work

---

**Mission Created**: 2025-11-22
**Ready for @code-implementer**: Step A7 (Rapid Code Implementation)
**Workflow Version**: ALPHA
