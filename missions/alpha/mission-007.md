# Mission: Test Mode Implementation

**Mission ID**: MISSION-007
**Feature Reference**: FEATURE-007 (from alpha-tasks/feature-007.md)
**Priority**: P3 (Quality enhancement - not critical path)
**Status**: Active
**Estimated Complexity**: Medium

---

## Objective

Implement `--test` mode functionality that discovers and runs tests from all loaded modules using pytest. This feature provides a single command to validate system stability by executing a consolidated test suite across main/ and all loaded modules.

**Current State**: `--test` flag exists in __main__.py but returns placeholder message
**Target State**: `--test` mode discovers tests from modules and runs them with pytest

---

## Context

### Required Knowledge

**Feature-007 Goals**:
- Create test runner module with pytest integration
- Implement test discovery from loaded modules
- Support optional `get_tests()` function in module interface
- Run consolidated pytest session with all discovered tests
- Exit with appropriate code (0 for pass, 1 for fail)

**Existing Components**:
- ModuleLoader: Has `get_loaded_modules()` → List[str] and `get_module(name)` → module object
- __main__.py: Has `--test` flag (placeholder implementation at line 44-48)
- config/modules.yaml: Module configuration (may be empty initially)
- Application: Full application lifecycle (not needed in test mode)

**Module Interface Enhancement**:
Modules may optionally implement:
```python
def get_tests() -> list[str]:
    """Return list of test paths relative to module directory."""
    return ["tests/"]  # Example
```

### File References

**Files to Create**:
- `src/main_app/testing/__init__.py` (empty or exports)
- `src/main_app/testing/test_runner.py` (pytest integration, test discovery)

**Files to Modify**:
- `src/main_app/__main__.py` (replace placeholder with actual test mode)

### Dependencies Met

- Feature-004 (Module Loading) - ✅ Completed (v0.5.0-alpha.1)
- Feature-006 (Application Integration) - ✅ Completed (v0.6.0-alpha.1)
- ModuleLoader has required methods: `get_loaded_modules()`, `get_module(name)`
- Configuration system functional
- Logging setup available

---

## Specifications

### Input Requirements

**Required**:
- pytest installed (already in requirements-dev.txt)
- ModuleLoader interface (`get_loaded_modules()`, `get_module(name)`)
- Config system and logging utilities available
- Existing __main__.py with argparse setup

**Optional**:
- Modules with `get_tests()` function (gracefully handle absence)
- Main/ tests directory (tests/ at project root)

### Output Deliverables

**1. Test Runner Module** (`src/main_app/testing/test_runner.py`):
- `discover_module_tests(module, module_name) -> List[Path]`: Extract test paths from module
- `run_all_tests(module_loader, main_tests_dir) -> int`: Aggregate and run all tests
- Handles modules without `get_tests()` gracefully (log and skip)
- Validates test paths exist before adding to pytest
- Returns pytest exit code (0 for pass, 1 for fail)

**2. Test Package Init** (`src/main_app/testing/__init__.py`):
- Empty file or exports for test runner

**3. CLI Integration** (`src/main_app/__main__.py`):
- Replace placeholder test mode (lines 44-48) with actual implementation
- Load config and setup logging
- Create EventBus and ModuleLoader (with hot-reload disabled)
- Load modules from config without starting application loop
- Call `run_all_tests()` and exit with returned code

### Acceptance Criteria

**Must Have**:
- [ ] `python -m main_app --test` triggers test mode instead of placeholder
- [ ] Modules loaded but Application.start() not called (no main loop)
- [ ] Test discovery calls `get_tests()` on each loaded module (if present)
- [ ] Test paths aggregated from all modules + main/tests/
- [ ] pytest executed with collected paths in single session
- [ ] Consolidated test report printed to console
- [ ] Exit code 0 if all tests pass, 1 if any fail
- [ ] Main/ tests included automatically (tests/ directory)
- [ ] Test mode works with empty modules list (runs only main/ tests)
- [ ] Modules without `get_tests()` logged and skipped (not an error)

**Nice to Have** (ALPHA - Skip):
- Coverage report generation - Skip
- JUnit XML output - Skip
- Parallel test execution - Skip

---

## Implementation Constraints

### Code Organization

**File Structure**:
```
src/main_app/testing/
├── __init__.py          (empty or minimal exports)
└── test_runner.py       (250-300 lines max)
```

**Size Limits** (ALPHA tolerance):
- test_runner.py: Target 250-300 lines (max 400 acceptable)
- __main__.py: Grows by ~30-40 lines (currently 66 lines, target ~100-110 total)

**Architecture Rules**:
- 1 package (testing/) for test-related functionality
- Separation: test discovery vs test execution
- No test execution in normal application mode

### Technical Requirements

**Dependencies**:
- pytest (already in requirements-dev.txt)
- pathlib for path manipulation
- logging for debug/info messages

**Integration Points**:
- ModuleLoader: `get_loaded_modules()`, `get_module(name)`
- Config system: `load_all_configs(config_dir)`
- Logging: `setup_logging(config)`

