# Mission: Demo Scenario Execution & ALPHA Validation

**Mission ID**: MISSION-009
**Feature Reference**: Feature-009 (Demo Scenario Execution)
**Priority**: P4 (Final ALPHA validation - proves complete system works)
**Status**: Active
**Estimated Complexity**: Low
**GitHub Issue**: https://github.com/Morgiver/claude-platform/issues/9

## Objective

Create comprehensive demo script and documentation that validates all ALPHA success criteria from the project brief. This is the final proof that the main/ orchestrator works as intended, demonstrating module loading, EventBus communication, hot-reload, logging, resource management, graceful shutdown, and test mode.

## Context

### Required Knowledge

**All ALPHA Features Completed (001-008)**:
- Feature-001: Configuration System (YAML loading)
- Feature-002: Centralized Logging (rotating file handler)
- Feature-003: Error Handling Integration (retry + circuit breaker)
- Feature-004: Module Loading & Lifecycle Management
- Feature-005: Module Hot-Reload System (watchdog)
- Feature-006: Application Startup & Integration
- Feature-007: Test Mode Implementation (`--test` flag)
- Feature-008: Dummy Modules (producer/consumer validation)

**Demo Validation Points** (from Project Brief):
1. Module loading from `config/modules.yaml` (producer + consumer)
2. EventBus communication (events delivered between modules)
3. Hot-reload functionality (file change → module reload < 1 second)
4. Centralized logging (logs written to `logs/app.log`)
5. Resource management (RAM/CPU limits calculated)
6. Graceful shutdown (Ctrl+C with no errors)
7. Test mode (tests discovered and run from modules)

**Existing Dummy Modules** (Feature-008):
- `mod-dummy-producer`: Publishes `test.ping` events every 5 seconds
- `mod-dummy-consumer`: Receives and logs `test.ping` events
- Both configured in `config/modules.yaml`

### File References

**Configuration Files**:
- `config/main.yaml` - application configuration
- `config/modules.yaml` - module declarations

**Dummy Modules**:
- `../modules-backend/mod-dummy-producer/__init__.py`
- `../modules-backend/mod-dummy-consumer/__init__.py`

**Test Directories**:
- `tests/` - core application tests
- `../modules-backend/mod-dummy-producer/tests/`
- `../modules-backend/mod-dummy-consumer/tests/`

### Dependencies Met

- All Features 001-008 completed and working
- Dummy modules functional and tested
- Complete ALPHA system operational

## Specifications

### Input Requirements

**Demo Script Requirements**:
- Must be cross-platform (Windows compatible)
- Python-based (use `demo.py` instead of bash for Windows compatibility)
- Automated validation of all success criteria
- Generate demo report with pass/fail results
- Capture logs and outputs for evidence

**Documentation Requirements**:
- Step-by-step manual demo instructions
- Expected outputs for each validation step
- Troubleshooting guide for common issues
- Quick-start guide for new users
- Success criteria checklist

### Output Deliverables

**Files to Create**:
1. `demo.py` - Python demo script (~200-250 lines, Windows compatible)
2. `DEMO.md` - Demo documentation with manual instructions (~150 lines)
3. `reports/alpha/alpha-validation-report.md` - Success criteria report (~80 lines)

**Expected Functionality**:
- Automated demo validates all 7 core features
- Demo script creates `demo-output/` directory with logs and reports
- Clear pass/fail feedback for each validation step
- Evidence collected for stakeholder presentation
- Manual demo option with detailed instructions

### Acceptance Criteria

- [ ] `demo.py` created with Python implementation (Windows compatible)
- [ ] Demo validates module loading (producer + consumer load successfully)
- [ ] Demo validates EventBus communication (events published and received)
- [ ] Demo validates hot-reload capability (file change detection - optional test)
- [ ] Demo validates centralized logging (logs written to `logs/app.log`)
- [ ] Demo validates resource management (RAM/CPU limits logged)
- [ ] Demo validates graceful shutdown (Ctrl+C exits cleanly)
- [ ] Demo validates test mode (discovers and runs all module tests)
- [ ] `DEMO.md` provides clear step-by-step manual instructions
- [ ] `DEMO.md` includes expected outputs and troubleshooting guide
- [ ] `reports/alpha/alpha-validation-report.md` generated with success checklist
- [ ] All success criteria from project brief validated and documented

## Implementation Constraints

### Code Organization

**Demo Script Structure** (`demo.py`):
- Use `subprocess` module for running application
- Use `time.sleep()` for waiting between validation steps
- Use `pathlib.Path` for cross-platform file operations
- Capture stdout/stderr for log analysis
- Generate markdown report with validation results
- Size limit: ~250 lines (simple and clear)

