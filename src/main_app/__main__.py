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

    # Handle --test flag (placeholder)
    if args.test:
        print("Test mode not yet implemented (Feature-007)")
        print("This feature will be added in a future release.")
        sys.exit(0)

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
