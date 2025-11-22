# Feature-006: Application Startup & Integration

**Status**: 🎯 planned
**Scope**: Medium
**Complexity**: Medium
**Priority**: P2 (Ties everything together)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/6

---

## Description

Complete the application startup flow by integrating all components (config loading, logging setup, module loading, error handling) into a cohesive application lifecycle. This feature ensures Application class orchestrates all components correctly and handles startup/shutdown gracefully.

---

## Objectives

1. **Complete Startup Sequence**
   - Load configuration from files
   - Setup centralized logging with config
   - Initialize EventBus, ModuleLoader, ResourceManager
   - Load all enabled modules with error handling
   - Publish app.started event
   - Enter main application loop

2. **Complete Shutdown Sequence**
   - Catch shutdown signals (SIGINT, SIGTERM)
   - Publish app.shutdown event
   - Shutdown all modules (call hooks)
   - Clear EventBus subscriptions
   - Stop file watchers
   - Log shutdown completion

3. **Enhance Main Loop**
   - Replace simple sleep() with useful operations
   - Monitor resource usage periodically (every 60s)
   - Log resource metrics (RAM, CPU)
   - Handle KeyboardInterrupt gracefully

4. **CLI Argument Parsing**
   - Add argparse for command-line options
   - Support `--config-dir` to specify config directory
   - Support `--test` flag (handled in Feature-007)
   - Support `--version` to show version info

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/core/application.py` (complete integration)
- `src/main_app/__main__.py` (add CLI argument parsing)

**Functionality Delivered**:
- Application starts with complete component integration
- Configuration, logging, modules all initialized in correct order
- Graceful shutdown on signals and KeyboardInterrupt
- Resource monitoring in main loop
- CLI arguments supported for flexibility
- Clear startup/shutdown logging

---

## Dependencies

**Upstream**:
- Feature-001 (Configuration System) - MUST be completed
- Feature-002 (Centralized Logging) - MUST be completed
- Feature-003 (Error Handling Integration) - MUST be completed
- Feature-004 (Module Loading) - MUST be completed

**Downstream**:
- Feature-007 (Test Mode) builds on this
- Feature-008 (Dummy Modules) validates this

---

## Acceptance Criteria

**Must Have**:
1. Application loads config from `config/` directory on startup
2. Logging setup completed before any component initialization
3. All components initialized in correct order (EventBus → ResourceManager → ModuleLoader)
4. Modules loaded after core components ready
5. `app.started` event published with resource info
6. Main loop monitors resources every 60 seconds
7. SIGINT/SIGTERM trigger graceful shutdown
8. `app.shutdown` event published before component shutdown
9. All modules shutdown() called before exit
10. CLI arguments parsed: `--config-dir`, `--version`
11. Startup completes in < 2 seconds (for 5 modules)

**Nice to Have** (bonus, not required):
- `--debug` flag for verbose logging - **Optional in ALPHA**
- Health check endpoint - **Skip in ALPHA**
- Metrics export - **Skip in ALPHA**

---

## Validation Approach (Manual Testing)

**Test Case 1: Complete Startup Sequence**
```bash
python -m main_app
# Expected logs sequence:
#   1. "Loading configuration from config/"
#   2. "Setting up logging..."
#   3. "EventBus initialized"
#   4. "ResourceManager initialized"
#   5. "ModuleLoader initialized (hot-reload=enabled)"
#   6. "System resources: X.XXG RAM, Y CPUs, limits: Z processes / W threads"
#   7. "Loading modules from configuration..."
#   8. "Module 'mod-X' loaded successfully"
#   9. "Module 'mod-X' initialized"
#   10. "Application started successfully"
#   11. "Published event: app.started"
# Startup time: < 2 seconds
```

**Test Case 2: Graceful Shutdown (SIGINT)**
```bash
python -m main_app
# Press Ctrl+C
# Expected logs sequence:
#   1. "Received signal 2" (SIGINT)
#   2. "Shutting down application..."
#   3. "Published event: app.shutdown"
#   4. "Module 'mod-X' unloaded"
#   5. "File observer stopped"
#   6. "ModuleLoader shutdown complete"
#   7. "Cleared all subscribers"
#   8. "Application shutdown complete"
# Exit code: 0
```

**Test Case 3: Resource Monitoring in Main Loop**
```bash
python -m main_app
# Let run for 2+ minutes
# Expected: Every 60 seconds, log shows:
#   "Resource usage: RAM=XX.X%, CPU=XX.X%"
#   "Active modules: N"
# Main loop doesn't block shutdown
```

**Test Case 4: CLI Arguments**
```bash
# Custom config directory
python -m main_app --config-dir /path/to/config
# Expected: Loads config from specified directory

# Version info
python -m main_app --version
# Expected: Prints "main-orchestrator v0.1.0-alpha.1" and exits

# Invalid argument
python -m main_app --invalid-flag
# Expected: Error message, usage help printed, exit code 1
```

**Test Case 5: Startup Failure Handling**
```bash
# Missing config file
rm config/main.yaml
python -m main_app
# Expected: Error "Config file not found", exit gracefully, exit code 1

# Invalid YAML syntax
# Corrupt config/main.yaml
python -m main_app
# Expected: Error "Failed to parse config", exit gracefully, exit code 1

# Module load failure (one module fails)
# Config has non-existent module path
python -m main_app
# Expected: Module error logged, app continues with other modules, exit code 0
```

---

## Implementation Notes

**Complete Application Class**:

```python
# src/main_app/core/application.py