**Error Handling**:
- Module `get_tests()` exceptions caught and logged (don't fail test mode)
- Invalid test paths warned and skipped
- Missing main/tests/ directory warned but not fatal
- No tests found: print warning, exit 0 (not an error)

---

## Testing Requirements

### Test Scenarios (Manual Validation - Step A8)

**Scenario 1: Run Tests from Main/ Only**
```bash
# No modules configured or modules without get_tests()
python -m main_app --test
```
Expected:
- Discovers tests in main/tests/ (if exists)
- Runs pytest with main/tests/ path
- Prints: "Running tests from 1 locations: - tests"
- Exit code 0 if tests pass

**Scenario 2: Run Tests from Modules**
```python
# Add to dummy module __init__.py
def get_tests():
    return ["tests/"]
```
```bash
python -m main_app --test
```
Expected:
- Discovers main/tests/ + module tests
- Runs pytest with both paths
- Prints: "Running tests from 2 locations..."
- Consolidated pytest report

**Scenario 3: Module Without get_tests()**
```python
# Module only has initialize()
def initialize(event_bus, config):
    pass
```
Expected:
- Logs: "Module 'mod-X' has no get_tests() function, skipping"
- Main/tests/ still runs
- No error, test mode continues

**Scenario 4: Test Failures**
```python
# In module test
def test_failing():
    assert False
```
Expected:
- pytest shows failure details
- Report: "1 failed, X passed"
- Exit code 1

**Scenario 5: No Tests Found**
```bash
# Empty tests/ everywhere
python -m main_app --test
```
Expected:
- Warning: "No tests discovered"
- Prints: "No tests found to run."
- Exit code 0 (not an error)

### Validation Method

**Step A8 Validation**:
1. Create minimal test in tests/test_example.py (just `assert True`)
2. Run `python -m main_app --test`
3. Verify test discovered and passes
4. Verify exit code 0
5. Verify logs show test mode activated

---

## Implementation Guidance

### Key Implementation Points

**1. Test Discovery Function**:
```python
def discover_module_tests(module, module_name: str) -> List[Path]:
    # Check hasattr(module, "get_tests")
    # Call module.get_tests(), validate return type
    # Convert relative paths to absolute (relative to module file)
    # Verify paths exist before returning
    # Return empty list on any error (log warning)
```

**2. Main Test Runner**:
```python
def run_all_tests(module_loader, main_tests_dir: Path = None) -> int:
    # Initialize empty list for test paths
    # Add main/tests/ if exists
    # Iterate loaded modules, call discover_module_tests()
    # If no tests found, print warning and return 0
    # Run pytest.main(["-v", "--tb=short", *test_paths])
    # Return pytest exit code
```

**3. CLI Integration** (replace lines 44-48 in __main__.py):
```python
if args.test:
    from .testing.test_runner import run_all_tests
    from .config.config_loader import load_all_configs
    from .logging.logger import setup_logging
    from .core.event_bus import EventBus
    from .core.module_loader import ModuleLoader

    # Setup (config + logging)
    # Create ModuleLoader(watch_reload=False)
    # Load modules from config
    # Call run_all_tests(module_loader)
    # sys.exit(exit_code)
```

### Patterns to Follow

**Logging**:
- INFO: Test mode start, module discovery count, paths discovered
- DEBUG: Individual module get_tests() calls
- WARNING: Missing paths, modules without get_tests(), no tests found
- ERROR: Exceptions during test discovery

**Path Handling**:
- Use pathlib.Path for all path operations
- Convert module-relative paths to absolute using `Path(module.__file__).parent`
- Verify paths exist with `path.exists()` before adding

**Error Isolation**:
- Wrap module.get_tests() in try/except
- Don't fail test mode if one module has broken get_tests()
- Log errors and continue with other modules

---

## Next Steps

### Upon Completion

**Immediate Actions**:
- Proceed to Step A8 (Manual Validation)
- Create basic test in tests/test_example.py for validation
- Run `python -m main_app --test` to verify functionality
- Test all 5 scenarios from Testing Requirements

**Follow-up Tasks**:
- Update module interface documentation (if needed)
- Create example module with get_tests() implementation (Feature-008)

### Blocked Features

**Unblocked by This Mission**:
- Feature-008 (Dummy Modules for Validation) - Can now include test examples
- Feature-009 (Demo Scenario Execution) - Can use --test for validation

---

## Success Indicators

**Mission Complete When**:
1. `python -m main_app --test` discovers and runs tests
2. All 5 test scenarios pass manual validation
3. Exit codes correct (0 for pass, 1 for fail)
4. Clear test report printed to console
5. Test mode doesn't start main application loop
6. Code follows project conventions (logging, error handling)
7. File sizes within tolerance (test_runner.py < 400 lines)

**Code Quality**:
- Clear function signatures with type hints
- Comprehensive docstrings
- Proper error handling with informative logs
- No pytest warnings or errors during execution

---

**Mission Created**: 2025-11-22
**Assigned to**: @code-implementer (Step A7)
**Next Step**: A7 (Rapid Code Implementation)
