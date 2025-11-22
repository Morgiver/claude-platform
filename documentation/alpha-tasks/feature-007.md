# Feature-007: Test Mode Implementation

**Status**: 🎯 planned
**Scope**: Large
**Complexity**: Medium
**Priority**: P3 (Quality enhancement - not critical path)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/7

---

## Description

Implement `--test` mode that discovers and runs tests from all loaded modules. This feature integrates pytest to execute a consolidated test suite across main/ and all loaded modules, providing a single command to validate system stability.

---

## Objectives

1. **Create Test Runner Module**
   - Create `testing/` package in main_app
   - Implement `test_runner.py` with pytest integration
   - Support test discovery from multiple modules
   - Generate consolidated test report

2. **Module Test Discovery**
   - Define optional `get_tests()` function in module interface
   - Modules return list of test paths (directories or files)
   - Aggregate test paths from all loaded modules
   - Include main/ tests in discovery

3. **Pytest Integration**
   - Use pytest for test execution (already in requirements-dev.txt)
   - Collect all test paths and run in single session
   - Capture test results (passed, failed, skipped)
   - Generate report with summary and exit code

4. **CLI Integration**
   - Handle `--test` flag in `__main__.py`
   - Load modules (without starting main loop)
   - Discover tests from modules
   - Run tests and exit with appropriate code

---

## Expected Outcomes

**Files Created**:
- `src/main_app/testing/` (new package)
- `src/main_app/testing/__init__.py`
- `src/main_app/testing/test_runner.py` (pytest integration and test discovery)

**Files Modified**:
- `src/main_app/__main__.py` (handle --test flag)
- Module interface documentation (add get_tests() optional function)

**Functionality Delivered**:
- `python -m main_app --test` discovers and runs all tests
- Tests discovered from main/ and all loaded modules
- Consolidated pytest report generated
- Exit code: 0 if all pass, 1 if any fail
- Test mode doesn't start main application loop

---

## Dependencies

**Upstream**:
- Feature-004 (Module Loading) - MUST be completed
- Feature-006 (Application Integration) - MUST be completed

**Downstream**: None (this is a quality enhancement feature)

---

## Acceptance Criteria

**Must Have**:
1. `--test` flag triggers test mode instead of normal startup
2. Modules loaded but application main loop not started
3. `get_tests()` called on each loaded module (if present)
4. Test paths aggregated from all modules
5. pytest runs with collected test paths
6. Consolidated test report printed to console
7. Exit code 0 if all tests pass, 1 if any fail
8. Main/ tests included in discovery automatically
9. Test mode works with empty modules list (runs only main/ tests)

**Nice to Have** (bonus, not required):
- Coverage report generation - **Optional in ALPHA**
- JUnit XML output for CI/CD - **Optional in ALPHA**
- Parallel test execution - **Skip in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Run Tests from Main/ Only**
```bash
# No modules configured
python -m main_app --test
# Expected:
#   - Discovers tests in main/tests/
#   - Runs pytest
#   - Prints report: "X passed in Y.YYs"
#   - Exit code 0
```

**Test Case 2: Run Tests from Modules**
```python
# In dummy module __init__.py
def get_tests():
    return ["tests/"]  # Relative to module directory
```
```bash
python -m main_app --test
# Expected:
#   - Discovers main/ tests
#   - Discovers dummy module tests
#   - Runs all tests in single pytest session
#   - Prints report: "X passed in Y.YYs"
```

**Test Case 3: Module Without get_tests()**
```python
# Module doesn't implement get_tests()
def initialize(event_bus, config):
    pass
```
```bash
python -m main_app --test
# Expected:
#   - Module loaded successfully
#   - No tests discovered from module (not an error)
#   - Main/ tests still run
#   - Logs: "Module 'mod-X' has no get_tests() function, skipping"
```

**Test Case 4: Test Failures Reported**
```python
# In module test file
def test_failing():
    assert False, "This test should fail"
```
```bash
python -m main_app --test
# Expected:
#   - Test runs and fails
#   - Report shows: "1 failed, X passed"
#   - Exit code 1
#   - Failure details printed
```

**Test Case 5: No Tests Found**
```bash
# Empty tests/ directories everywhere
python -m main_app --test
# Expected:
#   - Message: "No tests discovered"
#   - Exit code 0 (not an error)
```

---

## Implementation Notes

**Module Interface Enhancement**:

```python
# Optional function in module interface
def get_tests() -> list[str]:
    """
    Return list of test paths for --test mode.

    Returns:
        List of test directory or file paths relative to module directory.
        Examples: ["tests/"], ["tests/unit/", "tests/integration/"]

    Note:
        This function is optional. If not implemented, module will not
        contribute tests to --test mode.
    """
    return ["tests/"]
```

**Test Runner Implementation**:

