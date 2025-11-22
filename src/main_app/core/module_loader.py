"""Module loader - Declarative module loading with hot-reload support."""

import importlib
import importlib.util
import logging
import sys
import time
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

    def __init__(self, watch_reload: bool = True, reload_callback=None) -> None:
        """
        Initialize module loader.

        Args:
            watch_reload: Enable file watching for hot-reload
            reload_callback: Optional callback function(module_name, success) called after reload
        """
        self._modules: Dict[str, Any] = {}
        self._module_configs: Dict[str, ModuleConfig] = {}
        self._watch_reload = watch_reload
        self._observer: Optional[Observer] = None
        self._watched_paths: set[str] = set()
        self._reload_callback = reload_callback
        self._reload_context: Dict[str, Any] = {}  # Store event_bus and configs for reload

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

        # Start timing
        start_time = time.time()
        logger.info(f"[TIMING] Starting load for module '{config.name}'")

        try:
            module_path = Path(config.path)

            # Timing: Path validation
            path_check_start = time.time()
            if not module_path.exists():
                logger.error(f"Module path does not exist: {config.path}")
                return False
            logger.debug(f"[TIMING] Path validation for '{config.name}': {time.time() - path_check_start:.3f}s")

            # Timing: Module spec creation
            spec_start = time.time()
            spec = importlib.util.spec_from_file_location(config.name, module_path)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for '{config.name}'")
                return False
            logger.debug(f"[TIMING] Spec creation for '{config.name}': {time.time() - spec_start:.3f}s")

            # Timing: Module import and execution
            import_start = time.time()
            module = importlib.util.module_from_spec(spec)
            sys.modules[config.name] = module
            spec.loader.exec_module(module)
            import_elapsed = time.time() - import_start
            logger.info(f"[TIMING] Module import/exec for '{config.name}': {import_elapsed:.3f}s")

            # Store module and config
            self._modules[config.name] = module
            self._module_configs[config.name] = config

            # Timing: Setup hot-reload watching (non-blocking)
            if self._watch_reload:
                watch_start = time.time()
                self._watch_path(str(module_path.parent))
                watch_elapsed = time.time() - watch_start
                logger.debug(f"[TIMING] Watchdog setup for '{config.name}': {watch_elapsed:.3f}s")

            # Total timing
            total_elapsed = time.time() - start_time
            logger.info(f"[TIMING] Module '{config.name}' loaded in {total_elapsed:.3f}s")
            logger.info(f"Module '{config.name}' loaded successfully from {config.path}")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[TIMING] Failed to load module '{config.name}' after {elapsed:.3f}s: {e}", exc_info=True)
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

    def reload_module(self, module_name: str, event_bus=None, module_config=None) -> bool:
        """
        Reload a module with full lifecycle hooks and rollback support.

        Args:
            module_name: Name of module to reload
            event_bus: EventBus instance for initialize() hook
            module_config: Config dict for initialize() hook

        Returns:
            True if reload successful, False if rollback occurred
        """
        if module_name not in self._module_configs:
            logger.warning(f"Module '{module_name}' not in configurations")
            return False

        config = self._module_configs[module_name]
        old_module = self._modules.get(module_name)

        try:
            # Step 1: Call shutdown() hook on old module
            if old_module and hasattr(old_module, "shutdown"):
                try:
                    logger.info(f"Calling shutdown() on module '{module_name}' before reload")
                    old_module.shutdown()
                except Exception as e:
                    logger.warning(f"Error during shutdown of '{module_name}': {e}")

            # Step 2: Unload old module from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Step 3: Load new module version
            module_path = Path(config.path)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Failed to create module spec for '{module_name}'")

            new_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = new_module
            spec.loader.exec_module(new_module)

            # Step 4: Call initialize() hook on new module
            if hasattr(new_module, "initialize"):
                try:
                    logger.info(f"Calling initialize() on reloaded module '{module_name}'")
                    new_module.initialize(event_bus, module_config or config.config or {})
                except Exception as e:
                    logger.error(f"Failed to initialize reloaded module '{module_name}': {e}")
                    raise

            # Step 5: Update module registry
            self._modules[module_name] = new_module

            logger.info(f"Module '{module_name}' reloaded successfully")
            return True

        except Exception as e:
            # Step 6: Rollback - restore old module
            logger.error(f"Failed to reload module '{module_name}': {e}", exc_info=True)
            logger.info(f"Rolling back to previous version of '{module_name}'")

            try:
                # Restore old module in sys.modules and registry
                if old_module:
                    sys.modules[module_name] = old_module
                    self._modules[module_name] = old_module

                    # Re-initialize old module
                    if hasattr(old_module, "initialize"):
                        try:
                            old_module.initialize(event_bus, module_config or config.config or {})
                            logger.info(f"Old module '{module_name}' re-initialized after rollback")
                        except Exception as reinit_error:
                            logger.error(f"Failed to re-initialize old module '{module_name}': {reinit_error}")

                    logger.info(f"Successfully rolled back module '{module_name}' to previous version")
                else:
                    logger.warning(f"No previous version to rollback for '{module_name}'")

            except Exception as rollback_error:
                logger.error(f"Rollback failed for module '{module_name}': {rollback_error}", exc_info=True)

            return False

    def set_reload_context(self, event_bus, module_configs: Dict[str, Any]) -> None:
        """
        Set context for hot-reload operations.

        Args:
            event_bus: EventBus instance to pass to reloaded modules
            module_configs: Dict mapping module names to their configs
        """
        self._reload_context = {
            "event_bus": event_bus,
            "module_configs": module_configs
        }

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

                # Get reload context
                event_bus = self._reload_context.get("event_bus")
                module_configs = self._reload_context.get("module_configs", {})
                module_config = module_configs.get(name, config.config)

                # Perform reload with lifecycle hooks
                success = self.reload_module(name, event_bus, module_config)

                # Call reload callback if set
                if self._reload_callback:
                    self._reload_callback(name, success)

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
        Start watching a path for changes (non-blocking).

        Args:
            path: Directory path to watch
        """
        if path in self._watched_paths:
            logger.debug(f"Path already watched: {path}")
            return

        try:
            # Initialize observer if needed (lazy initialization)
            if self._observer is None:
                observer_start = time.time()
                self._observer = Observer()
                # Start observer in daemon mode (non-blocking)
                self._observer.daemon = True
                self._observer.start()
                observer_elapsed = time.time() - observer_start
                logger.info(f"[TIMING] File observer started in {observer_elapsed:.3f}s (daemon mode)")

            # Schedule path watching
            schedule_start = time.time()
            handler = ModuleReloadHandler(self)
            self._observer.schedule(handler, path, recursive=True)
            self._watched_paths.add(path)
            schedule_elapsed = time.time() - schedule_start
            logger.debug(f"[TIMING] Path scheduled for watching in {schedule_elapsed:.3f}s: {path}")

        except Exception as e:
            logger.warning(f"Failed to setup file watching for {path}: {e}")
            # Don't fail module loading if watching fails
            pass

    def shutdown(self) -> None:
        """Shutdown module loader and all loaded modules."""
        logger.info(f"Shutting down {len(self._modules)} modules...")

        # Call shutdown hook on each module
        for name, module in list(self._modules.items()):
            if hasattr(module, "shutdown"):
                try:
                    logger.info(f"Shutting down module '{name}'...")
                    module.shutdown()
                    logger.info(f"Module '{name}' shutdown successfully")
                except Exception as e:
                    logger.error(f"Error shutting down module '{name}': {e}", exc_info=True)
            else:
                logger.debug(f"Module '{name}' has no shutdown() hook")

        # Stop file observer
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=2)
            logger.info("File observer stopped")

        # Clear module registry
        self._modules.clear()
        self._module_configs.clear()
        logger.info("ModuleLoader shutdown complete")
