# Refinement-003: Multi-Platform Compatibility (Linux, macOS, Windows)

**Status**: 🚧 in-progress
**Type**: Enhancement / Cross-Platform
**Priority**: P1 (High - production readiness)
**Complexity**: Medium
**GitHub Issue**: TBD (will create during mission planning)

---

## Problem Description

Currently, the application has platform-specific behaviors that are not explicitly handled:
- Exit code handling differs between Windows and Unix (discovered in Refinement-002)
- Signal handling behaves differently on different platforms
- File paths and path separators may cause issues
- Process management varies by OS

**Current Behavior**:
- Application works on Windows (current development platform)
- Platform-specific behaviors are implicit, not explicit
- No platform detection or adaptation logic
- Exit codes vary by platform (Windows: 1, Linux: 0/-15)

**Expected Behavior**:
- Application adapts to platform automatically
- Explicit platform detection and handling
- Consistent user experience across platforms
- Documented platform-specific behaviors

**Impact**:
- Better cross-platform compatibility
- Clearer code intent (platform-aware)
- Production-ready for deployment on any OS
- Easier debugging of platform-specific issues

---

## Objectives

### 1. Platform Detection & Abstraction

**Add platform detection**:
```python
import platform
import sys

def get_platform_info():
    """Get normalized platform information."""
    return {
        'system': platform.system(),  # 'Windows', 'Linux', 'Darwin'
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': sys.version,
        'is_windows': platform.system() == 'Windows',
        'is_linux': platform.system() == 'Linux',
        'is_macos': platform.system() == 'Darwin'
    }
```

**Log platform info at startup** for debugging and support.

### 2. Cross-Platform Exit Code Handling

**Current Issue** (from Refinement-002):
- Windows `proc.terminate()` → exit code 1 (TerminateProcess API)
- Linux `proc.terminate()` → exit code 0 or -15 (SIGTERM signal)
- macOS likely same as Linux (POSIX)

**Solution**: Platform-aware exit code interpretation

```python
def is_clean_exit(exit_code: int) -> bool:
    """
    Check if exit code represents a clean shutdown.

    Platform-specific handling:
    - Windows: 0 (clean), 1 (TerminateProcess - acceptable)
    - Linux/macOS: 0 (clean), -15 or 143 (SIGTERM - acceptable)
    """
    if platform.system() == 'Windows':
        return exit_code in [0, 1]  # 1 from TerminateProcess is acceptable
    else:  # Linux, macOS, other Unix
        return exit_code in [0, -15, 143]  # SIGTERM variations
```

**Update demo.py** to use this function:

```python
if is_clean_exit(exit_code):
    self.print_success(f"Graceful shutdown successful (exit code: {exit_code})")
else:
    self.print_error(f"Unexpected exit code: {exit_code}")
```

### 3. Cross-Platform Signal Handling

**Issue**: Signal availability varies by platform

```python
import signal

def setup_signal_handlers(handler):
    """Setup signal handlers with platform detection."""
    # SIGINT (Ctrl+C) - Available on all platforms
    signal.signal(signal.SIGINT, handler)

    # SIGTERM - Available on all platforms (but behaves differently)
    signal.signal(signal.SIGTERM, handler)

    # Windows-specific
    if platform.system() == 'Windows':
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, handler)  # Ctrl+Break

    # Unix-specific (Linux, macOS)
    else:
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, handler)  # Terminal hangup
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, handler)  # Quit signal
```

### 4. Cross-Platform Path Handling

**Ensure pathlib is used consistently** (already done, verify):

```python
from pathlib import Path

# Good (cross-platform)
config_path = Path("config") / "app.yaml"

# Bad (platform-specific)
config_path = "config\\app.yaml"  # Windows-only
```

**Verify all path operations use pathlib**.

### 5. Platform-Specific Resource Limits

**Current resource_manager.py** calculates limits.

**Enhancement**: Platform-aware defaults

```python
def get_platform_defaults(self):
    """Get platform-specific default limits."""
    if platform.system() == 'Windows':
        return {
            'max_processes': min(cpu_count * 2, 32),  # Windows handles ~64 well
            'max_threads': min(cpu_count * 4, 128)
        }
    elif platform.system() == 'Darwin':  # macOS
        return {
            'max_processes': min(cpu_count * 2, 64),
            'max_threads': min(cpu_count * 4, 256)
        }
    else:  # Linux
        return {
            'max_processes': min(cpu_count * 4, 128),  # Linux scales better
            'max_threads': min(cpu_count * 8, 512)
        }
```

