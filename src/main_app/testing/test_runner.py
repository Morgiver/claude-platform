"""Test runner module - Discovers and executes tests from modules using pytest."""

import logging
import sys
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def discover_module_tests(module, module_name: str) -> List[Path]:
    """
    Discover test paths from a loaded module.

    Checks if the module implements the optional get_tests() function.
    If present, calls it to retrieve test paths relative to the module.
    Converts relative paths to absolute and validates they exist.

    Args:
        module: The loaded module object
        module_name: Name of the module (for logging)

    Returns:
        List of absolute Path objects pointing to test locations.
        Returns empty list if module has no get_tests() or on error.

    Note:
        Modules implementing get_tests() should return a list of string paths
        relative to the module's directory, e.g., ["tests/", "test_integration.py"]
    """
    test_paths = []

    # Check if module implements get_tests()
    if not hasattr(module, "get_tests"):
        logger.debug(f"Module '{module_name}' has no get_tests() function, skipping")
        return test_paths

    try:
        # Call get_tests() to retrieve test paths
        logger.debug(f"Calling get_tests() on module '{module_name}'")
        relative_paths = module.get_tests()

        # Validate return type
        if not isinstance(relative_paths, list):
            logger.warning(
                f"Module '{module_name}' get_tests() returned non-list: {type(relative_paths).__name__}"
            )
            return test_paths

        # Get module directory (base for relative paths)
        if not hasattr(module, "__file__") or module.__file__ is None:
            logger.warning(
                f"Module '{module_name}' has no __file__ attribute, cannot resolve test paths"
            )
            return test_paths

        module_dir = Path(module.__file__).parent

        # Convert relative paths to absolute and validate
        for rel_path in relative_paths:
            if not isinstance(rel_path, str):
                logger.warning(
                    f"Module '{module_name}' get_tests() contains non-string path: {rel_path}"
                )
                continue

            # Convert to absolute path
            abs_path = (module_dir / rel_path).resolve()

            # Validate path exists
            if not abs_path.exists():
                logger.warning(
                    f"Test path from module '{module_name}' does not exist: {abs_path}"
                )
                continue

            test_paths.append(abs_path)
            logger.debug(f"Discovered test path from '{module_name}': {abs_path}")

    except Exception as e:
        logger.error(
            f"Error calling get_tests() on module '{module_name}': {e}",
            exc_info=True,
        )
        return []

    return test_paths


def run_all_tests(
    module_loader,
    main_tests_dir: Optional[Path] = None,
) -> int:
    """
    Aggregate and run all tests from main/ and loaded modules.

    Discovers tests from:
    1. Main application tests directory (if provided and exists)
    2. All loaded modules that implement get_tests()

    Runs all discovered tests in a single pytest session and returns the exit code.

    Args:
        module_loader: ModuleLoader instance with loaded modules
        main_tests_dir: Path to main/ tests directory (default: None means use "tests/")

    Returns:
        Exit code from pytest (0 for success, 1 for failures, 2 for errors)

    Note:
        If no tests are found, prints a warning and returns 0 (not an error).
    """
    test_paths = []

    # Determine main tests directory
    if main_tests_dir is None:
        main_tests_dir = Path("tests")

    # Add main application tests if directory exists
    if main_tests_dir.exists():
        test_paths.append(main_tests_dir)
        logger.info(f"Added main tests directory: {main_tests_dir}")
    else:
        logger.warning(f"Main tests directory not found: {main_tests_dir}")

    # Discover tests from loaded modules
    try:
        loaded_modules = module_loader.get_loaded_modules()
        logger.info(f"Checking {len(loaded_modules)} loaded modules for tests")

        for module_name in loaded_modules:
            try:
                module = module_loader.get_module(module_name)
                if module is None:
                    logger.warning(f"Could not retrieve module '{module_name}'")
                    continue

                module_tests = discover_module_tests(module, module_name)
                if module_tests:
                    test_paths.extend(module_tests)
                    logger.info(
                        f"Module '{module_name}' provided {len(module_tests)} test path(s)"
                    )

            except Exception as e:
                logger.error(
                    f"Error discovering tests from module '{module_name}': {e}",
                    exc_info=True,
                )
                # Continue with other modules

    except Exception as e:
        logger.error(f"Error getting loaded modules: {e}", exc_info=True)

    # Check if any tests were found
    if not test_paths:
        print("\n[WARN] No tests discovered")
        print("No tests found to run.")
        logger.warning("No tests discovered from main/ or modules")
        return 0

    # Print test discovery summary
    print(f"\n[TEST] Running tests from {len(test_paths)} location(s):")
    for path in test_paths:
        print(f"  - {path}")
    print()

    # Run pytest with discovered paths
    try:
        import pytest

        # Build pytest arguments
        pytest_args = [
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--color=yes",  # Force color output
        ]

        # Add all test paths as strings
        pytest_args.extend([str(path) for path in test_paths])

        logger.debug(f"Running pytest with args: {pytest_args}")

        # Run pytest and capture exit code
        exit_code = pytest.main(pytest_args)

        # Log result
        if exit_code == 0:
            logger.info("All tests passed successfully")
        elif exit_code == 1:
            logger.warning("Some tests failed")
        else:
            logger.error(f"pytest exited with code {exit_code}")

        return exit_code

    except ImportError:
        print("\n[ERROR] pytest is not installed")
        print("Install with: pip install pytest")
        logger.error("pytest not installed - cannot run tests")
        return 2

    except Exception as e:
        print(f"\n[ERROR] Error running tests: {e}")
        logger.error(f"Unexpected error running pytest: {e}", exc_info=True)
        return 2
