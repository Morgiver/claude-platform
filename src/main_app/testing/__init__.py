"""Testing package - Test discovery and execution."""

from .test_runner import discover_module_tests, run_all_tests

__all__ = ["discover_module_tests", "run_all_tests"]
