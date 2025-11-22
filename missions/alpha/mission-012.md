# Mission 012 - Refinement-003: Multi-Platform Compatibility

**Type**: ALPHA Refinement / Enhancement
**Feature**: Refinement-003
**Objective**: Add explicit cross-platform compatibility (Windows, Linux, macOS)
**Context**: Post-refinement-002 (exit code investigation)
**Estimated Effort**: 2-3 hours

---

## Mission Objective

Implement explicit multi-platform compatibility to ensure the application works correctly and consistently across Windows, Linux, and macOS. Build on the knowledge gained from Refinement-002 about platform-specific exit code behaviors.

**Current State**: Application works on Windows, platform behaviors are implicit
**Target State**: Explicit platform detection, adaptation, and documentation

---

## Background from Refinement-002

We discovered that exit code 1 from `proc.terminate()` is Windows-specific behavior (TerminateProcess API), while Linux/macOS use SIGTERM signals (exit code 0 or -15). This revealed the need for explicit cross-platform handling.

**Platform Differences Discovered**:
- Windows: `proc.terminate()` → TerminateProcess() → exit code 1
- Linux/macOS: `proc.terminate()` → SIGTERM signal → exit code 0/-15
- Signal availability varies by platform

---

## Implementation Plan

### Task 1: Create Platform Utility Module

**Action**: Create new utility module for platform detection and helpers

**New File**: `src/main_app/utils/__init__.py` (empty)
**New File**: `src/main_app/utils/platform_utils.py`

**Content**:

```python
"""
Platform detection and compatibility utilities.

Provides cross-platform abstractions for:
- Platform detection (Windows, Linux, macOS)
- Exit code interpretation
- Signal availability
- Path handling verification
"""

import platform
import sys
from dataclasses import dataclass
from typing import Literal

PlatformType = Literal['Windows', 'Linux', 'Darwin', 'Unknown']

@dataclass
class PlatformInfo:
    """Platform information and detection."""

    system: str  # 'Windows', 'Linux', 'Darwin', etc.
    release: str  # OS version
    version: str  # Detailed version
    machine: str  # Architecture (x86_64, ARM64, etc.)
    python_version: str  # Python version
    is_windows: bool
    is_linux: bool
    is_macos: bool

    @property
    def display_name(self) -> str:
        """Human-readable platform name."""
        if self.is_windows:
            return f"Windows {self.release}"
        elif self.is_linux:
            return f"Linux {self.release}"
        elif self.is_macos:
            return f"macOS {self.release}"
        else:
            return f"{self.system} {self.release}"

    @property
    def is_unix(self) -> bool:
        """Check if platform is Unix-like (Linux or macOS)."""
        return self.is_linux or self.is_macos


def get_platform_info() -> PlatformInfo:
    """
    Get current platform information.

    Returns:
        PlatformInfo: Detected platform details

    Example:
        >>> info = get_platform_info()
        >>> if info.is_windows:
        ...     print("Running on Windows")
    """
    system = platform.system()

    return PlatformInfo(
        system=system,
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        is_windows=(system == 'Windows'),
        is_linux=(system == 'Linux'),
        is_macos=(system == 'Darwin')
    )


def is_clean_exit_code(exit_code: int) -> bool:
    """
    Check if exit code represents a clean shutdown.

    Platform-specific exit code handling:
    - Windows: 0 (success), 1 (TerminateProcess - acceptable)
    - Linux/macOS: 0 (success), -15 or 143 (SIGTERM - acceptable)

    Args:
        exit_code: Process exit code to check

    Returns:
        bool: True if exit code represents clean shutdown

    Example:
        >>> is_clean_exit_code(0)  # All platforms
        True
        >>> is_clean_exit_code(1)  # Windows only
        True (on Windows), False (on Linux/macOS)
    """
    info = get_platform_info()

    if info.is_windows:
        # Windows: 0 (clean) or 1 (TerminateProcess acceptable)
        return exit_code in [0, 1]
    else:
        # Linux/macOS: 0 (clean), -15 or 143 (SIGTERM variations)
        return exit_code in [0, -15, 143]


def get_available_signals() -> dict:
    """
    Get available signals for current platform.

    Returns:
        dict: Signal name → signal number mapping

    Example:
        >>> signals = get_available_signals()
        >>> 'SIGINT' in signals  # Available on all platforms
        True
        >>> 'SIGHUP' in signals  # Unix only
        True (on Linux/macOS), False (on Windows)
    """
    import signal

    available = {
        'SIGINT': signal.SIGINT,
        'SIGTERM': signal.SIGTERM
    }

    info = get_platform_info()

    if info.is_windows:
        # Windows-specific signals
        if hasattr(signal, 'SIGBREAK'):
            available['SIGBREAK'] = signal.SIGBREAK
    else:
        # Unix-specific signals
        if hasattr(signal, 'SIGHUP'):
            available['SIGHUP'] = signal.SIGHUP
        if hasattr(signal, 'SIGQUIT'):
            available['SIGQUIT'] = signal.SIGQUIT

    return available


def get_platform_resource_limits() -> dict:
    """
    Get platform-optimized resource limits.

    Returns recommended process/thread limits based on platform capabilities.

    Returns:
        dict: Resource limit recommendations

    Example:
        >>> limits = get_platform_resource_limits()
        >>> limits['max_processes']  # Platform-specific
        32 (Windows), 128 (Linux), 64 (macOS)
    """
    import multiprocessing

    cpu_count = multiprocessing.cpu_count()
    info = get_platform_info()

    if info.is_windows:
        # Windows: More conservative limits
        return {
            'max_processes': min(cpu_count * 2, 32),
            'max_threads': min(cpu_count * 4, 128),
            'reason': 'Windows process overhead'
        }
    elif info.is_macos:
        # macOS: Moderate limits
        return {
            'max_processes': min(cpu_count * 2, 64),
            'max_threads': min(cpu_count * 4, 256),
            'reason': 'macOS security restrictions'
        }
    else:  # Linux
        # Linux: More aggressive limits (better scaling)
        return {
            'max_processes': min(cpu_count * 4, 128),
            'max_threads': min(cpu_count * 8, 512),
            'reason': 'Linux process efficiency'
        }
```

