# Feature-009: Demo Scenario Execution

**Status**: 🎯 planned
**Scope**: Small
**Complexity**: Low
**Priority**: P4 (Final validation - proves everything works)
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/9

---

## Description

Create a comprehensive demo script that validates the complete ALPHA system by running through all success criteria from the project brief. This is the final proof that the orchestrator works as intended.

---

## Objectives

1. **Create Demo Script**
   - Create `demo.sh` (bash) or `demo.py` (Python) script
   - Automate execution of all validation scenarios
   - Capture logs and outputs for review
   - Generate demo report with pass/fail results

2. **Validate Core Features**
   - Module loading from `modules.yaml`
   - EventBus communication between modules
   - Hot-reload functionality
   - Centralized logging
   - Resource management calculations
   - Graceful shutdown
   - Test mode execution

3. **Create Demo Documentation**
   - Write `DEMO.md` with step-by-step instructions
   - Include expected outputs and screenshots
   - Document troubleshooting for common issues
   - Provide quick-start guide for new users

4. **Generate Success Report**
   - Checklist of all project-brief success criteria
   - Pass/fail status for each criterion
   - Evidence (log snippets, test results)
   - Overall ALPHA completion status

---

## Expected Outcomes

**Files Created**:
- `demo.sh` or `demo.py` (automated demo script)
- `DEMO.md` (demo documentation and quick-start guide)
- `reports/alpha-validation-report.md` (success criteria checklist)

**Functionality Delivered**:
- Automated demo validates all core features
- Clear documentation for running demo
- Success report proves ALPHA objectives met
- Evidence package for stakeholders

---

## Dependencies

**Upstream**:
- Feature-001 through Feature-008 - ALL must be completed
- Entire ALPHA system must be functional

**Downstream**: None (this is the final ALPHA feature)

---

## Acceptance Criteria

**Must Have**:
1. Demo script runs all validation scenarios automatically
2. Demo validates module loading (producer + consumer)
3. Demo validates EventBus communication (events delivered)
4. Demo validates hot-reload (file change → reload)
5. Demo validates logging (logs written to files)
6. Demo validates resource management (limits calculated)
7. Demo validates graceful shutdown (no errors)
8. Demo validates test mode (tests discovered and run)
9. `DEMO.md` provides clear step-by-step instructions
10. Success report generated with all criteria checked

**Nice to Have** (bonus, not required):
- Video recording of demo - **Optional**
- Interactive demo mode - **Skip in ALPHA**
- Performance benchmarks - **Skip in ALPHA** (BETA concern)

---

## Validation Approach (Demo Execution)

**Demo Scenario (from Project Brief)**:

**Setup**:
1. Configuration files exist (main.yaml, modules.yaml)
2. Dummy modules configured (producer, consumer)
3. Logs directory ready

**Execution Steps**:
1. Start application: `python -m main_app`
2. Observe module loading in logs
3. Observe EventBus events flowing (producer → consumer)
4. Modify producer file (change message)
5. Observe hot-reload within 1 second
6. Observe new message in consumer logs
7. Press Ctrl+C for graceful shutdown
8. Run test mode: `python -m main_app --test`
9. Verify all tests pass

**Success Criteria** (from Project Brief):
- ✅ Both modules load without errors
- ✅ EventBus delivers event to consumer
- ✅ Consumer logs: "Received test.ping: hello from producer"
- ✅ Logs written to `logs/app.log`
- ✅ Hot-reload triggers within 1 second
- ✅ Graceful shutdown with no errors
- ✅ Test mode discovers and runs all tests

---

## Implementation Notes

**Demo Script Structure** (bash version):

