"""Main entry point - Run application with python -m main_app."""

import argparse
import sys
from pathlib import Path

from .core.application import Application


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Main Application - Modular Application Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Path to configuration directory (default: config/)",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version information and exit",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (placeholder for Feature-007)",
    )

    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        print("Main Application v0.5.0-alpha.1")
        print("ALPHA Development Version")
        sys.exit(0)

    # Handle --test flag
    if args.test:
        from .testing.test_runner import run_all_tests
        from .config.config_loader import load_all_configs
        from .logging.logger import setup_logging
        from .core.event_bus import EventBus
        from .core.module_loader import ModuleLoader

        print("\n[TEST MODE] Activated\n")

        # Setup configuration
        config_dir = Path(args.config_dir)
        try:
            configs = load_all_configs(config_dir)
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            sys.exit(1)

        # Setup logging
        try:
            setup_logging(configs.get("logging", {}))
        except Exception as e:
            print(f"Error setting up logging: {e}", file=sys.stderr)
            sys.exit(1)

        # Create EventBus and ModuleLoader (without hot-reload)
        try:
            event_bus = EventBus()
            module_loader = ModuleLoader(watch_reload=False)
        except Exception as e:
            print(f"Error creating module loader: {e}", file=sys.stderr)
            sys.exit(1)

        # Load modules from configuration
        try:
            from .core.module_loader import ModuleConfig
            modules_config = configs.get("modules", {}).get("modules", [])
            for module_data in modules_config:
                config = ModuleConfig(
                    name=module_data["name"],
                    path=module_data["path"],
                    enabled=module_data.get("enabled", True),
                    config=module_data.get("config", {})
                )
                if config.enabled:
                    success = module_loader.load_module(config)
                    if success:
                        module = module_loader.get_module(config.name)
                        if hasattr(module, "initialize"):
                            module.initialize(event_bus, config.config)
        except Exception as e:
            print(f"Error loading modules: {e}", file=sys.stderr)
            sys.exit(1)

        # Run all tests
        # Calculate main tests directory relative to project root
        project_root = Path(__file__).parent.parent.parent
        main_tests_dir = project_root / "tests"
        exit_code = run_all_tests(module_loader, main_tests_dir)
        sys.exit(exit_code)

    # Create application with specified config directory
    config_dir = Path(args.config_dir)

    try:
        app = Application(config_dir=config_dir)
        app.start()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