**Validation**:
- Import module successfully
- `get_platform_info()` returns correct Windows info
- `is_clean_exit_code(0)` returns True
- `is_clean_exit_code(1)` returns True (on Windows)

---

### Task 2: Add Platform Logging to Application Startup

**File to Modify**: `src/main_app/core/application.py`

**Changes**:

1. **Import platform utils**:
```python
from ..utils.platform_utils import get_platform_info, get_available_signals
```

2. **Add platform logging in `start()` method** (after line 216):
```python
def start(self) -> None:
    """Start the application."""
    logger.info("Starting application...")

    # NEW: Log platform information
    platform_info = get_platform_info()
    logger.info(f"Platform: {platform_info.display_name}")
    logger.info(f"Architecture: {platform_info.machine}")
    logger.info(f"Python: {platform_info.python_version}")

    # NEW: Log available signals
    available_signals = get_available_signals()
    logger.debug(f"Available signals: {', '.join(available_signals.keys())}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    # ... rest of existing code ...
```

**Validation**:
- Application starts successfully
- Logs show: `Platform: Windows <version>`
- Logs show: `Architecture: AMD64` (or current)
- Logs show: `Python: 3.13.7` (or current)

---

### Task 3: Platform-Aware Signal Handler Registration

**File to Modify**: `src/main_app/core/application.py`

**Changes in `start()` method** (replace signal registration section):