### 6. Platform Information Logging

**Add platform info to startup logs**:

```python
logger.info(f"Platform: {platform.system()} {platform.release()}")
logger.info(f"Python: {platform.python_version()}")
logger.info(f"Architecture: {platform.machine()}")
```

---

## Expected Outcomes

### Files to Modify

**Core Files**:
- `src/main_app/core/application.py` - Platform-aware signal handling
- `src/main_app/core/resource_manager.py` - Platform-specific limits
- `src/main_app/__main__.py` - Platform detection logging

**Utility Files** (new):
- `src/main_app/utils/platform_utils.py` - Platform detection and helpers

**Demo/Test Files**:
- `demo.py` - Platform-aware exit code validation
- `test_exit_code_detailed.py` - Platform-specific testing

**Documentation**:
- `documentation/alpha-tasks/refinement-003.md` - This file
- `documentation/platform-compatibility.md` - Platform guide (new)

### Functionality Delivered

**Platform Detection**:
- Automatic platform detection at startup
- Platform info logged for debugging
- Helper functions for platform checks

**Exit Code Handling**:
- Platform-aware exit code interpretation
- Clean exit detection across platforms
- Demo script validates correctly on all platforms

**Signal Handling**:
- Platform-specific signal registration
- Windows: SIGINT, SIGTERM, SIGBREAK
- Linux/macOS: SIGINT, SIGTERM, SIGHUP, SIGQUIT

**Resource Management**:
- Platform-optimized default limits
- Better resource utilization per OS

**Documentation**:
- Platform compatibility guide
- Known platform differences documented
- Deployment notes per platform

---

## Acceptance Criteria

**Must Have**:
1. Platform detection implemented and logged at startup
2. Exit code handling is platform-aware
3. Demo script validates correctly on Windows (testable now)
4. Signal handlers registered based on platform
5. All path operations use pathlib (verify existing code)
6. Platform compatibility documented

**Nice to Have**:
- Platform-specific resource limits
- Platform info in version output (--version)
- Platform-specific troubleshooting guide

**Testing** (on Windows, current platform):
1. Application starts and logs platform info
2. Demo script passes with platform-aware exit code check
3. Ctrl+C works correctly (exit code 0)
4. All modules load and function correctly
5. Shutdown is clean and graceful

**Documentation**:
- Platform compatibility guide created
- Known differences documented
- Deployment recommendations per platform

---

## Implementation Strategy

### Phase 1: Platform Detection & Logging

**Create platform utility module**:

```python
# src/main_app/utils/platform_utils.py

import platform
import sys
from dataclasses import dataclass
from typing import Literal

PlatformType = Literal['Windows', 'Linux', 'Darwin', 'Unknown']

@dataclass
class PlatformInfo:
    """Platform information."""
    system: PlatformType
    release: str
    version: str
    machine: str
    python_version: str
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

def get_platform_info() -> PlatformInfo:
    """Get current platform information."""
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
    Check if exit code represents clean shutdown.

    Platform-specific:
    - Windows: 0 (clean), 1 (TerminateProcess acceptable)
    - Unix: 0 (clean), -15/143 (SIGTERM acceptable)
    """
    platform_info = get_platform_info()

    if platform_info.is_windows:
        # Windows: 0 or 1 (from TerminateProcess)
        return exit_code in [0, 1]
    else:
        # Linux/macOS: 0, -15, or 143 (SIGTERM variations)
        return exit_code in [0, -15, 143]
```

**Add to application.py startup**:

```python
from .utils.platform_utils import get_platform_info

def start(self):
    """Start the application."""
    # Log platform information
    platform_info = get_platform_info()
    logger.info(f"Platform: {platform_info.display_name}")
    logger.info(f"Architecture: {platform_info.machine}")
    logger.info(f"Python: {platform_info.python_version}")

    # ... existing startup code ...
```

### Phase 2: Platform-Aware Signal Handling

**Update signal handler registration**:

```python
def _setup_signal_handlers(self):
    """Setup signal handlers based on platform."""
    from .utils.platform_utils import get_platform_info

    platform_info = get_platform_info()

    # Common signals (all platforms)
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    logger.debug("Registered SIGINT and SIGTERM handlers")

    # Windows-specific
    if platform_info.is_windows:
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self._signal_handler)
            logger.debug("Registered Windows SIGBREAK handler")

    # Unix-specific (Linux, macOS)
    else:
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, self._signal_handler)
            logger.debug("Registered Unix SIGHUP handler")
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, self._signal_handler)
            logger.debug("Registered Unix SIGQUIT handler")
```

