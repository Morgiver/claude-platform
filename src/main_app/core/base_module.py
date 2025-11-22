"""
Base module abstract class for standardizing module development.

This module provides a base class that all modules can inherit from to reduce
boilerplate and enforce best practices.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
import threading
import logging


class BaseModule(ABC):
    """
    Abstract base class for all modules.

    Provides common functionality and enforces implementation of required methods.
    Includes built-in helpers for threading, logging, and EventBus integration.

    Example:
        ```python
        from main_app.core.base_module import BaseModule

        class MyModule(BaseModule):
            def on_initialize(self):
                # Start background work
                self.start_background_thread(self._worker)

            def _worker(self):
                while not self.is_stopping:
                    # Do work
                    self.logger.info("Working...")
                    self.wait_interruptible(5)

            def on_shutdown(self):
                # Cleanup (threads already stopped)
                self.logger.info("Cleanup complete")

        # Module instance (required for ModuleLoader)
        _module = MyModule()

        # Interface functions (required for ModuleLoader compatibility)
        def initialize(event_bus, config):
            _module.initialize(event_bus, config)

        def shutdown():
            _module.shutdown()

        def get_tests():
            return _module.get_tests()
        ```

    Attributes:
        event_bus: EventBus instance for pub/sub messaging
        config: Module configuration dictionary
        logger: Logger instance for this module
        name: Module name
        is_stopping: Boolean flag indicating shutdown state
    """

    def __init__(self):
        """Initialize base module state."""
        self._event_bus = None
        self._config = {}
        self._logger = None
        self._name = ""
        self._threads = []
        self._stop_event = threading.Event()

    @property
    def event_bus(self):
        """
        Get the EventBus instance.

        Returns:
            EventBus instance for pub/sub messaging
        """
        return self._event_bus

    @property
    def config(self) -> dict:
        """
        Get module configuration.

        Returns:
            dict: Module configuration from modules.yaml
        """
        return self._config

    @property
    def logger(self):
        """
        Get module logger.

        Returns:
            logging.Logger: Logger instance for this module
        """
        return self._logger

    @property
    def name(self) -> str:
        """
        Get module name.

        Returns:
            str: Module name
        """
        return self._name

    @property
    def is_stopping(self) -> bool:
        """
        Check if module is being stopped.

        Returns:
            bool: True if shutdown has been initiated, False otherwise
        """
        return self._stop_event.is_set()

    def initialize(self, event_bus, config: dict) -> None:
        """
        Initialize the module (called by ModuleLoader).

        This method sets up the base module infrastructure and then calls
        on_initialize() for module-specific setup.

        Args:
            event_bus: EventBus instance for pub/sub
            config: Module configuration from modules.yaml
        """
        self._event_bus = event_bus
        self._config = config
        self._name = config.get('name', self.__class__.__name__)
        self._logger = logging.getLogger(self._name)

        self.logger.info(f"Initializing {self.name}")
        self.on_initialize()

    @abstractmethod
    def on_initialize(self) -> None:
        """
        Module-specific initialization logic.

        This method is called after base initialization is complete.
        Override this method to implement your module's startup logic.

        Use self.event_bus, self.config, self.logger as needed.
        Start background threads with self.start_background_thread().

        Example:
            ```python
            def on_initialize(self):
                # Subscribe to events
                event_type = self.config.get("event_type", "default.event")
                self.event_bus.subscribe(event_type, self._handle_event)

                # Start background thread
                self.start_background_thread(self._worker)
            ```
        """
        pass

    def shutdown(self) -> None:
        """
        Shutdown the module (called by ModuleLoader).

        This method automatically stops all background threads and then
        calls on_shutdown() for module-specific cleanup.
        """
        self.logger.info(f"Shutting down {self.name}")

        # Stop all background threads
        self._stop_event.set()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2)
                if thread.is_alive():
                    self.logger.warning(
                        f"Thread {thread.name} did not stop within timeout"
                    )

        # Call module-specific shutdown
        self.on_shutdown()

        self.logger.info(f"{self.name} shutdown complete")

    @abstractmethod
    def on_shutdown(self) -> None:
        """
        Module-specific shutdown logic.

        This method is called after all background threads have been stopped.
        Override this method to implement your module's cleanup logic.

        Note: Background threads are already stopped before this is called.

        Example:
            ```python
            def on_shutdown(self):
                # Unsubscribe from events
                if self._subscription_id:
                    self.event_bus.unsubscribe(self._event_type, self._subscription_id)

                # Additional cleanup
                self.logger.info("Cleanup complete")
            ```
        """
        pass

    def get_tests(self) -> list[str]:
        """
        Get list of test files for this module.

        Returns:
            list[str]: List of test file paths (relative to module directory)

        Override this method if your module has tests:
            ```python
            def get_tests(self):
                return ['tests/test_my_module.py']
            ```
        """
        return []

    def start_background_thread(
        self,
        target: Callable,
        name: Optional[str] = None,
        daemon: bool = True
    ) -> threading.Thread:
        """
        Start a background thread with automatic lifecycle management.

        The thread will be automatically stopped during module shutdown.
        Use self.is_stopping and self.wait_interruptible() in your thread
        function for responsive shutdown.

        Args:
            target: Function to run in background thread
            name: Thread name (optional, defaults to function name)
            daemon: Whether thread should be daemon (default: True)

        Returns:
            threading.Thread: The started thread

        Example:
            ```python
            def on_initialize(self):
                self.start_background_thread(self._worker)

            def _worker(self):
                while not self.is_stopping:
                    # Do work
                    self.logger.info("Working...")
                    self.wait_interruptible(5)
            ```
        """
        thread_name = name or target.__name__
        full_name = f"{self.name}.{thread_name}"

        thread = threading.Thread(
            target=target,
            name=full_name,
            daemon=daemon
        )
        self._threads.append(thread)
        thread.start()
        self.logger.debug(f"Started background thread: {thread_name}")
        return thread

    def wait_interruptible(self, timeout: float) -> bool:
        """
        Interruptible sleep that responds immediately to shutdown signals.

        Use this instead of time.sleep() in loops to ensure responsive shutdown.

        Args:
            timeout: Time to wait in seconds

        Returns:
            bool: True if interrupted by shutdown, False if timeout completed

        Example:
            ```python
            while not self.is_stopping:
                # Do work
                self.logger.info("Working...")

                # Sleep for 10 seconds, but wake immediately on shutdown
                if self.wait_interruptible(10):
                    break  # Shutting down
            ```
        """
        return self._stop_event.wait(timeout=timeout)
