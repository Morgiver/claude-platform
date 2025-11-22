"""Main application entry point - Orchestrates all core components."""

import logging
import signal
import sys
from pathlib import Path
from typing import Optional

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
        self.config_dir = config_dir or Path("config")
        self.event_bus = EventBus()
        self.module_loader = ModuleLoader(watch_reload=True)
        self.resource_manager = ResourceManager()
        self._running = False

        logger.info("Application initialized")

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
    # Setup basic logging (will be enhanced by logging module later)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Application()
    app.start()


if __name__ == "__main__":
    main()
