# main/ ALPHA Demo Guide

Complete demonstration guide for validating the Multi-Agent Orchestrator prototype.

## Quick Start (Automated Demo)

The fastest way to validate all ALPHA features is to run the automated demo script:

```bash
# Run automated demo (validates all features)
python demo.py
```

**Expected Output**:
```
============================================================
main/ ALPHA Demo - Automated Validation
============================================================

[1/7] Cleaning up previous demo runs...
✅ Cleanup complete

[2/7] Validating configuration files...
✅ Configuration files exist

[3/7] Starting application and validating module loading...
✅ Producer module loaded
✅ Consumer module loaded

[4/7] Validating EventBus communication...
✅ Producer publishing events
✅ Consumer receiving events

[5/7] Validating centralized logging...
✅ Log file created: logs/app.log
✅ Log file contains application logs (2456 bytes)

[6/7] Testing graceful shutdown...
✅ Graceful shutdown successful (exit code: 0)

[7/7] Running test mode...
✅ Test mode passed (6+ assertions)

============================================================
✅ DEMO COMPLETE - ALL CHECKS PASSED
============================================================

Validation report: reports/alpha/alpha-validation-report.md
Demo logs: demo-output/app.log
Test logs: demo-output/test.log
```

**What the Automated Demo Validates**:
- Module loading from configuration (producer + consumer)
- EventBus communication (events published and received)
- Centralized logging (logs written to file)
- Graceful shutdown (clean exit on interrupt)
- Test mode execution (all tests passing)

**Output Artifacts**:
- `reports/alpha/alpha-validation-report.md` - Validation results
- `demo-output/app.log` - Application execution logs
- `demo-output/test.log` - Test execution output

---

## Manual Demo (Step-by-Step)

For a detailed walkthrough or troubleshooting, follow these manual steps:

### Step 1: Verify Configuration

**Action**: Check configuration files exist

```bash
# List configuration files
ls config/
```

**Expected Output**:
```
logging.yaml
main.yaml
modules.yaml
```

**Validates**: Configuration system (Feature-001)

---

### Step 2: Start the Application

**Action**: Run the main application

```bash
cd src
python -m main_app
```

**Expected Output** (first 10 seconds):
```
2025-01-17 10:30:15,123 - INFO - Starting Multi-Agent Orchestrator
2025-01-17 10:30:15,145 - INFO - Loading configuration from config/
2025-01-17 10:30:15,189 - INFO - Module 'mod-dummy-producer' loaded successfully
2025-01-17 10:30:15,192 - INFO - Module 'mod-dummy-consumer' loaded successfully
2025-01-17 10:30:15,195 - INFO - Initializing mod-dummy-producer
2025-01-17 10:30:15,197 - INFO - Producer thread started
2025-01-17 10:30:15,198 - INFO - Initializing mod-dummy-consumer
2025-01-17 10:30:15,200 - INFO - Subscribing to event: test.ping
2025-01-17 10:30:15,201 - INFO - Consumer subscribed to 1 event(s)
2025-01-17 10:30:20,205 - INFO - Publishing test.ping event #1
2025-01-17 10:30:20,206 - INFO - Received event: {'message': 'hello from producer', 'timestamp': 1705487420.205, 'counter': 1}
```

**Validates**:
- Module loading (Feature-004)
- Module lifecycle initialization (Feature-004)
- Centralized logging (Feature-002)

---

### Step 3: Verify EventBus Communication

**Action**: Let application run for 15 seconds, observe logs

**Expected Behavior**:
- Producer publishes events every 5 seconds
- Consumer receives each event immediately
- Event counter increments (1, 2, 3...)

**Example Log Snippet**:
```
2025-01-17 10:30:20,205 - INFO - Publishing test.ping event #1
2025-01-17 10:30:20,206 - INFO - Received event: {'message': 'hello from producer', ...}
2025-01-17 10:30:25,210 - INFO - Publishing test.ping event #2
2025-01-17 10:30:25,211 - INFO - Received event: {'message': 'hello from producer', ...}
```

**Validates**: EventBus communication (Feature-004, Feature-008)

---

### Step 4: Check Log File

**Action**: Open `logs/app.log` in another terminal/editor

```bash
# View log file (from project root)
cat logs/app.log

# Or follow logs in real-time
tail -f logs/app.log
```

**Expected Content**:
- Application startup messages
- Module loading confirmations
- Event publishing/receiving logs
- Timestamps and log levels

**Validates**: Centralized logging with file output (Feature-002)

---

### Step 5: Test Graceful Shutdown

**Action**: Stop the application with Ctrl+C

```bash
# Press Ctrl+C in the terminal running the application
^C
```

