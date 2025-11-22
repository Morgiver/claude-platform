"""Event bus implementation - Internal message broker with pub/sub pattern."""

from typing import Any, Callable, Dict, List
import logging
from collections import defaultdict
from threading import Lock


logger = logging.getLogger(__name__)


class EventBus:
    """
    Thread-safe event bus for inter-module communication.

    Implements a publish/subscribe pattern where modules can:
    - Subscribe to specific event types
    - Publish events to all subscribers
    - Unsubscribe from events

    Example:
        >>> bus = EventBus()
        >>> def handler(data):
        ...     print(f"Received: {data}")
        >>> bus.subscribe("module.loaded", handler)
        >>> bus.publish("module.loaded", {"module": "test"})
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty subscribers."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = Lock()
        logger.info("EventBus initialized")

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe a callback to a specific event type.

        Args:
            event_type: The type of event to subscribe to (e.g., "module.loaded")
            callback: Function to call when event is published. Receives event data as argument.
        """
        with self._lock:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to '{event_type}': {callback.__name__}")

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe a callback from a specific event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from '{event_type}': {callback.__name__}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: The type of event to publish
            data: Optional data to pass to subscribers
        """
        with self._lock:
            subscribers = self._subscribers[event_type].copy()

        logger.debug(f"Publishing event '{event_type}' to {len(subscribers)} subscribers")

        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                logger.error(
                    f"Error in subscriber {callback.__name__} for event '{event_type}': {e}",
                    exc_info=True
                )

    def clear(self, event_type: str | None = None) -> None:
        """
        Clear subscribers for a specific event type or all events.

        Args:
            event_type: Event type to clear. If None, clears all subscribers.
        """
        with self._lock:
            if event_type:
                self._subscribers[event_type].clear()
                logger.debug(f"Cleared subscribers for '{event_type}'")
            else:
                self._subscribers.clear()
                logger.debug("Cleared all subscribers")

    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of subscribers for a specific event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of subscribers
        """
        with self._lock:
            return len(self._subscribers[event_type])
