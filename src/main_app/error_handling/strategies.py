"""Retry and circuit breaker strategies for error handling."""

import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pybreaker import CircuitBreaker, CircuitBreakerError


logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for automatic retry with exponential backoff.

    Use this decorator for operations that may fail transiently (network calls,
    database connections, file I/O). The decorator will automatically retry
    the operation with exponential backoff between attempts.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time between retries (seconds)
        wait_max: Maximum wait time between retries (seconds)
        exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Example - Basic usage:
        >>> @with_retry(max_attempts=5, exceptions=(ConnectionError,))
        ... def fetch_data():
        ...     # This will retry up to 5 times on ConnectionError
        ...     response = requests.get("https://api.example.com/data")
        ...     return response.json()

    Example - With configuration:
        >>> from pathlib import Path
        >>> from main_app.config import load_all_configs
        >>>
        >>> config = load_all_configs(Path("config"))
        >>> retry_config = config["error_handling"]["retry"]
        >>>
        >>> @with_retry(
        ...     max_attempts=retry_config["max_attempts"],
        ...     wait_min=retry_config["wait_min_seconds"],
        ...     wait_max=retry_config["wait_max_seconds"],
        ...     exceptions=(ConnectionError, TimeoutError)
        ... )
        ... def load_remote_module():
        ...     # Configuration-driven retry for module loading
        ...     return download_module()
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(min=wait_min, max=wait_max),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug(f"Executing {func.__name__} with retry strategy")
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(
                    f"Retry attempt failed for {func.__name__}: {e}",
                    exc_info=True
                )
                raise

        return wrapper

    return decorator


def with_circuit_breaker(
    fail_max: int = 5,
    reset_timeout: int = 60,
    name: str | None = None,
) -> Callable:
    """
    Decorator for circuit breaker pattern.

    Circuit breaker prevents cascading failures by:
    - Opening after fail_max consecutive failures
    - Staying open for reset_timeout seconds
    - Allowing one request through after timeout (half-open state)
    - Closing if request succeeds, staying open if it fails

    Use this for external service calls, APIs, or any operation where repeated
    failures indicate a systemic problem that won't resolve immediately.

    Args:
        fail_max: Number of failures before opening circuit
        reset_timeout: Seconds to wait before attempting reset
        name: Circuit breaker name (defaults to function name)

    Returns:
        Decorated function with circuit breaker

    Example - Basic usage:
        >>> @with_circuit_breaker(fail_max=3, reset_timeout=30)
        ... def call_external_api():
        ...     # Circuit opens after 3 failures, resets after 30s
        ...     response = requests.get("https://external-api.com/endpoint")
        ...     return response.json()

    Example - With configuration:
        >>> from pathlib import Path
        >>> from main_app.config import load_all_configs
        >>>
        >>> config = load_all_configs(Path("config"))
        >>> cb_config = config["error_handling"]["circuit_breaker"]
        >>>
        >>> @with_circuit_breaker(
        ...     fail_max=cb_config["fail_max"],
        ...     reset_timeout=cb_config["reset_timeout_seconds"],
        ...     name="external_service"
        ... )
        ... def fetch_from_service():
        ...     # Configuration-driven circuit breaker
        ...     return call_service()

    Example - Checking circuit state:
        >>> @with_circuit_breaker(fail_max=5, reset_timeout=60)
        ... def protected_operation():
        ...     return do_something()
        >>>
        >>> # Access circuit breaker state
        >>> state = protected_operation.circuit_breaker.state  # 'closed', 'open', or 'half-open'
    """

    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            name=breaker_name,
        )

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                logger.error(
                    f"Circuit breaker '{breaker_name}' is OPEN - rejecting call to {func.__name__}"
                )
                raise
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed in circuit breaker '{breaker_name}': {e}",
                    exc_info=True
                )
                raise

        # Expose circuit breaker state
        wrapper.circuit_breaker = breaker

        return wrapper

    return decorator


class ErrorStrategy:
    """
    Combined error handling strategy with retry + circuit breaker.

    For critical operations that need both:
    - Fast fail when service is down (circuit breaker)
    - Automatic recovery from transient errors (retry)

    Example - Critical module loading:
        >>> from pathlib import Path
        >>> from main_app.config import load_all_configs
        >>>
        >>> config = load_all_configs(Path("config"))
        >>> error_config = config["error_handling"]
        >>>
        >>> @ErrorStrategy.critical_operation(
        ...     max_attempts=error_config["retry"]["max_attempts"],
        ...     fail_max=error_config["circuit_breaker"]["fail_max"],
        ...     reset_timeout=error_config["circuit_breaker"]["reset_timeout_seconds"]
        ... )
        ... def load_critical_module(module_name: str):
        ...     # This operation has both retry and circuit breaker protection
        ...     return import_module(module_name)
    """

    @staticmethod
    def critical_operation(
        max_attempts: int = 3,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ) -> Callable:
        """
        Decorator combining retry and circuit breaker for critical operations.

        This applies circuit breaker first (to fail fast when service is down),
        then retry logic (to handle transient failures). This order ensures that
        retries don't fight against an open circuit breaker.

        Args:
            max_attempts: Retry attempts
            fail_max: Circuit breaker failure threshold
            reset_timeout: Circuit breaker reset timeout

        Returns:
            Decorated function with both strategies

        Example:
            >>> @ErrorStrategy.critical_operation(max_attempts=5, fail_max=3)
            ... def critical_database_operation():
            ...     # Protected by both retry and circuit breaker
            ...     return db.execute_transaction()
        """

        def decorator(func: Callable) -> Callable:
            # Apply circuit breaker first (outer), then retry (inner)
            return with_circuit_breaker(
                fail_max=fail_max,
                reset_timeout=reset_timeout,
            )(
                with_retry(
                    max_attempts=max_attempts,
                    exceptions=(Exception,),
                )(func)
            )

        return decorator
