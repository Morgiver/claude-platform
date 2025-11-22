# Mission: Configuration System Integration

**Mission ID**: MISSION-001
**Feature Reference**: Feature-001 (Configuration System)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/1
**Priority**: P1 (Critical - Foundation for all features)
**Status**: Active
**Estimated Complexity**: Low
**Estimated Effort**: 2-3 hours

---

## Objective

Integrate YAML configuration loading into the Application class to enable declarative configuration of the orchestrator. Configuration files already exist and need to be loaded and distributed to core components.

**Success Criteria**: Application loads configuration files at startup and makes them available to all components.

---

## Context

### What Already Exists

**Configuration Files** (already created):
- `config/main.yaml` - Global application settings (resources, logging, error handling)
- `config/modules.yaml` - Module declarations (currently empty, ready for Feature-004)
- `config/logging.yaml` - Detailed logging configuration
- `.env.example` - Template for environment variables

**Core Components** (already implemented):
- `Application` class - Main orchestrator (needs config loading)
- `EventBus` - Event broker (works with defaults)
- `ModuleLoader` - Dynamic module loading (needs config)
- `ResourceManager` - System resource monitoring (needs config)
- `setup_logging()` - Logging setup utility (needs config)

**Dependencies Available**:
- PyYAML (already in requirements.txt)
- python-dotenv (needs to be added to requirements.txt)

### What's Needed

1. **Config Loader Utility** - Load YAML files with environment variable substitution
2. **Application Integration** - Load config in `Application.__init__()`
3. **Component Configuration** - Pass config to ResourceManager, ModuleLoader, Logger
4. **Error Handling** - Graceful handling of missing/invalid config files

---

## Implementation Tasks

### Task 1: Create Config Loader Utility (30-45 min)

**Action**: Create `src/main_app/config/` package with config loading logic

**Files to Create**:
- `src/main_app/config/__init__.py`
- `src/main_app/config/config_loader.py`

**Config Loader Requirements**:
- Load YAML configuration files using PyYAML
- Support environment variable substitution (`${VAR_NAME}` → `os.environ.get("VAR_NAME")`)
- Handle missing files gracefully (log error, raise exception)
- Handle invalid YAML gracefully (log error with line number, raise exception)
- Provide clear error messages for all failure modes

**Function Signatures**:
```python
def load_yaml_config(file_path: str | Path) -> Dict[str, Any]:
    """Load YAML config with environment variable substitution."""
    pass

def load_all_configs(config_dir: Path = Path("config")) -> Dict[str, Any]:
    """Load main.yaml and modules.yaml, return combined configuration."""
    pass
```

**Expected Behavior**:
- Environment variables like `${WEBHOOK_URL}` are replaced with actual values
- Missing environment variables use empty string as default (with warning log)
- Invalid YAML produces clear error message and raises exception
- Missing config files produce clear error message and raise exception

### Task 2: Add python-dotenv Dependency (5 min)

**Action**: Add `python-dotenv` to `requirements.txt`

**Why**: Load environment variables from `.env` file for local development

**Usage**:
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file before loading YAML configs
```

### Task 3: Integrate Config Loading in Application (30-45 min)

**Action**: Modify `src/main_app/core/application.py` to load configuration

**Changes Needed**:

**In `Application.__init__()`**:
1. Load environment variables from `.env` file
2. Load configuration from YAML files
3. Store config in instance variable
4. Pass config to ResourceManager, ModuleLoader
5. Call `setup_logging()` with config parameters

**Example**:
```python
from dotenv import load_dotenv
from ..config import load_all_configs
from pathlib import Path

class Application:
    def __init__(self, config_dir: Path | None = None):
        # Load environment variables
        load_dotenv()

        # Load configuration
        self.config_dir = config_dir or Path("config")
        self.config = load_all_configs(self.config_dir)

        # Setup logging with config
        from ..logging import setup_logging
        logging_config = self.config.get("logging", {})
        setup_logging(
            log_dir=Path(logging_config.get("directory", "logs")),
            level=logging_config.get("level", "INFO"),
            max_bytes=logging_config.get("max_file_size_mb", 10) * 1024 * 1024,
            backup_count=logging_config.get("backup_count", 5),
        )

        # Initialize components with config
        resource_config = self.config.get("resources", {})
        self.resource_manager = ResourceManager(
            process_memory_mb=resource_config.get("process_memory_mb", 512),
            reserved_ram_percent=resource_config.get("reserved_ram_percent", 0.25),
        )

        # ... rest of initialization
```

**Files to Modify**:
- `src/main_app/core/application.py` (add config loading, modify __init__)

### Task 4: Update ResourceManager Constructor (15 min)

**Action**: Modify `ResourceManager.__init__()` to accept configuration parameters

**Current**: Uses hardcoded constants `PROCESS_MEMORY_MB`, `RESERVED_RAM_PERCENT`
**New**: Accept constructor parameters with defaults

**Changes**:
```python
class ResourceManager:
    def __init__(
        self,
        process_memory_mb: int = 512,
        reserved_ram_percent: float = 0.25,
    ):
        self.process_memory_mb = process_memory_mb
        self.reserved_ram_percent = reserved_ram_percent