```python
# Register signal handlers based on platform
platform_info = get_platform_info()  # Already fetched above
available_signals = get_available_signals()

# Common signals (all platforms)
signal.signal(signal.SIGINT, self._signal_handler)
signal.signal(signal.SIGTERM, self._signal_handler)
logger.info("Registered SIGINT and SIGTERM handlers")

# Platform-specific signals
if platform_info.is_windows:
    if 'SIGBREAK' in available_signals:
        signal.signal(available_signals['SIGBREAK'], self._signal_handler)
        logger.debug("Registered Windows SIGBREAK handler")
else:  # Unix (Linux, macOS)
    if 'SIGHUP' in available_signals:
        signal.signal(available_signals['SIGHUP'], self._signal_handler)
        logger.debug("Registered Unix SIGHUP handler")
    if 'SIGQUIT' in available_signals:
        signal.signal(available_signals['SIGQUIT'], self._signal_handler)
        logger.debug("Registered Unix SIGQUIT handler")
```

**Validation**:
- Application logs show signal handler registration
- Windows: SIGINT, SIGTERM, SIGBREAK registered
- No errors during startup

---

### Task 4: Update Demo Script for Platform-Aware Validation

**File to Modify**: `demo.py`

**Changes**:

1. **Add import at top**:
```python
import sys
import os

# Add src to path to import platform_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from main_app.utils.platform_utils import is_clean_exit_code, get_platform_info
```

2. **Update `validate_graceful_shutdown()` method**:
```python
def validate_graceful_shutdown(self):
    """Validate graceful shutdown (platform-aware)."""
    self.print_step(6, 7, "Testing graceful shutdown")

    # ... existing process start code ...

    exit_code = proc.returncode

    # Platform-aware exit code validation
    platform_info = get_platform_info()

    if is_clean_exit_code(exit_code):
        self.print_success(
            f"Graceful shutdown successful "
            f"(exit code: {exit_code}, platform: {platform_info.system})"
        )
    else:
        self.print_error(
            f"Unexpected exit code: {exit_code} "
            f"(platform: {platform_info.system})"
        )
        return False

    return True
```

**Validation**:
- Demo script runs successfully
- Graceful shutdown passes with exit code 1 (Windows)
- Message shows platform: Windows

---

### Task 5: Update Resource Manager with Platform Limits

**File to Modify**: `src/main_app/core/resource_manager.py`

**Changes**:

1. **Import platform utils**:
```python
from ..utils.platform_utils import get_platform_resource_limits, get_platform_info
```

2. **Update `_calculate_limits()` method**:
```python
def _calculate_limits(self) -> None:
    """Calculate resource limits based on system resources."""
    cpu_count = multiprocessing.cpu_count()
    total_ram_gb = self._get_total_ram_gb()

    # Get platform-optimized defaults
    platform_limits = get_platform_resource_limits()
    platform_info = get_platform_info()

    # Calculate limits (use platform-aware defaults)
    self.max_processes = platform_limits['max_processes']
    self.max_threads = platform_limits['max_threads']

    logger.info(
        f"Resource limits calculated: "
        f"{self.max_processes} processes, {self.max_threads} threads "
        f"(platform: {platform_info.system}, reason: {platform_limits['reason']})"
    )
```

**Validation**:
- Application logs show platform-specific limits
- Windows: 32 processes, 128 threads (or calculated)
- Reason logged: "Windows process overhead"

---

### Task 6: Add Platform Info to --version

**File to Modify**: `src/main_app/__main__.py`

**Changes in `--version` handling**:

```python
# Handle --version flag
if args.version:
    from .utils.platform_utils import get_platform_info

    platform_info = get_platform_info()

    print("Main Application v0.11.0-alpha.1")
    print("ALPHA Development Version")
    print(f"Platform: {platform_info.display_name}")
    print(f"Architecture: {platform_info.machine}")
    print(f"Python: {platform_info.python_version}")
    sys.exit(0)
```

**Validation**:
- Run: `python -m main_app --version`
- Output shows platform information

---

## Acceptance Criteria

**Must Have**:
1. ✅ Platform utils module created and functional
2. ✅ Application logs platform info at startup
3. ✅ Signal handlers registered based on platform
4. ✅ Demo script uses platform-aware exit code validation
5. ✅ Resource manager uses platform-specific limits
6. ✅ `--version` shows platform information

