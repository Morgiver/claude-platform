# Feature-001: Configuration System

**Status**: 🎯 planned
**Scope**: Medium
**Complexity**: Low
**Priority**: P1 (Critical path - foundation for all features)

---

## Description

Implement a comprehensive configuration system that loads YAML configuration files and makes them available to all components. This is the foundation for declarative module loading, logging setup, and error handling strategies.

---

## Objectives

1. **Create Configuration Files**
   - Create `config/main.yaml` with global application settings
   - Create `config/modules.yaml` for declarative module loading
   - Create `.env.example` template for secrets management

2. **Implement Config Loader**
   - Create `config_loader.py` utility to load YAML files
   - Support environment variable substitution in YAML (e.g., `${WEBHOOK_API_KEY}`)
   - Validate configuration structure (basic validation, not strict schemas)

3. **Integrate with Application**
   - Modify `Application.__init__()` to load configuration
   - Pass configuration to components (EventBus, ModuleLoader, ResourceManager)
   - Store config in Application instance for access

---

## Expected Outcomes

**Files Created**:
- `config/main.yaml` (global settings: resource limits, logging, error handling)
- `config/modules.yaml` (module declarations with enable/disable flags)
- `.env.example` (template for secrets)
- `src/main_app/config/` (new package)
- `src/main_app/config/__init__.py`
- `src/main_app/config/config_loader.py` (YAML loading + env var substitution)

**Files Modified**:
- `src/main_app/core/application.py` (add config loading in `__init__()`)

**Functionality Delivered**:
- Configuration files are loaded at application startup
- Environment variable substitution works (e.g., `api_key: ${API_KEY}`)
- Invalid YAML files produce clear error messages
- Configuration accessible from Application instance

---

## Dependencies

**Upstream**: None (this is the first feature)
**Downstream**: All other features depend on this

---

## Acceptance Criteria

**Must Have**:
1. `config/main.yaml` contains all settings from tech-specifications (resources, logging, error_handling)
2. `config/modules.yaml` is structured with module list (can be empty initially)
3. `config_loader.py` successfully loads YAML files
4. Environment variable substitution works: `${VAR_NAME}` replaced with env value
5. Application loads config on startup without errors
6. Invalid YAML produces clear error message and graceful failure

**Nice to Have** (bonus, not required):
- Validation of config structure (warn if unexpected keys)
- Support for multiple config file formats (JSON, TOML) - **Skip in ALPHA**
- Config hot-reload - **Skip in ALPHA** (feature for later)

---

## Validation Approach (Manual Testing)

**Test Case 1: Load Valid Configuration**
```bash
# Create config/main.yaml and config/modules.yaml
python -m main_app
# Expected: Application starts, logs show config loaded successfully
```

**Test Case 2: Environment Variable Substitution**
```bash
# Add to config/main.yaml:
#   webhook_url: ${WEBHOOK_URL}
export WEBHOOK_URL="https://example.com/webhook"
python -m main_app
# Expected: Config contains substituted value, not ${WEBHOOK_URL}
```

**Test Case 3: Invalid YAML**
```bash
# Corrupt config/main.yaml (remove closing bracket)
python -m main_app
# Expected: Clear error message, application exits gracefully
```

**Test Case 4: Missing Config File**
```bash
# Rename config/main.yaml temporarily
python -m main_app
# Expected: Error message "Config file not found: config/main.yaml", graceful exit
```

---

## Implementation Notes

**Tech Stack**:
- `pyyaml` library (already in requirements.txt)
- `python-dotenv` for `.env` file loading (add to requirements if not present)
- Standard library `os.environ` for env var access

**Config File Templates**:

**config/main.yaml**:
```yaml
app:
  name: "main-orchestrator"
  version: "0.1.0-alpha.1"

resources:
  process_memory_mb: 512
  reserved_ram_percent: 0.25
  thread_per_core: 2

logging:
  level: "DEBUG"
  directory: "logs"
  max_file_size_mb: 10
  backup_count: 5

error_handling:
  retry_max_attempts: 3
  retry_wait_min: 1.0
  retry_wait_max: 10.0
  circuit_breaker_fail_max: 5
  circuit_breaker_reset_timeout: 60

# Optional: Webhook for critical errors
webhooks:
  critical_errors_url: "${WEBHOOK_URL}"  # From .env
```

**config/modules.yaml**:
```yaml
modules: []
# Empty for now - will be populated in Feature-004
# Example structure:
#  - name: "mod-dummy-producer"
#    path: "../modules-backend/mod-dummy-producer/__init__.py"
#    enabled: true
#    config:
#      publish_interval: 5
```

**.env.example**:
```bash
# Webhook for critical error notifications
WEBHOOK_URL=https://example.com/webhook

# Add other secrets here as needed
# API_KEY=your-api-key-here
```

**config_loader.py Structure**:
```python
import os
import yaml
from pathlib import Path
from typing import Any, Dict

def load_yaml_config(file_path: str | Path) -> Dict[str, Any]:
    """Load YAML config with env var substitution."""
    # Read file
    # Substitute ${VAR} with os.environ.get("VAR")
    # Parse YAML
    # Return dict
    pass

def load_all_configs(config_dir: Path) -> Dict[str, Any]:
    """Load main.yaml and modules.yaml."""
    # Load main config
    # Load modules config
    # Return combined dict
    pass
```

**Error Handling**:
- Missing config files: Log error, exit gracefully
- Invalid YAML syntax: Log error with line number, exit gracefully
- Missing environment variables: Log warning, use empty string as default
- Invalid config values: Log warning, use defaults from ResourceManager/Logger

---

## Rough Effort Estimate

**Time**: 2-3 hours (including testing)

**Breakdown**:
- Create config files: 30 minutes
- Implement config_loader.py: 1 hour
- Integrate with Application: 30 minutes
- Manual testing: 30-60 minutes

---

## Success Metrics

**Functional**:
- Configuration loads successfully on every startup
- Environment variables are substituted correctly
- Application gracefully handles missing/invalid config

**Quality**:
- config_loader.py < 200 lines
- Clear error messages for all failure modes
- Code follows project conventions (type hints, docstrings, logging)

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.1.0-alpha.1
**Next Feature**: Feature-002 (Centralized Logging Setup)