```python
# src/main_app/testing/test_runner.py

import logging
import sys
from pathlib import Path
from typing import List
import pytest

logger = logging.getLogger(__name__)


def discover_module_tests(module, module_name: str) -> List[Path]:
    """
    Discover tests from a module.

    Args:
        module: Loaded module object
        module_name: Name of the module

    Returns:
        List of test paths
    """
    if not hasattr(module, "get_tests"):
        logger.debug(f"Module '{module_name}' has no get_tests() function, skipping")
        return []

    try:
        test_paths = module.get_tests()
        if not isinstance(test_paths, list):
            logger.warning(f"Module '{module_name}' get_tests() didn't return list")
            return []

        # Convert to absolute paths (relative to module location)
        module_file = Path(module.__file__).parent
        absolute_paths = []
        for path_str in test_paths:
            abs_path = (module_file / path_str).resolve()
            if abs_path.exists():
                absolute_paths.append(abs_path)
                logger.info(f"Discovered tests from '{module_name}': {abs_path}")
            else:
                logger.warning(f"Test path doesn't exist: {abs_path}")

        return absolute_paths

    except Exception as e:
        logger.error(f"Error discovering tests from '{module_name}': {e}", exc_info=True)
        return []


def run_all_tests(module_loader, main_tests_dir: Path = None) -> int:
    """
    Run all tests from main/ and loaded modules.

    Args:
        module_loader: ModuleLoader instance with loaded modules
        main_tests_dir: Path to main/ tests directory (default: tests/)

    Returns:
        Exit code: 0 if all pass, 1 if any fail
    """
    logger.info("Starting test discovery...")

    all_test_paths: List[Path] = []

    # Discover main/ tests
    if main_tests_dir is None:
        main_tests_dir = Path("tests")

    if main_tests_dir.exists():
        all_test_paths.append(main_tests_dir)
        logger.info(f"Discovered main/ tests: {main_tests_dir}")
    else:
        logger.warning(f"Main tests directory not found: {main_tests_dir}")

    # Discover module tests
    loaded_modules = module_loader.get_loaded_modules()
    logger.info(f"Discovering tests from {len(loaded_modules)} loaded modules...")

    for module_name in loaded_modules:
        module = module_loader.get_module(module_name)
        if module:
            module_paths = discover_module_tests(module, module_name)
            all_test_paths.extend(module_paths)

    # Check if any tests found
    if not all_test_paths:
        logger.warning("No tests discovered")
        print("\nNo tests found to run.")
        return 0

    # Convert paths to strings for pytest
    test_path_strs = [str(p) for p in all_test_paths]

    logger.info(f"Running tests from {len(test_path_strs)} paths...")
    print(f"\n{'='*70}")
    print(f"Running tests from {len(test_path_strs)} locations:")
    for path in test_path_strs:
        print(f"  - {path}")
    print(f"{'='*70}\n")

    # Run pytest
    try:
        exit_code = pytest.main([
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            *test_path_strs
        ])

        return exit_code

    except Exception as e:
        logger.error(f"Failed to run tests: {e}", exc_info=True)
        return 1
```

**CLI Integration**:

```python
# src/main_app/__main__.py

def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="main/ - Modular Orchestration Platform"
    )
    parser.add_argument("--config-dir", type=Path, default=Path("config"))
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--test", action="store_true",
                       help="Run test mode (discover and run module tests)")

    args = parser.parse_args()

    # Handle version
    if args.version:
        print("main-orchestrator v0.1.0-alpha.1")
        sys.exit(0)

    # Handle test mode
    if args.test:
        from .testing.test_runner import run_all_tests
        from .config.config_loader import load_all_configs
        from .logging.logger import setup_logging
        from .core.event_bus import EventBus
        from .core.module_loader import ModuleLoader

        # Load config and setup logging
        config = load_all_configs(args.config_dir)
        setup_logging(config)

        logger.info("=== TEST MODE ===")
        logger.info("Loading modules for test discovery...")

        # Load modules (but don't start application)
        event_bus = EventBus()
        module_loader = ModuleLoader(watch_reload=False)  # Disable hot-reload in test mode

        # Load modules
        modules_config = config.get("modules", [])
        for module_data in modules_config:
            from .core.module_loader import ModuleConfig
            config_obj = ModuleConfig(
                name=module_data["name"],
                path=module_data["path"],
                enabled=module_data.get("enabled", True),
                config=module_data.get("config", {})
            )
            module_loader.load_module(config_obj)

        # Run tests
        exit_code = run_all_tests(module_loader)

        logger.info(f"Test mode completed with exit code {exit_code}")
        sys.exit(exit_code)

    # Normal mode: Start application
    try:
        app = Application(config_dir=args.config_dir)
        app.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)
```

**Usage Examples**:
```bash
# Run all tests
python -m main_app --test

# Run tests with custom config
python -m main_app --config-dir /path/to/config --test

# CI/CD integration
python -m main_app --test && echo "All tests passed!" || echo "Tests failed!"
```

---

## Rough Effort Estimate

**Time**: 4-5 hours (including testing)

**Breakdown**:
- Create test_runner.py: 2 hours
- Integrate with __main__.py: 1 hour
- Create test fixtures and examples: 1 hour
- Manual testing: 1-2 hours

---

## Success Metrics

**Functional**:
- `--test` mode discovers and runs all tests
- Tests from main/ and modules aggregated correctly
- Exit codes correct (0 for pass, 1 for fail)
- Clear test report printed
- Test mode doesn't start main application loop

**Quality**:
- test_runner.py < 300 lines
- Clear error messages for test discovery issues
- Comprehensive logging in test mode
- Code follows project conventions

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.4.0-alpha.1 or v0.5.0-alpha.1
**Previous Feature**: Feature-006 (Application Startup & Integration)
**Next Feature**: Feature-008 (Dummy Modules for Validation)
