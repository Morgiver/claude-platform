# Mission: Fix Consumer Module Loading Timing Issue

**Mission ID**: MISSION-010
**Task Reference**: Refinement-001 (from alpha-tasks/refinement-001.md)
**Priority**: P1 (High - blocks automated demo validation)
**Status**: Active
**Estimated Complexity**: Medium
**Type**: Bug Fix (ALPHA Polish & Refinement)
**Target Version**: v0.10.0-alpha.2

---

## Objective

Fix the consumer module loading timeout issue that prevents end-to-end EventBus communication validation during automated demo execution. The consumer module starts loading but doesn't complete initialization, preventing event reception validation.

**Goal**: Ensure consumer module (`mod-dummy-consumer`) completes initialization within 5 seconds and successfully receives events from producer during automated demo runs.

---

## Context

### Problem Summary
During automated demo execution (`demo.py`), the consumer module exhibits the following behavior:
- Producer loads successfully and publishes events
- Consumer loading starts (watchdog observer setup begins)
- Consumer initialization never completes before demo timeout
- No "Subscribed to event: test.ping" logs appear
- No "Received event:" logs appear
- Manual testing with longer wait times shows consumer works correctly

### Root Cause Analysis
**Primary Hypothesis**: Blocking operation in `module_loader.py` during hot-reload setup
- Watchdog observer initialization may be blocking module import completion
- Possible race condition between module loading and observer setup
- Thread synchronization issue preventing consumer from completing `initialize()`

**Impact**:
- Automated demo cannot validate end-to-end EventBus communication
- ALPHA tolerance workaround applied (demo passes despite consumer not working)
- Reduces confidence in system reliability

### Current Workaround
Demo script (`demo.py`) currently uses ALPHA tolerance:
```python
# ALPHA TOLERANCE: Consumer may not receive events in time
if "Consumer receiving events" not in results:
    print("[TOLERANCE] Consumer didn't receive events (ALPHA known issue)")
```

**This workaround must be removed** after fix.

---

## Specifications

### Input Requirements

**Files to Analyze**:
1. `src/main_app/core/module_loader.py` (270 lines)
   - Focus on: `load_module()`, `_watch_module_file()`, watchdog observer setup
   - Look for: Blocking operations, synchronization issues, race conditions
2. `modules-backend/mod-dummy-consumer/__init__.py`
   - Verify: `initialize()` function doesn't have blocking operations
   - Check: Subscription logic is non-blocking
3. `demo.py`
   - Current validation logic and tolerance workarounds

**Known Constraints**:
- Module loading must remain synchronous for ALPHA (no async refactoring)
- Hot-reload feature must continue to work
- Existing producer and test-module loading must not be affected

---

### Output Deliverables

**Modified Files**:

1. **`src/main_app/core/module_loader.py`**
   - Add detailed timing logs for each module load phase
   - Fix blocking operation in hot-reload observer setup
   - Ensure watchdog observer doesn't block module initialization
   - Add initialization completion confirmation log
   - **Target size**: 320-400 lines (current: 270 lines)

2. **`modules-backend/mod-dummy-consumer/__init__.py`**
   - Verify and optimize if needed (likely minimal changes)
   - Ensure `initialize()` completes quickly
   - Add confirmation log after subscription

3. **`demo.py`**
   - Remove ALPHA tolerance workaround for consumer
   - Make consumer event reception a **required** validation check
   - Update validation criteria to fail if consumer doesn't receive events

**Functionality Delivered**:
- Consumer module loads and initializes within 5 seconds
- Consumer successfully subscribes to events (logs confirm)
- Consumer receives events within 10 seconds (logs confirm)
- Automated demo passes without tolerance workarounds
- All 3 modules (test-module, producer, consumer) load reliably

---

### Acceptance Criteria

**Must Have**:
- [ ] Consumer module completes initialization within 5 seconds
- [ ] Logs show: `"Subscribed to event: test.ping"` from consumer
- [ ] Logs show: `"Received event:"` from consumer within 10 seconds of startup
- [ ] Automated demo passes without ALPHA tolerance workaround
- [ ] All 3 modules (test-module, producer, consumer) load successfully
- [ ] Module loading order is deterministic and consistent
- [ ] Detailed `[TIMING]` logs show initialization timeline for each module
- [ ] No regression: producer and test-module still load correctly
- [ ] Hot-reload functionality still works for all modules

