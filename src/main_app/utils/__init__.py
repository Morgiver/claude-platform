"""Utility modules for main application."""

from .platform_utils import (
    PlatformInfo,
    get_platform_info,
    is_clean_exit_code,
    get_available_signals,
    get_platform_resource_limits
)

__all__ = [
    'PlatformInfo',
    'get_platform_info',
    'is_clean_exit_code',
    'get_available_signals',
    'get_platform_resource_limits'
]