```

**Files to Modify**:
- `src/main_app/core/resource_manager.py` (update constructor)

### Task 5: Manual Testing (30-45 min)

**Test Cases to Execute**:

**Test 1: Valid Configuration**
```bash
python -m main_app
# Expected: Application starts, logs show "Config loaded successfully"
# Verify: Logs show correct values from config files
```

**Test 2: Environment Variable Substitution**
```bash
# Add to .env file:
WEBHOOK_URL=https://example.com/webhook

python -m main_app
# Expected: Config contains substituted value
# Verify: Log shows webhook URL loaded correctly
```

**Test 3: Missing Config File**
```bash
# Temporarily rename config/main.yaml
mv config/main.yaml config/main.yaml.bak

python -m main_app
# Expected: Clear error message "Config file not found: config/main.yaml"
# Expected: Application exits gracefully (no crash)
```

**Test 4: Invalid YAML**
```bash
# Corrupt config/main.yaml (add invalid syntax)
echo "invalid: yaml: {{{" >> config/main.yaml

python -m main_app
# Expected: Clear error message with line number
# Expected: Application exits gracefully
```

---

## Acceptance Criteria

**Must Have**:
- [ ] `config_loader.py` successfully loads YAML files
- [ ] Environment variable substitution works (`${VAR}` → actual value)
- [ ] Application loads config on startup without errors
- [ ] Config passed to ResourceManager with correct values
- [ ] Logging configured from YAML config
- [ ] Invalid YAML produces clear error message and graceful exit
- [ ] Missing config file produces clear error message and graceful exit
- [ ] Missing environment variables log warning and use empty string default

**Nice to Have** (bonus):
- [ ] Validation of config structure (warn if unexpected keys)
- [ ] Config schema documentation

---

## Files to Create/Modify

### Create:
1. `src/main_app/config/__init__.py` (exports: load_all_configs, load_yaml_config)
2. `src/main_app/config/config_loader.py` (YAML loading + env var substitution)

### Modify:
1. `src/main_app/core/application.py` (add config loading in __init__)
2. `src/main_app/core/resource_manager.py` (accept config parameters)
3. `requirements.txt` (add python-dotenv)

**Expected Total Lines**:
- config_loader.py: ~150-200 lines
- application.py: +30-40 lines (modifications)
- resource_manager.py: +10-15 lines (modifications)
- Total: ~200-250 lines of new/modified code

---

## Implementation Constraints

### ALPHA Constraints:
- Prefer simplicity over completeness
- Manual testing acceptable (no automated tests required)
- Basic error handling sufficient (no strict schema validation)
- File size limit: 1500 lines (current files well below)

### Code Quality:
- Use type hints for all functions
- Add docstrings for public functions
- Log all errors with context
- Follow existing naming conventions (snake_case for files/functions)

### Error Handling:
- Missing config files: Log error, raise FileNotFoundError
- Invalid YAML: Log error with line number, raise yaml.YAMLError
- Missing environment variables: Log warning, use empty string default
- Invalid config values: Log warning, use hardcoded defaults

---

## Testing Requirements

### Manual Testing (Required):
1. Start application with valid config → Success
2. Start with env var substitution → Substitution works
3. Start with missing config file → Clear error, graceful exit
4. Start with invalid YAML → Clear error, graceful exit

### Validation Method:
- Inspect logs for config loading messages
- Verify ResourceManager uses config values (check logs)
- Verify logging uses config values (check log file location/level)
- Verify graceful error handling (no stack traces for expected errors)

---

## Next Steps

### Upon Completion:
1. **Proceed to Step A8**: Manual Validation & Debug
2. **Update Feature-001 status**: Mark as "in-progress" → "completed"
3. **Prepare for Feature-002**: Centralized logging (uses config from this mission)

### Blocked Features Unblocked:
- Feature-002 (Centralized Logging) - Will use logging config
- Feature-004 (Module Loading) - Will use modules.yaml config
- Feature-006 (Application Integration) - Depends on config system

---

## Notes

**Quick Wins**:
- Config files already created (main.yaml, modules.yaml, logging.yaml)
- PyYAML already in requirements.txt
- Components designed to accept configuration

**Complexity Assessment**:
- Low complexity (straightforward YAML loading + wiring)
- Clear implementation path
- Well-defined success criteria

**ALPHA Philosophy**:
- Focus on making it work, not making it perfect
- Basic validation sufficient (strict schemas in BETA)
- Manual testing acceptable

---

**Mission Created**: 2025-11-22
**Ready for @code-implementer**: Step A7 (Rapid Code Implementation)
**Workflow Version**: ALPHA