### Phase 3: Platform-Aware Demo Validation

**Update demo.py**:

```python
from main.src.main_app.utils.platform_utils import is_clean_exit_code

def validate_graceful_shutdown(self):
    """Validate graceful shutdown (platform-aware)."""
    # ... existing code to get exit_code ...

    if is_clean_exit_code(exit_code):
        self.print_success(
            f"Graceful shutdown successful (exit code: {exit_code}, "
            f"platform: {platform.system()})"
        )
    else:
        self.print_error(
            f"Unexpected exit code: {exit_code} "
            f"(expected 0 or platform-specific clean exit)"
        )
```

### Phase 4: Documentation

**Create platform compatibility guide**:

```markdown
# Platform Compatibility Guide

## Supported Platforms

- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, RHEL, etc.)
- ✅ macOS 10.15+

## Platform-Specific Behaviors

### Exit Codes

**Windows**:
- Clean exit: 0
- TerminateProcess: 1 (acceptable for automated termination)
- Ctrl+C: 0 (via KeyboardInterrupt)

**Linux/macOS**:
- Clean exit: 0
- SIGTERM: -15 or 143
- Ctrl+C: 0 (via KeyboardInterrupt)

### Signal Handling

**Windows**:
- SIGINT (Ctrl+C)
- SIGTERM (limited support)
- SIGBREAK (Ctrl+Break)

**Linux/macOS**:
- SIGINT (Ctrl+C)
- SIGTERM
- SIGHUP (terminal hangup)
- SIGQUIT

### Resource Limits

**Windows**: More conservative (32 processes, 128 threads)
**Linux**: More aggressive (128 processes, 512 threads)
**macOS**: Moderate (64 processes, 256 threads)

## Deployment Recommendations

### Windows
- Use Task Scheduler for automation
- Consider Windows Service for production
- Monitor with Event Viewer

### Linux
- Use systemd for service management
- Configure proper ulimits
- Monitor with journalctl

### macOS
- Use launchd for service management
- Respect macOS security policies
- Monitor with Console.app
```

---

## Rough Effort Estimate

**Time**: 2-3 hours

**Breakdown**:
- Platform utility module: 30 minutes
- Signal handling updates: 30 minutes
- Demo script updates: 20 minutes
- Resource manager updates: 20 minutes
- Documentation: 40 minutes
- Testing and validation: 40 minutes

---

## Known Platform Differences

### Windows
- `proc.terminate()` uses `TerminateProcess()` (exit code 1)
- Limited signal support (no SIGHUP, SIGQUIT)
- Path separator: `\` (but pathlib handles this)
- Case-insensitive filesystem
- Different resource limits

### Linux
- `proc.terminate()` sends SIGTERM (exit code 0 or -15)
- Full POSIX signal support
- Path separator: `/`
- Case-sensitive filesystem
- Better process/thread scaling

### macOS
- Similar to Linux (POSIX-compliant)
- Additional security restrictions
- Different process limits (more conservative than Linux)
- XNU kernel specifics

---

## Success Metrics

**Before Refinement-003**:
- Platform-specific behaviors implicit
- Exit code handling not platform-aware
- No platform documentation

**After Refinement-003**:
- Explicit platform detection and logging
- Platform-aware exit code validation
- Comprehensive platform compatibility guide
- Signal handling adapted to platform
- Resource limits optimized per platform

---

## Notes

**Philosophy**:
- **Explicit over implicit**: Platform checks are clear in code
- **Adapt, don't restrict**: Work with platform strengths
- **Document differences**: Clear guide for each platform

**ALPHA Approach**:
- Focus on Windows (current platform) validation
- Design for cross-platform compatibility
- Document known differences
- Test other platforms in BETA (if needed)

**Future Enhancements** (BETA/PRODUCTION):
- CI/CD testing on multiple platforms
- Platform-specific optimizations
- Windows Service / systemd / launchd support
- Platform-specific installers

---

**Version Target**: v0.11.0-alpha.1 (new feature: multi-platform)
**Previous Version**: v0.10.0-alpha.3 (documentation refinement)
**Next Refinement**: None planned (ALPHA complete after this)