**Demo Documentation Structure** (`DEMO.md`):
- Quick Start section (automated demo)
- Manual Demo section (step-by-step with expected outputs)
- Troubleshooting section (common issues and solutions)
- Success Criteria Checklist
- Size: ~150 lines (comprehensive but concise)

**Validation Report Structure** (`reports/alpha/alpha-validation-report.md`):
- Header with date and version
- Success criteria checklist (7 core features)
- Evidence section (log snippets, test results)
- Conclusion with overall status
- Size: ~80 lines

### Technical Requirements

**Demo Script Approach**:
```python
# demo.py - Automated ALPHA demo
import subprocess
import time
import os
from pathlib import Path

def validate_module_loading():
    """Start app and verify modules load"""
    # Start app in background, capture logs
    # Check for "Module 'mod-dummy-producer' loaded successfully"
    # Return True if both modules loaded

def validate_eventbus_communication():
    """Verify events published and received"""
    # Check logs for "Publishing test.ping event"
    # Check logs for "Received event:"
    # Return True if both found

def validate_logging():
    """Verify centralized logging"""
    # Check logs/app.log exists
    # Check file contains application logs
    # Return True if valid

def validate_test_mode():
    """Run test mode and verify"""
    # Run: python -m main_app --test
    # Check exit code == 0
    # Return True if tests passed

def generate_report():
    """Generate markdown report"""
    # Create reports/alpha/alpha-validation-report.md
    # Include all validation results
```

**ALPHA Constraints**:
- Manual hot-reload test is optional (requires interactive file editing)
- Focus on core automated validation
- Evidence-based reporting (log snippets, not just pass/fail)
- Windows-compatible paths and commands

## Testing Requirements

### Test Specifications

**Automated Validation Scenarios**:

1. **Module Loading Validation**
   - Start application: `python -m main_app`
   - Wait 3 seconds for startup
   - Check logs for module load messages
   - Expected: Both modules loaded successfully

2. **EventBus Communication Validation**
   - Wait 7 seconds for event publishing
   - Check logs for producer publish messages
   - Check logs for consumer receive messages
   - Expected: Events published and received

3. **Logging Validation**
   - Check `logs/app.log` file exists
   - Verify file contains application logs
   - Expected: Log file created with content

4. **Graceful Shutdown Validation**
   - Send SIGINT to application process
   - Wait 2 seconds for shutdown
   - Check logs for shutdown messages
   - Expected: Clean shutdown with no errors

5. **Test Mode Validation**
   - Run: `python -m main_app --test`
   - Capture exit code and output
   - Expected: Exit code 0, all tests passed

### Validation Method (Demo Execution)

**Run Automated Demo**:
```bash
python demo.py
```

**Expected Output**:
```
=========================================
main/ ALPHA Demo - Automated Validation
=========================================

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
✅ Log file contains application logs

[6/7] Testing graceful shutdown...
✅ Graceful shutdown successful

[7/7] Running test mode...
✅ Test mode passed (6 tests)

=========================================
✅ DEMO COMPLETE - ALL CHECKS PASSED
=========================================

Validation report: reports/alpha/alpha-validation-report.md
Demo logs: demo-output/app.log
```

**Manual Demo** (documented in DEMO.md):
- Follow step-by-step instructions
- Verify expected outputs manually
- Validate each feature interactively

## Next Steps

### Upon Completion

1. Update `documentation/alpha-tasks/feature-009.md` with completion timestamp
2. Update `documentation/alpha-tasks/index.md` status: 🎯 planned → ✅ completed
3. Archive mission file to `missions/alpha-archived/mission-009.md`
4. Proceed to Step A8 (Manual Validation) - run automated demo and verify all checks pass
5. Proceed to Step A9 (Feedback Checkpoint) - present complete ALPHA system to user
6. Proceed to Step A10 (GitHub Issue Sync) - update issue #9 and close with demo evidence
7. Proceed to Step A11 (Version Bump) - bump to final ALPHA version (v0.10.0-alpha.1 or similar)

### ALPHA Completion Decision

After Feature-009 completion, user will decide:
- **Option A**: Add more features (Step A9B - Feature Discovery Interview)
- **Option B**: Refine existing features (create refinement missions)
- **Option C**: Migrate to BETA (deliberate user choice, NOT automatic)

**Remember**: ALPHA never ends automatically. This is the last planned feature, but BETA migration requires conscious user decision based on satisfaction with prototype and readiness for structured refactoring.

### Evidence Package for Stakeholders

**Deliverables for Presentation**:
- Automated demo script (`demo.py`)
- Demo documentation (`DEMO.md`)
- Validation report (`reports/alpha/alpha-validation-report.md`)
- Demo execution logs (`demo-output/app.log`, `demo-output/test.log`)
- Success criteria checklist (all items checked ✅)
