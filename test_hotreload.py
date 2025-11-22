"""
Simple test script to validate hot-reload functionality.
Runs the application, modifies a module, and checks if reload occurs.
"""
import subprocess
import time
import sys
from pathlib import Path

def test_hotreload():
    print("=" * 60)
    print("Hot-Reload Test")
    print("=" * 60)

    # Start application
    print("\n[1/5] Starting application...")
    app_process = subprocess.Popen(
        [sys.executable, "-m", "main_app", "--config-dir", "../config"],
        cwd="src",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Wait for startup
    print("[2/5] Waiting 3 seconds for startup...")
    time.sleep(3)

    # Check if process is running
    if app_process.poll() is not None:
        print("[ERROR] Application failed to start!")
        stdout, _ = app_process.communicate()
        print(stdout)
        return False

    print("[OK] Application started successfully")

    # Modify test module
    print("\n[3/5] Modifying test module to trigger reload...")
    test_module_path = Path("../modules-backend/test-module/__init__.py")

    # Read current content
    content = test_module_path.read_text()

    # Append a comment
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    modified_content = content + f"\n# Hot-reload test modification at {timestamp}\n"

    # Write back
    test_module_path.write_text(modified_content)
    print(f"[OK] Module modified at {timestamp}")

    # Wait for reload to trigger
    print("[4/5] Waiting 3 seconds for hot-reload to trigger...")
    time.sleep(3)

    # Read logs to check for reload
    print("\n[5/5] Checking logs for reload events...")
    log_file = Path("logs/app.log")

    if log_file.exists():
        log_lines = log_file.read_text().split("\n")
        recent_logs = log_lines[-50:]  # Last 50 lines

        reload_found = False
        for line in recent_logs:
            if "reload" in line.lower() or "hot-reload" in line.lower():
                print(f"  LOG: {line}")
                reload_found = True

        if reload_found:
            print("\n[OK] Hot-reload logs found!")
        else:
            print("\n[WARN] No reload logs found in recent entries")
    else:
        print("[WARN] Log file not found")

    # Cleanup - stop application
    print("\n[Cleanup] Stopping application...")
    app_process.terminate()
    try:
        app_process.wait(timeout=5)
        print("[OK] Application stopped gracefully")
    except subprocess.TimeoutExpired:
        app_process.kill()
        print("[WARN] Application killed (didn't stop gracefully)")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        test_hotreload()
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