**Expected Output**:
```
^C
Application interrupted by user
2025-01-17 10:32:45,300 - INFO - Shutting down application
2025-01-17 10:32:45,301 - INFO - Shutting down mod-dummy-producer
2025-01-17 10:32:45,305 - INFO - Producer thread stopped
2025-01-17 10:32:45,306 - INFO - Shutting down mod-dummy-consumer
2025-01-17 10:32:45,307 - INFO - Unsubscribing from event: test.ping
2025-01-17 10:32:45,308 - INFO - Consumer unsubscribed from all events
2025-01-17 10:32:45,310 - INFO - Application shutdown complete
```

**Validates**: Graceful shutdown handling (Feature-006)

---

### Step 6: Run Test Mode

**Action**: Execute application in test mode

```bash
cd src
python -m main_app --test
```

**Expected Output**:
```
[TEST MODE] Activated

Running tests from: E:\claude\main\tests
Discovered 2 test files

Running: tests\test_config_loader.py
✅ PASSED (3 assertions)

Running: tests\test_event_bus.py
✅ PASSED (3 assertions)

Checking modules for tests:
Module 'mod-dummy-producer' provides tests: ['tests/']
Module 'mod-dummy-consumer' provides tests: ['tests/']

=========================================
TEST SUMMARY
=========================================
Tests Run: 2
Tests Passed: 2
Tests Failed: 0
Exit Code: 0
```

**Validates**: Test mode execution (Feature-007)

---

### Step 7: Hot-Reload Validation (Optional)

**Action**: Test hot-reload by modifying a module file

1. Start the application: `python -m main_app`
2. Wait for modules to load and events to start flowing
3. Edit `modules-backend/mod-dummy-producer/__init__.py`
4. Make a trivial change (add a comment or modify log message)
5. Save the file
6. Observe logs for reload message

**Expected Output**:
```
2025-01-17 10:35:12,500 - INFO - File change detected: mod-dummy-producer/__init__.py
2025-01-17 10:35:12,550 - INFO - Reloading module: mod-dummy-producer
2025-01-17 10:35:12,555 - INFO - Module 'mod-dummy-producer' reloaded successfully
```

**Validates**: Hot-reload system (Feature-005)

**Note**: This is an interactive test and not included in automated demo.

---

## Troubleshooting

### Application Won't Start

**Symptom**: Error on startup, application exits immediately

**Common Causes**:
- Configuration files missing
- Invalid YAML syntax in config files
- Module paths incorrect in `modules.yaml`

**Solution**:
1. Verify config files exist: `ls config/`
2. Check YAML syntax: `python -c "import yaml; yaml.safe_load(open('config/main.yaml'))"`
3. Verify module paths in `config/modules.yaml`

---

### No Events Published/Received

**Symptom**: Application runs but no event logs appear

**Common Causes**:
- Modules not enabled in `config/modules.yaml`
- Producer thread failed to start
- Consumer not subscribed to correct event type

**Solution**:
1. Check module loading logs for errors
2. Verify `enabled: true` in `modules.yaml`
3. Check producer publish interval (default: 5 seconds)

---

### Log File Not Created

**Symptom**: `logs/app.log` does not exist

**Common Causes**:
- Logging configuration issue
- Permissions problem
- Working directory incorrect

**Solution**:
1. Check `config/logging.yaml` exists
2. Verify `logs/` directory exists and is writable
3. Run from project root directory

---

### Test Mode Fails

**Symptom**: `python -m main_app --test` exits with non-zero code

**Common Causes**:
- Test files have errors
- Module tests not discoverable
- Configuration issues

**Solution**:
1. Run tests individually to isolate failures
2. Check test file naming (`test_*.py`)
3. Verify module `get_tests()` functions exist

---

## Success Criteria Checklist

Use this checklist to verify all ALPHA features are working:

- [ ] **Configuration System**: Config files loaded from `config/` directory
- [ ] **Module Loading**: Producer and consumer modules load successfully
- [ ] **Module Initialization**: Modules initialize with EventBus and config
- [ ] **EventBus Communication**: Events published and received between modules
- [ ] **Centralized Logging**: Logs written to `logs/app.log` with timestamps
- [ ] **Resource Management**: RAM/CPU limits calculated on startup
- [ ] **Graceful Shutdown**: Ctrl+C triggers clean shutdown with no errors
- [ ] **Test Mode**: All tests discovered and executed successfully
- [ ] **Hot-Reload** (Optional): File changes trigger module reload

---

## Next Steps

After successful demo:

1. Review validation report: `reports/alpha/alpha-validation-report.md`
2. Proceed to Step A9 (Feedback Checkpoint) for user feedback
3. Decide next action:
   - Add more features (Step A9B - Feature Discovery)
   - Refine existing features (create refinement missions)
   - Migrate to BETA (deliberate user choice)

**ALPHA Development Complete**: All 9 features implemented and validated!
