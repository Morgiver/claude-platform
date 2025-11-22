"""
Error Handling Demo - Showcases retry, circuit breaker, and webhook notifications.

This demo demonstrates the error handling strategies available in the application:
1. Retry decorator with exponential backoff
2. Circuit breaker pattern
3. Combined strategy (retry + circuit breaker)
4. Webhook notifications for critical errors

Run: python examples/error_handling_demo.py
"""

import logging
import random
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup basic logging for demo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Import error handling strategies
from main_app.error_handling.strategies import (
    with_retry,
    with_circuit_breaker,
    ErrorStrategy,
)
from main_app.config import load_all_configs


def main():
    """Run all error handling demonstrations."""
    print("=" * 70)
    print("ERROR HANDLING DEMONSTRATION")
    print("=" * 70)
    print()

    # Load configuration
    try:
        config_dir = Path(__file__).parent.parent / "config"
        config = load_all_configs(config_dir)
        error_config = config["error_handling"]
        print(f"[OK] Configuration loaded from: {config_dir}")
        print(f"   - Retry max attempts: {error_config['retry']['max_attempts']}")
        print(f"   - Circuit breaker fail max: {error_config['circuit_breaker']['fail_max']}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        print("   Using default values for demo...")
        error_config = {
            "retry": {"max_attempts": 3, "wait_min_seconds": 1.0, "wait_max_seconds": 10.0},
            "circuit_breaker": {"fail_max": 5, "reset_timeout_seconds": 60},
        }
        print()

    # Demo 1: Retry decorator
    demo_retry_decorator(error_config)

    # Demo 2: Circuit breaker
    demo_circuit_breaker(error_config)

    # Demo 3: Combined strategy
    demo_combined_strategy(error_config)

    # Demo 4: Webhook notification simulation
    demo_webhook_notification()

    print()
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


def demo_retry_decorator(config):
    """Demonstrate retry decorator with simulated failures."""
    print("-" * 70)
    print("DEMO 1: Retry Decorator with Exponential Backoff")
    print("-" * 70)

    retry_config = config["retry"]

    # Create a flaky function that sometimes fails
    attempt_counter = {"count": 0}

    @with_retry(
        max_attempts=retry_config["max_attempts"],
        wait_min=retry_config["wait_min_seconds"],
        wait_max=retry_config["wait_max_seconds"],
        exceptions=(ConnectionError,),
    )
    def flaky_network_call():
        """Simulates a flaky network operation."""
        attempt_counter["count"] += 1
        print(f"   Attempt {attempt_counter['count']}: Calling network endpoint...")

        # 70% chance of failure on first 2 attempts
        if attempt_counter["count"] < 3 and random.random() < 0.7:
            print(f"   [ERROR] ConnectionError: Network temporarily unavailable")
            raise ConnectionError("Simulated network failure")

        print(f"   [OK] Success! Data retrieved")
        return {"status": "ok", "data": "sample_data"}

    try:
        print("\nCalling flaky_network_call() with retry protection...")
        result = flaky_network_call()
        print(f"\n[OK] Final result: {result}")
        print(f"   Total attempts needed: {attempt_counter['count']}")
    except ConnectionError as e:
        print(f"\n[ERROR] Failed after {retry_config['max_attempts']} attempts: {e}")

    print()


def demo_circuit_breaker(config):
    """Demonstrate circuit breaker pattern."""
    print("-" * 70)
    print("DEMO 2: Circuit Breaker Pattern")
    print("-" * 70)

    cb_config = config["circuit_breaker"]

    # Create a function that always fails (simulating down service)
    failure_counter = {"count": 0}

    @with_circuit_breaker(
        fail_max=cb_config["fail_max"],
        reset_timeout=cb_config["reset_timeout_seconds"],
        name="external_api",
    )
    def external_api_call():
        """Simulates calling an external API that is down."""
        failure_counter["count"] += 1
        print(f"   Attempt {failure_counter['count']}: Calling external API...")
        print(f"   [ERROR] TimeoutError: API not responding")
        raise TimeoutError("External API timeout")

    print(f"\nCalling external_api_call() - it will fail {cb_config['fail_max']} times...")
    print(f"Circuit breaker will OPEN after {cb_config['fail_max']} failures\n")

    # Try to call the API multiple times
    for i in range(cb_config["fail_max"] + 2):
        try:
            time.sleep(0.1)  # Small delay between calls
            result = external_api_call()
        except TimeoutError:
            print(f"   Call {i+1}: Failed (circuit state: {external_api_call.circuit_breaker.state})")
        except Exception as e:
            # Circuit breaker opened - it's now rejecting calls
            print(f"   Call {i+1}: [BLOCKED] CIRCUIT BREAKER OPEN - Call rejected!")
            print(f"            Circuit will reset in {cb_config['reset_timeout_seconds']} seconds")
            break

    print(f"\n[OK] Circuit breaker successfully prevented cascading failures")
    print(f"   Total failures before opening: {failure_counter['count']}")
    print()


def demo_combined_strategy(config):
    """Demonstrate combined retry + circuit breaker strategy."""
    print("-" * 70)
    print("DEMO 3: Combined Strategy (Retry + Circuit Breaker)")
    print("-" * 70)

    retry_config = config["retry"]
    cb_config = config["circuit_breaker"]

    attempt_counter = {"count": 0}

    @ErrorStrategy.critical_operation(
        max_attempts=retry_config["max_attempts"],
        fail_max=cb_config["fail_max"],
        reset_timeout=cb_config["reset_timeout_seconds"],
    )
    def load_critical_resource():
        """Simulates loading a critical resource with transient failures."""
        attempt_counter["count"] += 1
        print(f"   Attempt {attempt_counter['count']}: Loading critical resource...")

        # First 2 attempts fail transiently, 3rd succeeds
        if attempt_counter["count"] < 3:
            print(f"   [ERROR] Transient failure (will retry)")
            raise ConnectionError("Temporary connection issue")

        print(f"   [OK] Resource loaded successfully!")
        return {"resource": "critical_data", "version": "1.0"}

    print("\nCalling load_critical_resource() with combined protection...")
    print("This operation has BOTH retry and circuit breaker\n")

    try:
        result = load_critical_resource()
        print(f"\n[OK] Final result: {result}")
        print(f"   Total attempts: {attempt_counter['count']}")
        print(f"   Strategy: Retry handled transient failures successfully")
    except Exception as e:
        print(f"\n[ERROR] Operation failed: {e}")

    print()


def demo_webhook_notification():
    """Demonstrate webhook notification setup."""
    print("-" * 70)
    print("DEMO 4: Webhook Notification Integration")
    print("-" * 70)

    print("\nWebhook notifications are integrated with the Application class.")
    print("\nTo enable webhook notifications:")
    print("   1. Set WEBHOOK_URL environment variable:")
    print("      export WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'")
    print()
    print("   2. Start the application:")
    print("      python -m src.main_app.core.application")
    print()
    print("   3. Critical errors will automatically be sent to the webhook URL")
    print()
    print("Example webhook payload structure:")
    print("   {")
    print('     "timestamp": "2025-01-17T10:30:00.000000",')
    print('     "severity": "critical",')
    print('     "error_type": "ModuleLoadError",')
    print('     "error_message": "Failed to load module: auth_service",')
    print('     "context": {"module": "auth_service", "retry_count": 3}')
    print("   }")
    print()
    print("[OK] Webhook integration ready (configure WEBHOOK_URL to activate)")
    print()


if __name__ == "__main__":
    main()