**Nice to Have**:
- [ ] Performance metrics logged for each module load phase
- [ ] Progress indicators during module loading
- [ ] Async module loading exploration (future BETA consideration)

---

## Implementation Constraints

### Code Organization
- **File type**: Core infrastructure (module_loader.py), Demo validation (demo.py)
- **Size limit**: Max 1500 lines per file (ALPHA tolerance)
- **Expected size**: module_loader.py ~350 lines, demo.py ~400 lines
- **Architecture rule**: 1 class = 1 file (maintained)

### Technical Requirements
- **Python 3.11+**: Use modern type hints
- **Logging**: Add `[TIMING]` prefix for timing logs
- **No breaking changes**: Existing module interface must remain unchanged
- **Hot-reload**: Watchdog observer must remain functional
- **Thread safety**: Ensure no race conditions introduced

### Investigation Strategy

**Step 1: Add Detailed Timing Logs**
```python
# In module_loader.py - load_module()
import time

logger.info(f"[TIMING] Starting load for module '{name}'")
start_time = time.time()

# ... existing loading code ...

elapsed = time.time() - start_time
logger.info(f"[TIMING] Module '{name}' loaded in {elapsed:.3f}s")
```

**Step 2: Identify Blocking Operation**
- Review watchdog observer setup in `_watch_module_file()`
- Check if observer.start() or observer.schedule() blocks
- Look for synchronous file I/O or network calls
- Identify any locks or waits

**Step 3: Fix Blocking Issue**
- Move observer setup to non-blocking context if possible
- Ensure observer starts after module initialization completes
- Fix any race conditions in initialization sequence
- Confirm consumer's `initialize()` completes before returning

**Step 4: Validate Fix**
- Run automated demo and verify consumer logs appear
- Check timing logs show consumer loads in < 5 seconds
- Confirm consumer receives events within 10 seconds
- Remove tolerance workaround and verify demo passes

---

## Testing Requirements

### Test Specifications

**Manual Testing**:
1. Run application with detailed logging enabled
2. Observe consumer initialization timeline in logs
3. Verify consumer shows subscription confirmation
4. Verify consumer shows received events
5. Check for any errors or warnings during loading

**Automated Testing**:
1. Run `python demo.py` (automated demo script)
2. Verify ALL validation checks pass:
   - `[OK] Producer module loaded`
   - `[OK] Consumer module loaded`
   - `[OK] Producer publishing events`
   - `[OK] Consumer receiving events` ← Must pass (no tolerance)
3. Demo exit code must be 0
4. No tolerance workarounds triggered

### Validation Method

**Success Indicators**:
```
# In demo output logs:
[TIMING] Starting load for module 'mod-dummy-consumer'
[TIMING] Module 'mod-dummy-consumer' loaded in 2.543s
Subscribed to event: test.ping
Received event: {'type': 'test.ping', 'data': {...}}

# In demo validation:
[OK] Consumer module loaded
[OK] Consumer receiving events
```

**Failure Indicators** (must not appear):
```
[TOLERANCE] Consumer didn't receive events
[TIMEOUT] Module 'mod-dummy-consumer' loading timed out
[ERROR] Consumer module failed to initialize
```

---

## Next Steps

### Upon Completion
1. Update `demo.py` to remove ALPHA tolerance completely
2. Verify automated demo passes 3 consecutive times
3. Document fix in mission report
4. Proceed to Step A8 (Manual Validation & Debug)

### Blocked Tasks
- **Refinement-002**: Exit code fix (can proceed in parallel)
- **Version bump to v0.10.0-alpha.2**: After both refinements complete

---

## Notes

**Known Facts**:
- Consumer code itself is simple and doesn't block (verified by manual testing)
- Issue appears only during automated subprocess demo
- Manual testing with longer wait times works perfectly
- Producer loads and works without issues

**ALPHA Context**:
This is a polish phase bug fix. The system works but needs reliability improvements for convincing demo execution.

**Estimated Effort**: 2-3 hours
- Investigation: 1 hour
- Fix implementation: 1 hour
- Testing: 1 hour

---

**Created**: 2025-11-22
**Workflow**: ALPHA Polish & Refinement
**Previous Mission**: MISSION-009 (Demo Scenario Execution)
**Next Mission**: TBD (likely MISSION-011 for Refinement-002)