**Validation** (on Windows):
- Application starts and logs: `Platform: Windows <version>`
- Demo script passes with platform-aware message
- Ctrl+C works (exit code 0)
- proc.terminate() acceptable (exit code 1, platform: Windows)
- All modules load successfully

**Code Quality**:
- Type hints used (PlatformInfo dataclass)
- Docstrings for all public functions
- Platform checks are explicit and readable
- No platform-specific code outside platform_utils.py

---

## Files Modified Summary

**New Files**:
- `src/main_app/utils/__init__.py` (empty package init)
- `src/main_app/utils/platform_utils.py` (~150 lines)

**Modified Files**:
- `src/main_app/core/application.py` (+15 lines)
- `src/main_app/core/resource_manager.py` (+10 lines)
- `src/main_app/__main__.py` (+6 lines)
- `demo.py` (+8 lines)

**Documentation**:
- `documentation/alpha-tasks/refinement-003.md` (already created)

**Total Lines Changed**: ~190 lines (new + modifications)

---

## Testing Strategy

### Test 1: Platform Detection

```python
from main_app.utils.platform_utils import get_platform_info

info = get_platform_info()
assert info.is_windows == True  # On Windows
assert info.system == 'Windows'
print(f"✅ Platform detected: {info.display_name}")
```

### Test 2: Exit Code Validation

```python
from main_app.utils.platform_utils import is_clean_exit_code

assert is_clean_exit_code(0) == True  # All platforms
assert is_clean_exit_code(1) == True  # Windows
print("✅ Exit code validation works")
```

### Test 3: Application Startup

```bash
cd main
set PYTHONPATH=src
python -m main_app
# Check logs for platform information
# Press Ctrl+C
# Verify clean shutdown
```

### Test 4: Demo Script

```bash
cd main
python demo.py
# Verify platform-aware message in graceful shutdown
```

### Test 5: Version Output

```bash
cd main
set PYTHONPATH=src
python -m main_app --version
# Should show platform info
```

---

## Expected Outcomes

### Startup Logs (Example)

```
2025-11-22 20:30:00 - main_app.core.application - INFO - Starting application...
2025-11-22 20:30:00 - main_app.core.application - INFO - Platform: Windows 10
2025-11-22 20:30:00 - main_app.core.application - INFO - Architecture: AMD64
2025-11-22 20:30:00 - main_app.core.application - INFO - Python: 3.13.7
2025-11-22 20:30:00 - main_app.core.application - DEBUG - Available signals: SIGINT, SIGTERM, SIGBREAK
2025-11-22 20:30:00 - main_app.core.application - INFO - Registered SIGINT and SIGTERM handlers
2025-11-22 20:30:00 - main_app.core.application - DEBUG - Registered Windows SIGBREAK handler
```

### Demo Output (Example)

```
[6/7] Testing graceful shutdown...
[OK] Graceful shutdown successful (exit code: 1, platform: Windows)
```

### Version Output (Example)

```
Main Application v0.11.0-alpha.1
ALPHA Development Version
Platform: Windows 10
Architecture: AMD64
Python: 3.13.7
```

---

## Success Metrics

**Before Refinement-003**:
- Platform behaviors implicit
- Exit code handling not aware of platform
- No platform detection logging
- Resource limits generic

**After Refinement-003**:
- Explicit platform detection and logging
- Platform-aware exit code validation
- Signal handlers adapted to platform
- Resource limits optimized per platform
- Platform info in version output

---

## Notes

**ALPHA Philosophy**:
- Focus on Windows validation (current platform)
- Design for cross-platform compatibility
- Explicit platform handling
- Document differences clearly

**Benefits**:
- Better debugging (platform info in logs)
- Clearer code intent (explicit platform checks)
- Production-ready for any platform
- Foundation for platform-specific optimizations

**Future** (BETA/PRODUCTION):
- CI/CD testing on multiple platforms
- Platform-specific installers
- Service integration (Windows Service, systemd, launchd)

---

**Mission Created**: 2025-11-22
**Estimated Completion**: 2-3 hours
**Priority**: P1 (High - production readiness)
**Complexity**: Medium (new module + integrations)