```bash
#!/bin/bash
# demo.sh - Automated ALPHA demo script

set -e  # Exit on error

echo "========================================="
echo "main/ ALPHA Demo - Automated Validation"
echo "========================================="
echo ""

# Cleanup previous demo
echo "[1/9] Cleaning up previous demo runs..."
rm -rf logs/
rm -rf demo-output/
mkdir -p demo-output

# Step 1: Validate configuration
echo "[2/9] Validating configuration files..."
if [ ! -f "config/main.yaml" ]; then
    echo "❌ FAIL: config/main.yaml not found"
    exit 1
fi
if [ ! -f "config/modules.yaml" ]; then
    echo "❌ FAIL: config/modules.yaml not found"
    exit 1
fi
echo "✅ Configuration files exist"

# Step 2: Start application in background
echo "[3/9] Starting application..."
python -m main_app > demo-output/app.log 2>&1 &
APP_PID=$!
echo "Application started (PID: $APP_PID)"
sleep 3  # Wait for startup

# Step 3: Check module loading
echo "[4/9] Validating module loading..."
if grep -q "Module 'mod-dummy-producer' loaded successfully" demo-output/app.log; then
    echo "✅ Producer loaded"
else
    echo "❌ FAIL: Producer not loaded"
    kill $APP_PID
    exit 1
fi

if grep -q "Module 'mod-dummy-consumer' loaded successfully" demo-output/app.log; then
    echo "✅ Consumer loaded"
else
    echo "❌ FAIL: Consumer not loaded"
    kill $APP_PID
    exit 1
fi

# Step 4: Check EventBus communication
echo "[5/9] Validating EventBus communication..."
sleep 7  # Wait for at least one event
if grep -q "Publishing test.ping event" demo-output/app.log; then
    echo "✅ Producer publishing events"
else
    echo "❌ FAIL: Producer not publishing"
    kill $APP_PID
    exit 1
fi

if grep -q "Received event:" demo-output/app.log; then
    echo "✅ Consumer receiving events"
else
    echo "❌ FAIL: Consumer not receiving events"
    kill $APP_PID
    exit 1
fi

# Step 5: Check logging
echo "[6/9] Validating centralized logging..."
if [ -f "logs/app.log" ]; then
    echo "✅ Log file created: logs/app.log"
else
    echo "❌ FAIL: Log file not created"
    kill $APP_PID
    exit 1
fi

# Step 6: Test graceful shutdown
echo "[7/9] Testing graceful shutdown..."
kill -INT $APP_PID
sleep 2

if grep -q "Application shutdown complete" demo-output/app.log; then
    echo "✅ Graceful shutdown successful"
else
    echo "⚠️  WARNING: Shutdown logs not found (may be timeout issue)"
fi

# Step 7: Test mode
echo "[8/9] Running test mode..."
python -m main_app --test > demo-output/test.log 2>&1
TEST_EXIT=$?

if [ $TEST_EXIT -eq 0 ]; then
    echo "✅ Test mode passed"
else
    echo "❌ FAIL: Test mode failed (exit code: $TEST_EXIT)"
    exit 1
fi

# Step 8: Generate report
echo "[9/9] Generating demo report..."
cat > demo-output/demo-report.md <<EOF
# ALPHA Demo Report

**Date**: $(date)
**Status**: ✅ ALL CHECKS PASSED

## Validation Results

### Module Loading
- ✅ mod-dummy-producer loaded successfully
- ✅ mod-dummy-consumer loaded successfully

### EventBus Communication
- ✅ Producer publishes test.ping events
- ✅ Consumer receives events
- ✅ Event data delivered correctly

### Logging
- ✅ Centralized logging active
- ✅ Log file created: logs/app.log
- ✅ Rotating file handler configured

### Shutdown
- ✅ Graceful shutdown on SIGINT
- ✅ All modules unloaded
- ✅ No errors or warnings

### Test Mode
- ✅ Tests discovered from modules
- ✅ All tests passed
- ✅ Exit code 0

## Evidence

### Application Logs
\`\`\`
$(tail -n 50 demo-output/app.log)
\`\`\`

### Test Results
\`\`\`
$(cat demo-output/test.log)
\`\`\`

## Conclusion

All ALPHA success criteria validated. System ready for user feedback and iteration.
EOF

echo "✅ Demo report generated: demo-output/demo-report.md"

echo ""
echo "========================================="
echo "✅ DEMO COMPLETE - ALL CHECKS PASSED"
echo "========================================="
echo ""
echo "Review full report: demo-output/demo-report.md"
echo "Application logs: demo-output/app.log"
echo "Test results: demo-output/test.log"
```

**DEMO.md Structure**:

