"""Process pool - Spawn processes on demand with auto-scaling limits."""

import logging
import multiprocessing as mp
from typing import Callable, Any, Optional, List
from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a running process."""

    pid: Optional[int]
    started_at: datetime
    task_name: str
    status: str  # pending, running, completed, failed


class ProcessPool:
    """
    Manages a pool of worker processes with auto-scaling.

    Features:
    - Spawn processes on demand (no pre-creation)
    - Automatic limit calculation based on system resources
    - Process lifecycle management
    - Result tracking
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        resource_manager: Optional[Any] = None,
    ) -> None:
        """
        Initialize process pool.

        Args:
            max_workers: Maximum concurrent processes. If None, auto-calculated.
            resource_manager: ResourceManager instance for auto-scaling
        """
        self.resource_manager = resource_manager
        self._max_workers = max_workers
        self._executor: Optional[ProcessPoolExecutor] = None
        self._active_processes: List[ProcessInfo] = []
        self._futures: List[Future] = []

        # Calculate max workers if not provided
        if self._max_workers is None and resource_manager:
            self._max_workers = resource_manager.get_max_processes()
        elif self._max_workers is None:
            # Fallback to CPU count
            self._max_workers = mp.cpu_count()

        logger.info(f"ProcessPool initialized (max_workers={self._max_workers})")

    def submit(
        self,
        func: Callable,
        *args: Any,
        task_name: str = "unnamed",
        **kwargs: Any,
    ) -> Future:
        """
        Submit a task to be executed in a separate process.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            task_name: Name for tracking this task
            **kwargs: Keyword arguments for function

        Returns:
            Future object representing the pending result
        """
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self._max_workers)

        # Track process info
        process_info = ProcessInfo(
            pid=None,
            started_at=datetime.now(),
            task_name=task_name,
            status="pending",
        )
        self._active_processes.append(process_info)

        # Submit task
        future = self._executor.submit(func, *args, **kwargs)
        self._futures.append(future)

        # Update status when done
        future.add_done_callback(
            lambda f: self._on_task_complete(f, process_info)
        )

        logger.info(f"Task '{task_name}' submitted to process pool")
        return future

    def _on_task_complete(self, future: Future, process_info: ProcessInfo) -> None:
        """
        Callback when task completes.

        Args:
            future: Completed future
            process_info: Process information
        """
        try:
            if future.exception():
                process_info.status = "failed"
                logger.error(
                    f"Task '{process_info.task_name}' failed: {future.exception()}",
                    exc_info=True
                )
            else:
                process_info.status = "completed"
                logger.info(f"Task '{process_info.task_name}' completed successfully")
        except Exception as e:
            process_info.status = "failed"
            logger.error(f"Error handling task completion: {e}", exc_info=True)

    def map(
        self,
        func: Callable,
        iterable: List[Any],
        task_name: str = "batch",
    ) -> List[Any]:
        """
        Map function over iterable using process pool.

        Args:
            func: Function to apply
            iterable: Items to process
            task_name: Name for tracking

        Returns:
            List of results
        """
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self._max_workers)

        logger.info(f"Batch task '{task_name}' mapping {len(iterable)} items")

        results = list(self._executor.map(func, iterable))

        logger.info(f"Batch task '{task_name}' completed")
        return results

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the process pool.

        Args:
            wait: Wait for pending tasks to complete
        """
        if self._executor:
            logger.info(f"Shutting down process pool (wait={wait})")
            self._executor.shutdown(wait=wait)
            self._executor = None

        self._active_processes.clear()
        self._futures.clear()
        logger.info("Process pool shutdown complete")

    def get_active_count(self) -> int:
        """
        Get number of active processes.

        Returns:
            Count of running/pending processes
        """
        active = sum(
            1 for p in self._active_processes
            if p.status in ("pending", "running")
        )
        return active

    def get_process_info(self) -> List[ProcessInfo]:
        """
        Get information about all processes.

        Returns:
            List of ProcessInfo objects
        """
        return self._active_processes.copy()

    def has_capacity(self) -> bool:
        """
        Check if pool has capacity for more tasks.

        Returns:
            True if can accept more tasks
        """
        return self.get_active_count() < self._max_workers

    def wait_for_capacity(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until pool has capacity.

        Args:
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            True if capacity available, False if timeout
        """
        import time
        start = time.time()

        while not self.has_capacity():
            if timeout and (time.time() - start) > timeout:
                logger.warning("Timeout waiting for process pool capacity")
                return False
            time.sleep(0.1)

        return True

    @property
    def max_workers(self) -> int:
        """Get maximum number of workers."""
        return self._max_workers

    def __enter__(self) -> "ProcessPool":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.shutdown(wait=True)
