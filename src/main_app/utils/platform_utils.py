"""
Platform detection and compatibility utilities.

Provides cross-platform abstractions for:
- Platform detection (Windows, Linux, macOS)
- Exit code interpretation
- Signal availability
- Resource limit recommendations
"""

import platform
import signal
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
        dict: Resource limit recommendations with 'max_processes', 'max_threads', and 'reason'

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