import argparse
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..config.config_loader import load_all_configs
from ..logging.logger import setup_logging
from .event_bus import EventBus
from .module_loader import ModuleLoader, ModuleConfig
from .resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class Application:
    """Main application orchestrator."""

    def __init__(self, config_dir: Path) -> None:
        """
        Initialize application.

        Args:
            config_dir: Path to configuration directory
        """
        # Load configuration
        logger.info(f"Loading configuration from {config_dir}")
        self.config = load_all_configs(config_dir)

        # Setup logging from config
        setup_logging(self.config)

        # Initialize core components
        self.event_bus = EventBus()
        self.resource_manager = ResourceManager(
            process_memory_mb=self.config.get("resources", {}).get("process_memory_mb", 512)
        )

        hot_reload = self.config.get("app", {}).get("hot_reload", True)
        self.module_loader = ModuleLoader(watch_reload=hot_reload)

        self._running = False
        self._module_configs: Dict[str, Dict[str, Any]] = {}

        logger.info("Application initialized")

    def start(self) -> None:
        """Start the application."""
        logger.info("Starting application...")

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Log system resources
        resources = self.resource_manager.get_system_resources()
        logger.info(
            f"System resources: {resources.total_ram_gb:.2f}GB RAM, "
            f"{resources.cpu_count} CPUs, "
            f"limits: {resources.max_processes} processes / {resources.max_threads} threads"
        )

        # Load modules
        logger.info("Loading modules from configuration...")
        self._load_modules()

        # Publish startup event
        self.event_bus.publish("app.started", {"resources": resources})
        logger.info("Published event: app.started")

        self._running = True
        logger.info("Application started successfully")

        # Main loop
        self._run()

    def _load_modules(self) -> None:
        """Load modules from configuration."""
        modules_config = self.config.get("modules", [])

        for module_data in modules_config:
            config = ModuleConfig(
                name=module_data["name"],
                path=module_data["path"],
                enabled=module_data.get("enabled", True),
                config=module_data.get("config", {})
            )

            # Load module
            success = self.module_loader.load_module(config)

            if success:
                # Call initialize hook
                module = self.module_loader.get_module(config.name)
                if hasattr(module, "initialize"):
                    try:
                        module.initialize(self.event_bus, config.config or {})
                        self._module_configs[config.name] = config.config or {}
                        self.event_bus.publish("module.loaded", {
                            "name": config.name,
                            "config": config.config
                        })
                        logger.info(f"Module '{config.name}' initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize module '{config.name}': {e}", exc_info=True)
                        self.event_bus.publish("module.error", {
                            "name": config.name,
                            "error": str(e)
                        })
            else:
                self.event_bus.publish("module.error", {
                    "name": config.name,
                    "error": "Failed to load"
                })

    def _run(self) -> None:
        """Main application loop."""
        last_resource_check = time.time()

        try:
            while self._running:
                # Resource monitoring every 60 seconds
                if time.time() - last_resource_check >= 60:
                    ram_usage = self.resource_manager.get_memory_usage_percent()
                    cpu_usage = self.resource_manager.get_cpu_usage_percent(interval=0.1)
                    active_modules = len(self.module_loader.get_loaded_modules())

                    logger.info(
                        f"Resource usage: RAM={ram_usage:.1f}%, CPU={cpu_usage:.1f}%, "
                        f"Active modules: {active_modules}"
                    )
                    last_resource_check = time.time()

                # Sleep to avoid busy-waiting
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
        logger.info("Published event: app.shutdown")

        # Shutdown modules
        self.module_loader.shutdown()

        # Clear event bus
        self.event_bus.clear()

        logger.info("Application shutdown complete")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle OS signals for graceful shutdown."""
        logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="main/ - Modular Orchestration Platform"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Path to configuration directory (default: config/)"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test mode (discover and run module tests)"
    )

    args = parser.parse_args()

    # Handle version
    if args.version:
        print("main-orchestrator v0.1.0-alpha.1")
        sys.exit(0)

    # Handle test mode (Feature-007)
    if args.test:
        print("Test mode not yet implemented (Feature-007)")
        sys.exit(1)

    # Normal mode: Start application
    try:
        app = Application(config_dir=args.config_dir)
        app.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**CLI Usage Examples**:
```bash
# Normal startup
python -m main_app

# Custom config directory
python -m main_app --config-dir /etc/main-orchestrator

# Show version
python -m main_app --version

# Test mode (Feature-007)
python -m main_app --test
```

---

## Rough Effort Estimate

**Time**: 3-4 hours (including testing)

**Breakdown**:
- Complete Application class integration: 1.5 hours
- Add CLI argument parsing: 30 minutes
- Implement resource monitoring: 30 minutes
- Manual testing (startup/shutdown/signals): 1-1.5 hours

---

## Success Metrics

**Functional**:
- Application starts and shuts down gracefully
- All components integrated correctly
- Resource monitoring works
- CLI arguments parsed correctly
- Startup time < 2 seconds (5 modules)

**Quality**:
- Clear, comprehensive logging throughout
- No crashes or unexpected exits
- Graceful error handling
- Code follows project conventions
- Application.py remains < 400 lines

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.3.0-alpha.1 or v0.4.0-alpha.1
**Previous Feature**: Feature-005 (Module Hot-Reload System)
**Next Feature**: Feature-007 (Test Mode Implementation)
