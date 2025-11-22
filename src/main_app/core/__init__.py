"""Core module - Event bus, module loader, resource management."""

from .event_bus import EventBus
from .module_loader import ModuleLoader
from .resource_manager import ResourceManager

__all__ = ["EventBus", "ModuleLoader", "ResourceManager"]