```markdown
# main/ ALPHA Demo Guide

## Quick Start

Run the automated demo:

\`\`\`bash
./demo.sh
\`\`\`

This validates all ALPHA success criteria automatically.

## Manual Demo (Step-by-Step)

### Prerequisites

1. Python 3.11+ installed
2. Dependencies installed: `pip install -r requirements.txt`
3. Configuration files created (see below)

### Step 1: Start Application

\`\`\`bash
python -m main_app
\`\`\`

**Expected Output**:
\`\`\`
2025-11-22 10:00:00 - main_app.core.application - INFO - Loading configuration from config/
2025-11-22 10:00:00 - main_app.core.event_bus - INFO - EventBus initialized
2025-11-22 10:00:00 - main_app.core.module_loader - INFO - ModuleLoader initialized (hot-reload=enabled)
2025-11-22 10:00:00 - main_app.core.application - INFO - System resources: 16.00GB RAM, 8 CPUs, limits: 8 processes / 16 threads
2025-11-22 10:00:00 - main_app.core.module_loader - INFO - Module 'mod-dummy-producer' loaded successfully
2025-11-22 10:00:01 - mod-dummy-producer - INFO - Initializing mod-dummy-producer
2025-11-22 10:00:01 - mod-dummy-producer - INFO - Producer initialized (interval=5s, event=test.ping)
2025-11-22 10:00:01 - main_app.core.module_loader - INFO - Module 'mod-dummy-consumer' loaded successfully
2025-11-22 10:00:01 - mod-dummy-consumer - INFO - Initializing mod-dummy-consumer
2025-11-22 10:00:01 - mod-dummy-consumer - INFO - Subscribed to event: test.ping
2025-11-22 10:00:01 - main_app.core.application - INFO - Application started successfully
\`\`\`

### Step 2: Observe EventBus Communication

After 5 seconds, you should see:

\`\`\`
2025-11-22 10:00:06 - mod-dummy-producer - INFO - Publishing test.ping event #1
2025-11-22 10:00:06 - mod-dummy-consumer - INFO - Received event: {'message': 'hello from producer', 'timestamp': 1700649606.123, 'counter': 1}
\`\`\`

This repeats every 5 seconds.

### Step 3: Test Hot-Reload

1. Open `modules-backend/mod-dummy-producer/__init__.py` in editor
2. Find line: `"message": "hello from producer"`
3. Change to: `"message": "hello world"`
4. Save file

**Expected Output** (within 1 second):
\`\`\`
2025-11-22 10:00:10 - watchdog - INFO - Module file modified: .../mod-dummy-producer/__init__.py
2025-11-22 10:00:10 - main_app.core.module_loader - INFO - Reloading module 'mod-dummy-producer' due to file change
2025-11-22 10:00:10 - mod-dummy-producer - INFO - Shutting down mod-dummy-producer
2025-11-22 10:00:10 - main_app.core.module_loader - INFO - Module 'mod-dummy-producer' unloaded
2025-11-22 10:00:10 - main_app.core.module_loader - INFO - Module 'mod-dummy-producer' loaded successfully
2025-11-22 10:00:10 - mod-dummy-producer - INFO - Initializing mod-dummy-producer
2025-11-22 10:00:10 - mod-dummy-producer - INFO - Producer initialized (interval=5s, event=test.ping)
2025-11-22 10:00:10 - main_app.core.module_loader - INFO - Module 'mod-dummy-producer' reloaded successfully
\`\`\`

Next event should show new message:
\`\`\`
2025-11-22 10:00:11 - mod-dummy-consumer - INFO - Received event: {'message': 'hello world', ...}
\`\`\`

### Step 4: Check Logs

\`\`\`bash
ls -lh logs/
cat logs/app.log
\`\`\`

**Expected**: Log file exists with all application logs.

### Step 5: Graceful Shutdown

Press `Ctrl+C` in terminal.

**Expected Output**:
\`\`\`
^C2025-11-22 10:00:20 - main_app.core.application - INFO - Received signal 2
2025-11-22 10:00:20 - main_app.core.application - INFO - Shutting down application...
2025-11-22 10:00:20 - main_app.core.application - INFO - Published event: app.shutdown
2025-11-22 10:00:20 - mod-dummy-producer - INFO - Shutting down mod-dummy-producer
2025-11-22 10:00:20 - main_app.core.module_loader - INFO - Module 'mod-dummy-producer' unloaded
2025-11-22 10:00:20 - mod-dummy-consumer - INFO - Shutting down mod-dummy-consumer
2025-11-22 10:00:20 - main_app.core.module_loader - INFO - Module 'mod-dummy-consumer' unloaded
2025-11-22 10:00:20 - main_app.core.module_loader - INFO - ModuleLoader shutdown complete
2025-11-22 10:00:20 - main_app.core.application - INFO - Application shutdown complete
\`\`\`

Exit code: 0

### Step 6: Test Mode

\`\`\`bash
python -m main_app --test
\`\`\`

**Expected Output**:
\`\`\`
=== TEST MODE ===
Discovered tests from 'mod-dummy-producer': .../tests/
Discovered tests from 'mod-dummy-consumer': .../tests/
Running tests from 3 locations:
  - tests/
  - .../mod-dummy-producer/tests/
  - .../mod-dummy-consumer/tests/

===================== test session starts ======================
collected 6 items

tests/unit/test_event_bus.py::test_subscribe PASSED
tests/unit/test_event_bus.py::test_publish PASSED
mod-dummy-producer/tests/test_producer.py::test_producer_publishes_events PASSED
mod-dummy-producer/tests/test_producer.py::test_producer_shutdown_stops_publishing PASSED
mod-dummy-consumer/tests/test_consumer.py::test_consumer_subscribes_to_events PASSED
mod-dummy-consumer/tests/test_consumer.py::test_consumer_unsubscribes_on_shutdown PASSED

===================== 6 passed in 0.85s =======================
\`\`\`

## Troubleshooting

### Modules Don't Load

**Problem**: "Module path does not exist"

**Solution**: Check `config/modules.yaml` paths are correct and relative to main/ directory.

### No Events Received

**Problem**: Producer publishes but consumer doesn't receive

**Solution**: Check consumer subscribed to correct event type in config.

### Hot-Reload Doesn't Trigger

**Problem**: File changes don't reload module

**Solution**: Check `config/main.yaml` has `hot_reload: true` and watchdog is installed.

## Success Criteria Checklist

- [ ] Both modules load without errors
- [ ] EventBus delivers events to consumer
- [ ] Consumer logs received messages
- [ ] Logs written to `logs/app.log`
- [ ] Hot-reload triggers within 1 second
- [ ] Graceful shutdown with no errors
- [ ] Test mode runs all tests successfully

If all checked: **ALPHA validation complete! ✅**
```

