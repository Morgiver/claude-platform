"""Resource manager - Auto-calculate system limits for threading/multiprocessing."""

import psutil
import logging
from dataclasses import dataclass
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class SystemResources:
    """
    System resource information.

    Attributes:
        total_ram_gb: Total RAM in gigabytes
        available_ram_gb: Available RAM in gigabytes
        cpu_count: Number of CPU cores (logical)
        cpu_count_physical: Number of physical CPU cores
        max_processes: Recommended max concurrent processes
        max_threads: Recommended max concurrent threads
    """

    total_ram_gb: float
    available_ram_gb: float
    cpu_count: int
    cpu_count_physical: int
    max_processes: int
    max_threads: int


class ResourceManager:
    """
    Manages system resources and calculates optimal limits for process/thread pools.

    Automatically determines safe limits based on:
    - Available RAM (reserves 25% for system)
    - CPU core count
    - Process memory footprint estimation
    """

    # Estimated memory per process (MB) - can be configured
    PROCESS_MEMORY_MB = 512
    # Reserve percentage of RAM for system
    RESERVED_RAM_PERCENT = 0.25
    # Thread multiplier per CPU core
    THREAD_PER_CORE = 2

    def __init__(self, process_memory_mb: Optional[int] = None) -> None:
        """
        Initialize resource manager.

        Args:
            process_memory_mb: Estimated memory per process in MB.
                             If None, uses default (512MB).
        """
        self.process_memory_mb = process_memory_mb or self.PROCESS_MEMORY_MB
        logger.info(f"ResourceManager initialized (process_memory: {self.process_memory_mb}MB)")

    def get_system_resources(self) -> SystemResources:
        """
        Get current system resources and calculate limits.

        Returns:
            SystemResources object with all resource information
        """
        # Memory info
        mem = psutil.virtual_memory()
        total_ram_gb = mem.total / (1024**3)
        available_ram_gb = mem.available / (1024**3)

        # CPU info
        cpu_count = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count

        # Calculate max processes based on available RAM
        reserved_ram_gb = total_ram_gb * self.RESERVED_RAM_PERCENT
        usable_ram_gb = available_ram_gb - reserved_ram_gb
        usable_ram_mb = max(0, usable_ram_gb * 1024)
        max_processes = max(1, int(usable_ram_mb / self.process_memory_mb))

        # Limit by CPU cores as well
        max_processes = min(max_processes, cpu_count)

        # Calculate max threads
        max_threads = cpu_count * self.THREAD_PER_CORE

        resources = SystemResources(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_count=cpu_count,
            cpu_count_physical=cpu_count_physical,
            max_processes=max_processes,
            max_threads=max_threads,
        )

        logger.info(
            f"System resources: RAM={total_ram_gb:.2f}GB (available={available_ram_gb:.2f}GB), "
            f"CPUs={cpu_count} (physical={cpu_count_physical}), "
            f"max_processes={max_processes}, max_threads={max_threads}"
        )

        return resources

    def get_max_processes(self) -> int:
        """
        Get recommended maximum concurrent processes.

        Returns:
            Maximum number of concurrent processes
        """
        return self.get_system_resources().max_processes

    def get_max_threads(self) -> int:
        """
        Get recommended maximum concurrent threads.

        Returns:
            Maximum number of concurrent threads
        """
        return self.get_system_resources().max_threads

    def has_sufficient_memory(self, num_processes: int) -> bool:
        """
        Check if system has sufficient memory for requested number of processes.

        Args:
            num_processes: Number of processes to check

        Returns:
            True if sufficient memory is available
        """
        required_mb = num_processes * self.process_memory_mb
        resources = self.get_system_resources()
        available_mb = resources.available_ram_gb * 1024

        reserved_mb = resources.total_ram_gb * 1024 * self.RESERVED_RAM_PERCENT
        usable_mb = available_mb - reserved_mb

        sufficient = usable_mb >= required_mb

        if not sufficient:
            logger.warning(
                f"Insufficient memory for {num_processes} processes. "
                f"Required: {required_mb}MB, Available: {usable_mb:.2f}MB"
            )

        return sufficient

    def get_memory_usage_percent(self) -> float:
        """
        Get current memory usage percentage.

        Returns:
            Memory usage as percentage (0-100)
        """
        return psutil.virtual_memory().percent

    def get_cpu_usage_percent(self, interval: float = 1.0) -> float:
        """
        Get current CPU usage percentage.

        Args:
            interval: Time interval to measure over (seconds)

        Returns:
            CPU usage as percentage (0-100)
        """
        return psutil.cpu_percent(interval=interval)
