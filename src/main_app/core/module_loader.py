"""Module loader - Declarative module loading with hot-reload support."""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    """
    Configuration for a loadable module.

    Attributes:
        name: Module identifier
        path: Path to module file or package
        enabled: Whether module should be loaded
        config: Additional configuration for the module
    """

    name: str
    path: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class ModuleReloadHandler(FileSystemEventHandler):
    """File system event handler for module hot-reload."""

    def __init__(self, loader: "ModuleLoader") -> None:
        """
        Initialize reload handler.

        Args:
            loader: ModuleLoader instance to notify of changes
        """
        self.loader = loader
        super().__init__()

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Handle file modification event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix == ".py":
            logger.info(f"Module file modified: {file_path}")
            self.loader.reload_module_by_path(str(file_path))


class ModuleLoader:
    """
    Loads and manages Python modules with hot-reload support.

    Features:
    - Declarative module configuration
    - Hot-reload on file changes (via watchdog)
    - Module lifecycle management (load/unload/reload)
    - Error isolation (failed modules don't crash loader)
    """

    def __init__(self, watch_reload: bool = True) -> None:
        """
        Initialize module loader.

        Args:
            watch_reload: Enable file watching for hot-reload
        """
        self._modules: Dict[str, Any] = {}
        self._module_configs: Dict[str, ModuleConfig] = {}
        self._watch_reload = watch_reload
        self._observer: Optional[Observer] = None
        self._watched_paths: set[str] = set()

        logger.info(f"ModuleLoader initialized (hot-reload={'enabled' if watch_reload else 'disabled'})")

    def load_module(self, config: ModuleConfig) -> bool:
        """
        Load a module from configuration.

        Args:
            config: Module configuration

        Returns:
            True if module loaded successfully, False otherwise
        """
        if not config.enabled:
            logger.info(f"Module '{config.name}' is disabled, skipping")
            return False

        try:
            module_path = Path(config.path)

            if not module_path.exists():
                logger.error(f"Module path does not exist: {config.path}")
                return False

            # Load module
            spec = importlib.util.spec_from_file_location(config.name, module_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for '{config.name}'")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[config.name] = module
            spec.loader.exec_module(module)

            # Store module and config
            self._modules[config.name] = module
            self._module_configs[config.name] = config

            # Setup hot-reload watching
            if self._watch_reload:
                self._watch_path(str(module_path.parent))

            logger.info(f"Module '{config.name}' loaded successfully from {config.path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load module '{config.name}': {e}", exc_info=True)
            return False

    def load_modules(self, configs: List[ModuleConfig]) -> Dict[str, bool]:
        """
        Load multiple modules.

        Args:
            configs: List of module configurations

        Returns:
            Dict mapping module names to load success status
        """
        results = {}
        for config in configs:
            results[config.name] = self.load_module(config)
        return results

    def unload_module(self, module_name: str) -> bool:
        """
        Unload a module.

        Args:
            module_name: Name of module to unload

        Returns:
            True if module unloaded successfully
        """
        if module_name not in self._modules:
            logger.warning(f"Module '{module_name}' not loaded")
            return False

        try:
            # Call shutdown hook if exists
            module = self._modules[module_name]
            if hasattr(module, "shutdown"):
                module.shutdown()

            # Remove from sys.modules and our cache
            if module_name in sys.modules:
                del sys.modules[module_name]
            del self._modules[module_name]
            del self._module_configs[module_name]

            logger.info(f"Module '{module_name}' unloaded")
            return True

        except Exception as e:
            logger.error(f"Failed to unload module '{module_name}': {e}", exc_info=True)
            return False

    def reload_module(self, module_name: str) -> bool:
        """
        Reload a module (unload then load).

        Args:
            module_name: Name of module to reload

        Returns:
            True if module reloaded successfully
        """
        if module_name not in self._module_configs:
            logger.warning(f"Module '{module_name}' not in configurations")
            return False

        config = self._module_configs[module_name]
        self.unload_module(module_name)
        return self.load_module(config)

    def reload_module_by_path(self, file_path: str) -> None:
        """
        Reload module by file path.

        Args:
            file_path: Path to modified file
        """
        # Find module by path
        for name, config in self._module_configs.items():
            if Path(config.path) == Path(file_path):
                logger.info(f"Reloading module '{name}' due to file change")
                self.reload_module(name)
                break

    def get_module(self, module_name: str) -> Optional[Any]:
        """
        Get loaded module by name.

        Args:
            module_name: Name of module

        Returns:
            Module object or None if not loaded
        """
        return self._modules.get(module_name)

    def get_loaded_modules(self) -> List[str]:
        """
        Get list of loaded module names.

        Returns:
            List of module names
        """
        return list(self._modules.keys())

    def _watch_path(self, path: str) -> None:
        """
        Start watching a path for changes.

        Args:
            path: Directory path to watch
        """
        if path in self._watched_paths:
            return

        if self._observer is None:
            self._observer = Observer()
            self._observer.start()
            logger.info("File observer started for hot-reload")

        handler = ModuleReloadHandler(self)
        self._observer.schedule(handler, path, recursive=True)
        self._watched_paths.add(path)
        logger.debug(f"Watching path for changes: {path}")

    def shutdown(self) -> None:
        """Shutdown module loader and stop file watching."""
        # Stop observer
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("File observer stopped")

        # Unload all modules
        for module_name in list(self._modules.keys()):
            self.unload_module(module_name)

        logger.info("ModuleLoader shutdown complete")