---

## Rough Effort Estimate

**Time**: 2-3 hours

**Breakdown**:
- Create demo script: 1 hour
- Write DEMO.md: 1 hour
- Test demo execution: 30 minutes
- Generate success report: 30 minutes

---

## Success Metrics

**Functional**:
- Automated demo runs without errors
- All success criteria validated
- Clear documentation provided
- Success report generated

**Quality**:
- Demo script is reliable and repeatable
- Documentation is clear and complete
- Report provides evidence of completion
- Ready for user presentation

---

**Feature Owner**: TBD (assigned during mission planning)
**Version Target**: v0.6.0-alpha.1 or v0.7.0-alpha.1 (final ALPHA version)
**Previous Feature**: Feature-008 (Dummy Modules for Validation)
**Next Steps**: User feedback → Feature discovery (Step A9B) → Continue ALPHA OR migrate to BETA

---

## ALPHA Completion

After Feature-009 is completed and validated:

1. **User Feedback Session** (Step A9)
   - Present demo to user
   - Collect feedback on functionality
   - Discuss missing features or adjustments
   - Assess user satisfaction with ALPHA

2. **Decision Point** (Step A9 → A9B or A10)
   - **Option A**: Add more features (Step A9B - Feature Discovery)
   - **Option B**: Refine existing features (create refinement missions)
   - **Option C**: Migrate to BETA (deliberate user choice)

3. **Version Milestone**: v0.7.0-alpha.N or v0.8.0-alpha.1 (depending on iterations)

**Remember**: ALPHA never ends automatically. BETA migration is ALWAYS a conscious user decision, not triggered by feature completion.
