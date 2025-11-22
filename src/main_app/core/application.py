"""Main application entry point - Orchestrates all core components."""

import logging
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from ..config import load_all_configs
from ..logging import setup_logging
from ..error_handling.webhook_notifier import WebhookNotifier
from .event_bus import EventBus
from .module_loader import ModuleLoader
from .resource_manager import ResourceManager


logger = logging.getLogger(__name__)


class Application:
    """
    Main application class orchestrating all core components.

    Responsibilities:
    - Initialize core components (EventBus, ModuleLoader, ResourceManager)
    - Load configuration
    - Manage application lifecycle
    - Handle graceful shutdown
    """

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """
        Initialize application.

        Args:
            config_dir: Path to configuration directory. Defaults to ./config
        """
        # Load environment variables from .env file
        load_dotenv()

        # Load configuration
        # Default to config/ directory relative to project root (2 levels up from this file)
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.config_dir = project_root / "config"
        else:
            self.config_dir = config_dir
        try:
            self.config = load_all_configs(self.config_dir)
        except Exception as e:
            # Setup basic logging to report error
            logging.basicConfig(level=logging.ERROR)
            logger.error(f"Failed to load configuration: {e}")
            raise

        # Setup logging with configuration
        self._setup_logging()

        # Now we can log properly
        logger.info(f"Configuration loaded from {self.config_dir}")

        # Initialize core components with configuration
        self._initialize_components()

        self._running = False
        logger.info("Application initialized successfully")

    def _setup_logging(self) -> None:
        """Setup logging using configuration."""
        # Pass full config dict to setup_logging
        # It will extract and parse the logging section
        setup_logging(self.config)

    def _initialize_components(self) -> None:
        """Initialize core components with configuration."""
        # Event bus (no config needed yet)
        self.event_bus = EventBus()

        # Resource manager with config
        resource_config = self.config.get("resources", {})
        self.resource_manager = ResourceManager(
            process_memory_mb=resource_config.get("process_memory_mb", 512),
            reserved_ram_percent=resource_config.get("reserved_ram_percent", 0.25),
            threads_per_core=resource_config.get("threads_per_core", 2),
        )

        # Module loader with config and hot-reload callback
        modules_config = self.config.get("modules", {})
        hot_reload_enabled = modules_config.get("hot_reload", True)

        self.module_loader = ModuleLoader(
            watch_reload=hot_reload_enabled,
            reload_callback=self._on_module_reload
        )

        logger.info(f"Hot-reload: {'enabled' if hot_reload_enabled else 'disabled'}")

        # Webhook notifier with config
        webhook_config = self.config.get("error_handling", {}).get("webhook", {})
        webhook_url = webhook_config.get("url", "")
        webhook_timeout = webhook_config.get("timeout_seconds", 10.0)
        webhook_enabled = webhook_config.get("enabled", False)

        # Only initialize if enabled and URL is provided (not empty string from env substitution)
        if webhook_enabled and webhook_url and webhook_url.strip():
            self.webhook_notifier = WebhookNotifier(
                webhook_url=webhook_url,
                timeout=webhook_timeout,
                enabled=True,
            )
            logger.info(f"Webhook notifier initialized: {webhook_url}")
        else:
            # Initialize disabled notifier (for consistency)
            self.webhook_notifier = WebhookNotifier(enabled=False)
            logger.info("Webhook notifier disabled (no URL configured or disabled in config)")

    def _on_module_reload(self, module_name: str, success: bool) -> None:
        """
        Callback for module reload events.

        Args:
            module_name: Name of the reloaded module
            success: Whether reload was successful
        """
        if success:
            logger.info(f"Module '{module_name}' reloaded successfully")
            self.event_bus.publish("module.reloaded", {"name": module_name})
        else:
            logger.error(f"Module '{module_name}' reload failed, rollback occurred")
            self.event_bus.publish("module.reload_failed", {
                "name": module_name,
                "error": "Reload failed, see logs for details"
            })

    def _load_modules(self, modules_config: List[Dict[str, Any]]) -> None:
        """
        Load modules from configuration.

        Args:
            modules_config: List of module configurations from modules.yaml
        """
        from .module_loader import ModuleConfig

        logger.info(f"Loading {len(modules_config)} modules...")

        # Build module configs dict for hot-reload context
        module_configs_dict = {}

        for module_data in modules_config:
            config = ModuleConfig(
                name=module_data["name"],
                path=module_data["path"],
                enabled=module_data.get("enabled", True),
                config=module_data.get("config", {})
            )

            # Store config for hot-reload context
            module_configs_dict[config.name] = config.config

            # Skip disabled modules
            if not config.enabled:
                logger.info(f"Module '{config.name}' is disabled, skipping")
                continue

            # Load module
            try:
                success = self.module_loader.load_module(config)

                if success:
                    # Call initialize hook
                    module = self.module_loader.get_module(config.name)
                    if hasattr(module, "initialize"):
                        try:
                            module.initialize(self.event_bus, config.config)
                            logger.info(f"Module '{config.name}' initialized successfully")

                            # Publish success event
                            self.event_bus.publish("module.loaded", {
                                "name": config.name,
                                "path": config.path,
                                "config": config.config
                            })
                        except Exception as e:
                            logger.error(f"Failed to initialize module '{config.name}': {e}", exc_info=True)
                            self.event_bus.publish("module.error", {
                                "name": config.name,
                                "error": str(e),
                                "phase": "initialize"
                            })
                    else:
                        logger.warning(f"Module '{config.name}' has no initialize() function")
                else:
                    # Load failed
                    logger.error(f"Failed to load module '{config.name}'")
                    self.event_bus.publish("module.error", {
                        "name": config.name,
                        "error": "Module load failed",
                        "phase": "load"
                    })
            except Exception as e:
                logger.error(f"Error loading module '{config.name}': {e}", exc_info=True)
                self.event_bus.publish("module.error", {
                    "name": config.name,
                    "error": str(e),
                    "phase": "load"
                })

        # Set reload context for hot-reload functionality
        self.module_loader.set_reload_context(self.event_bus, module_configs_dict)
        logger.info("Hot-reload context configured")

    def start(self) -> None:
        """Start the application."""
        logger.info("Starting application...")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Enable webhook notifications if configured
        if self.webhook_notifier.webhook_url:
            self.webhook_notifier.enable()
            logger.info(f"Webhook notifications enabled: {self.webhook_notifier.webhook_url}")

        # Log system resources
        resources = self.resource_manager.get_system_resources()
        logger.info(
            f"System resources: {resources.total_ram_gb:.2f}GB RAM, "
            f"{resources.cpu_count} CPUs, "
            f"limits: {resources.max_processes} processes / {resources.max_threads} threads"
        )

        # Publish startup event
        self.event_bus.publish("app.started", {"resources": resources})

        # Load modules from configuration
        modules_config = self.config.get("modules", {}).get("modules", [])
        if modules_config:
            self._load_modules(modules_config)
        else:
            logger.info("No modules configured, skipping module loading")

        self._running = True
        logger.info("Application started successfully")

        # Keep application running
        self._run()

    def _run(self) -> None:
        """Main application loop with resource monitoring."""
        import time

        last_monitor_time = time.time()
        monitor_interval = 60  # Monitor resources every 60 seconds

        try:
            while self._running:
                current_time = time.time()

                # Resource monitoring every 60 seconds
                if current_time - last_monitor_time >= monitor_interval:
                    try:
                        ram_usage = self.resource_manager.get_memory_usage_percent()
                        cpu_usage = self.resource_manager.get_cpu_usage_percent(interval=0.1)
                        active_modules = len(self.module_loader.get_loaded_modules())

                        logger.info(
                            f"Resource Monitor: RAM {ram_usage:.1f}%, "
                            f"CPU {cpu_usage:.1f}%, "
                            f"Active Modules: {active_modules}"
                        )

                        # Publish resource monitoring event
                        self.event_bus.publish("app.monitor", {
                            "ram_percent": ram_usage,
                            "cpu_percent": cpu_usage,
                            "active_modules": active_modules,
                            "timestamp": current_time
                        })

                        last_monitor_time = current_time
                    except Exception as e:
                        logger.error(f"Error monitoring resources: {e}", exc_info=True)

                # Sleep to avoid busy-wait
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown application gracefully."""
        if not self._running:
            return

        logger.info("Shutting down application...")
        self._running = False

        # Disable webhook notifications
        if self.webhook_notifier:
            self.webhook_notifier.disable()
            logger.info("Webhook notifications disabled")

        # Publish shutdown event
        self.event_bus.publish("app.shutdown")

        # Shutdown components
        self.module_loader.shutdown()
        self.event_bus.clear()

        logger.info("Application shutdown complete")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle OS signals for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)


def main() -> None:
    """Main entry point."""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
