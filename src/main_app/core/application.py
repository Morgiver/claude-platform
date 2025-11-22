"""Main application entry point - Orchestrates all core components."""

import logging
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from ..config import load_all_configs
from ..logging import setup_logging
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
        logging_config = self.config.get("logging", {})

        # Extract logging parameters from config
        file_config = logging_config.get("file", {})
        console_config = logging_config.get("console", {})

        # Convert string log level to logging constant
        level_str = logging_config.get("level", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)

        # Setup logging with configured parameters
        setup_logging(
            log_dir=Path(file_config.get("directory", "logs")),
            log_file=file_config.get("filename", "app.log"),
            level=level,
            console_output=console_config.get("enabled", True),
            file_output=file_config.get("enabled", True),
            max_bytes=file_config.get("max_bytes", 10 * 1024 * 1024),
            backup_count=file_config.get("backup_count", 5),
        )

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

        # Module loader with config
        modules_config = self.config.get("modules", {})
        self.module_loader = ModuleLoader(
            watch_reload=modules_config.get("hot_reload", True)
        )

    def start(self) -> None:
        """Start the application."""
        logger.info("Starting application...")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Log system resources
        resources = self.resource_manager.get_system_resources()
        logger.info(
            f"System resources: {resources.total_ram_gb:.2f}GB RAM, "
            f"{resources.cpu_count} CPUs, "
            f"limits: {resources.max_processes} processes / {resources.max_threads} threads"
        )

        # Publish startup event
        self.event_bus.publish("app.started", {"resources": resources})

        self._running = True
        logger.info("Application started successfully")

        # Keep application running
        self._run()

    def _run(self) -> None:
        """Main application loop."""
        try:
            while self._running:
                # Main loop - for now just wait
                # In future, this could process tasks, monitor health, etc.
                import time
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
