# Refinement-001: Fix Consumer Module Loading Timing Issue

**Status**: 🔄 refining
**Type**: Bug Fix
**Priority**: P1 (High - affects automated demo)
**Complexity**: Medium
**GitHub Issue**: TBD (will create during mission planning)

---

## Problem Description

During automated demo execution, the `mod-dummy-consumer` module starts loading but doesn't complete initialization before the demo script times out. The logs show:
- Producer loads successfully and starts publishing events
- Consumer loading starts (watchdog observer setup)
- Consumer initialization never completes
- No consumer subscription logs appear
- No "Received event" logs appear

**Impact**:
- Automated demo can't validate end-to-end EventBus communication
- Manual testing shows consumer works fine with longer wait times
- ALPHA tolerance applied but should be fixed for reliability

**Root Cause**: Unknown - possibly:
- Module import blocking on file watcher initialization
- Race condition between modules loading
- Deadlock in module initialization sequence
- Thread synchronization issue

---

## Objectives

1. **Investigate Consumer Loading**
   - Add detailed logging to module_loader.py during consumer load
   - Measure initialization time for each module
   - Identify bottleneck or blocking operation
   - Check for deadlocks or race conditions

2. **Fix Loading Issue**
   - Ensure consumer initializes within 3-5 seconds
   - Make module loading non-blocking if possible
   - Fix any race conditions or deadlocks
   - Ensure consistent load order

3. **Validate Fix**
   - Run automated demo and verify consumer receives events
   - Check logs show "Subscribed to event: test.ping"
   - Check logs show "Received event:" within 10 seconds
   - Ensure all modules load reliably

4. **Update Demo Script**
   - Remove ALPHA tolerance workaround
   - Require consumer to receive events for pass
   - Update validation criteria

---

## Expected Outcomes

**Files Modified**:
- `src/main_app/core/module_loader.py` - add logging, fix blocking
- `modules-backend/mod-dummy-consumer/__init__.py` - optimize if needed
- `demo.py` - remove tolerance workaround, stricter validation

**Functionality Delivered**:
- Consumer loads and initializes within 5 seconds
- Consumer successfully receives events from producer
- Automated demo validates end-to-end communication
- Reliable module loading sequence

---

## Acceptance Criteria

**Must Have**:
1. Consumer module completes initialization within 5 seconds
2. Consumer logs show "Subscribed to event: test.ping"
3. Consumer logs show "Received event:" within 10 seconds of startup
4. Automated demo passes without tolerance workarounds
5. All 3 modules (test-module, producer, consumer) load successfully
6. No deadlocks or race conditions during loading
7. Module loading order is deterministic and consistent
8. Detailed logging shows initialization timeline

**Nice to Have**:
- Performance metrics for module loading times
- Async module loading if beneficial
- Progress indicators during loading

---

## Investigation Plan

**Step 1: Add Detailed Logging**
```python
# In module_loader.py
logger.info(f"[TIMING] Starting load for module '{name}'")
start_time = time.time()
# ... loading code ...
elapsed = time.time() - start_time
logger.info(f"[TIMING] Module '{name}' loaded in {elapsed:.3f}s")
```

**Step 2: Check for Blocking Operations**
- Review watchdog observer setup in module_loader.py
- Check if file observer blocks on consumer path
- Look for synchronous operations that should be async
- Identify any locks or waits

**Step 3: Test with Different Configurations**
- Disable hot-reload to see if watchdog is the issue
- Load consumer first, then producer
- Load modules sequentially vs in current order
- Measure timing for each scenario

**Step 4: Review Consumer Code**
- Check __init__.py for blocking operations
- Review subscription logic
- Look for module-level imports that might be slow

---

## Validation Approach

**Manual Testing**:
1. Run application with detailed logging enabled
2. Observe consumer initialization timeline
3. Verify consumer receives events
4. Check for any errors or warnings

**Automated Testing**:
1. Run demo.py and verify ALL checks pass
2. Consumer should receive events during demo
3. No tolerance workarounds needed
4. Exit code 0 from demo script

**Success Criteria**:
```
[OK] Producer module loaded
[OK] Consumer module loaded
[OK] Producer publishing events
[OK] Consumer receiving events  # <- This must pass
```

---

## Rough Effort Estimate

**Time**: 2-3 hours

**Breakdown**:
- Investigation and logging: 1 hour
- Fix implementation: 1 hour
- Testing and validation: 1 hour

---

## Notes

**Known Facts**:
- Consumer code is simple and doesn't block (verified by manual import test)
- Producer loads and works perfectly
- Issue appears during automated demo with subprocess
- Manual testing with longer wait times shows consumer works

**Hypothesis**:
The issue is likely in module_loader.py's hot-reload setup or initialization sequence, not in the consumer module itself.

**ALPHA Context**:
This was tolerated in ALPHA with documented workaround. Now we're polishing to make the system more reliable and the demo more convincing.

---

**Version Target**: v0.10.0-alpha.2 or v0.11.0-alpha.1 (depending on scope)
**Previous Version**: v0.10.0-alpha.1 (FINAL ALPHA with tolerance)
**Next Refinement**: Refinement-002 (Exit code fix)
