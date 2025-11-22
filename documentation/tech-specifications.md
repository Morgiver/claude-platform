# Technical Specifications - main/ (Orchestrateur Modulaire)

**Project**: main/ - Modular Orchestration Platform
**Version**: ALPHA
**Date**: 2025-11-22
**Session**: 001

---

## Technology Stack

### Primary Technologies

#### Language: Python 3.11+
**Justification**:
- Modern type hints (PEP 604 union syntax: `str | None`)
- Performance improvements over 3.10
- Excellent async/await support for future process isolation
- Rich ecosystem for system monitoring and process management
- Native dataclasses for clean data modeling

#### Core Framework: Standard Library + Selective Dependencies
**Approach**: Minimal dependencies, leverage Python standard library
**Justification**:
- ALPHA phase prioritizes simplicity and rapid iteration
- Standard library provides robust multiprocessing, threading, logging
- Add focused libraries only for specific needs (watchdog, psutil)
- Reduces dependency conflicts and installation complexity

### Supporting Technologies

#### Event Bus: In-Process Pub/Sub (Custom Implementation)
**Technology**: Custom `EventBus` class with threading.Lock
**Justification**:
- ALPHA phase: In-process communication is fastest and simplest
- Thread-safe design allows concurrent module operations
- No external broker (Redis/RabbitMQ) needed for ALPHA
- **BETA Migration Path**: Can swap for multiprocess queue or external broker
- Current implementation: ~109 lines, well-tested pattern

#### Module Discovery: Declarative YAML Configuration
**Technology**: PyYAML + `importlib.util`
**Configuration File**: `config/modules.yaml`
**Justification**:
- Explicit control over loaded modules (no auto-discovery surprises)
- YAML is human-readable and easy to modify
- `importlib.util` allows dynamic module loading without `__import__` hacks
- Hot-reload friendly (watchdog monitors config changes)

#### Hot-Reload: Watchdog File Observer
**Technology**: `watchdog` (v3.0.0+)
**Justification**:
- Standard Python library for cross-platform file monitoring
- Event-driven architecture fits our design
- Minimal overhead when watching module directories
- **ALPHA Note**: Optional feature, can be disabled in production

#### System Monitoring: psutil
**Technology**: `psutil` (v5.9.6+)
**Justification**:
- Cross-platform system resource monitoring (RAM, CPU)
- Auto-calculate process/thread limits based on available resources
- Prevent system overload by monitoring usage in real-time
- Lightweight and battle-tested

#### Error Handling: tenacity + pybreaker
**Technology**:
- `tenacity` (v8.2.3+): Retry with exponential backoff
- `pybreaker` (v1.0.1+): Circuit breaker pattern
**Justification**:
- **tenacity**: Flexible retry decorators, supports async, configurable backoff
- **pybreaker**: Prevents cascade failures, state management (open/closed/half-open)
- Combined strategy for critical operations (external API calls, module loading)

#### Testing Framework: pytest
**Technology**: `pytest` (v7.4.3+) + `pytest-cov` + `pytest-asyncio`
**Justification**:
- Industry standard for Python testing
- Rich plugin ecosystem (coverage, async, fixtures)
- `--test` mode will use pytest discovery and execution
- **ALPHA Constraint**: Manual testing acceptable, automated tests are bonus

#### Code Quality: Ruff + MyPy
**Technology**:
- `ruff` (v0.1.8+): Linting + formatting (replaces Black + Flake8)
- `mypy` (v1.7.1+): Static type checking
**Justification**:
- **Ruff**: 10-100x faster than alternatives, combines linting and formatting
- **MyPy**: Catch type errors before runtime, enforce type hints
- **ALPHA Note**: Type hints preferred but not strictly enforced

#### Logging: Python logging module with RotatingFileHandler
**Technology**: Standard library `logging` + `logging.handlers.RotatingFileHandler`
**Configuration**:
- Level: DEBUG (ALPHA)
- Format: Human-readable timestamps
- Output: Console + rotating files (10MB max, 5 backups)
- Directory: `logs/`
**Justification**:
- No external dependency needed
- Automatic log rotation prevents disk overflow
- Structured format allows future parsing/analysis
- Easy to configure per-module log levels

### Dependencies Summary

**Production Dependencies** (requirements.txt):
```
pyyaml>=6.0.1          # YAML configuration parsing
watchdog>=3.0.0        # Hot-reload file monitoring
psutil>=5.9.6          # System resource monitoring
tenacity>=8.2.3        # Retry strategies
pybreaker>=1.0.1       # Circuit breaker pattern
httpx>=0.25.2          # Async HTTP for webhook notifications
```

**Development Dependencies**:
```
pytest>=7.4.3          # Testing framework
pytest-asyncio>=0.21.1 # Async test support
pytest-cov>=4.1.0      # Coverage reporting
ruff>=0.1.8            # Linting and formatting
mypy>=1.7.1            # Static type checking
types-PyYAML>=6.0.12   # Type stubs for PyYAML
```

---

## Architecture Design

### System Architecture Pattern: Event-Driven Orchestration

**Pattern**: Event-driven architecture with centralized event bus and isolated modules

**Core Principle**: Modules communicate ONLY through events, never direct imports

```
┌─────────────────────────────────────────────────────────────┐
│                     Application (Orchestrator)               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  EventBus   │  │ ModuleLoader │  │ ResourceManager  │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │              │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          │        ┌────────┴────────┐          │
          │        │                 │          │
     ┌────▼────┐  ┌▼─────────┐  ┌──▼──────┐   │
     │ Module  │  │ Module   │  │ Module  │   │
     │    A    │  │    B     │  │    C    │   │
     └─────────┘  └──────────┘  └─────────┘   │
          │             │             │         │
          └─────────────┼─────────────┘         │
                        │                       │
                   (pub/sub events)    (resource limits)
```

**Architecture Layers**:

1. **Orchestration Layer** (main_app/core/)
   - `Application`: Entry point, lifecycle management
   - `EventBus`: Centralized message broker
   - `ModuleLoader`: Dynamic module loading/unloading
   - `ResourceManager`: System resource monitoring

2. **Support Layer** (main_app/logging, error_handling, threading)
   - Logging setup and utilities
   - Error strategies (retry, circuit breaker)
   - Process/thread pool management (future)

3. **Module Layer** (external: ../modules-backend/mod-*)
   - Loaded dynamically via ModuleLoader
   - Communicate via EventBus
   - Implement standard interface (initialize, shutdown, get_tests)

### Component Organization

#### Core Components (main_app/core/)

**EventBus** (`event_bus.py`):
- Thread-safe pub/sub implementation
- Methods: `subscribe()`, `publish()`, `unsubscribe()`, `clear()`
- Isolation: Subscriber errors don't crash publisher
- **File Size**: 109 lines (well within ALPHA limits)

**ModuleLoader** (`module_loader.py`):
- Declarative module loading from YAML config
- Hot-reload via watchdog (optional)
- Lifecycle hooks: `initialize(event_bus, config)`, `shutdown()`
- **File Size**: 270 lines (well within ALPHA limits)

**ResourceManager** (`resource_manager.py`):
- Auto-calculate max processes/threads based on RAM/CPU
- Reserves 25% RAM for system
- Estimates 512MB per process (configurable)
- **File Size**: 172 lines (well within ALPHA limits)

**Application** (`application.py`):
- Main orchestrator class
- Initializes all core components
- Handles graceful shutdown (SIGINT, SIGTERM)
- **File Size**: 125 lines (well within ALPHA limits)

#### Module Interface Contract

**Standard Interface** (all modules must implement):

```python
# Required hooks
def initialize(event_bus: EventBus, config: dict) -> None:
    """
    Called by main/ when module is loaded.

    Args:
        event_bus: Shared EventBus instance for pub/sub
        config: Module-specific configuration from modules.yaml
    """
    pass

def shutdown() -> None:
    """Called by main/ when module is unloaded or app shuts down."""
    pass

# Optional hooks
def get_tests() -> list[str]:
    """
    Return list of test paths for --test mode.

    Returns:
        List of test directory/file paths (e.g., ["tests/"])
    """
    return []
```

**Module Communication Protocol**:
- Modules receive `event_bus` in `initialize()`
- Subscribe to events: `event_bus.subscribe("event.type", callback)`
- Publish events: `event_bus.publish("event.type", data)`
- **No direct imports** between modules allowed

### Data Architecture

#### Configuration Files

**main/config/main.yaml** (Global Configuration):
```yaml
app:
  name: "main-orchestrator"
  version: "0.1.0-alpha.1"

resources:
  process_memory_mb: 512        # Estimated memory per process
  reserved_ram_percent: 0.25    # Reserve 25% RAM for system
  thread_per_core: 2            # Thread multiplier

logging:
  level: "DEBUG"                # ALPHA: verbose logging
  directory: "logs"
  max_file_size_mb: 10
  backup_count: 5

error_handling:
  retry_max_attempts: 3
  retry_wait_min: 1.0
  retry_wait_max: 10.0
  circuit_breaker_fail_max: 5
  circuit_breaker_reset_timeout: 60
```

**main/config/modules.yaml** (Module Declaration):
```yaml
modules:
  - name: "mod-dummy-producer"
    path: "../modules-backend/mod-dummy-producer/__init__.py"
    enabled: true
    config:
      publish_interval: 5
      event_type: "test.ping"

  - name: "mod-dummy-consumer"
    path: "../modules-backend/mod-dummy-consumer/__init__.py"
    enabled: true
    config:
      subscribe_events: ["test.ping"]
```

**Secrets Management**:
- Environment variables via `.env` file (python-dotenv)
- **NEVER** commit secrets to YAML files
- Config files reference env vars: `api_key: ${WEBHOOK_API_KEY}`

#### Event Protocol

**Event Structure**:
```python
event_type: str          # Namespaced event name (e.g., "module.loaded")
data: Any | None         # Event payload (dict, list, primitive, or None)
```

**Event Naming Convention**:
- Format: `<namespace>.<action>`
- Examples:
  - `app.started`, `app.shutdown`
  - `module.loaded`, `module.unloaded`, `module.error`
  - `test.ping`, `data.received`, `task.completed`

**Built-in Events** (published by main/):
- `app.started` - Application initialized (data: `{"resources": SystemResources}`)
- `app.shutdown` - Application shutting down
- `module.loaded` - Module loaded (data: `{"name": str, "config": dict}`)
- `module.unloaded` - Module unloaded (data: `{"name": str}`)
- `module.error` - Module encountered error (data: `{"name": str, "error": str}`)

### Module Isolation Strategy

**ALPHA Phase**: In-Process Isolation
- Modules loaded in same process as main/
- Error isolation via try/except in EventBus
- Subscriber errors logged but don't crash publisher
- **Trade-off**: Speed and simplicity over robustness

**BETA/PRODUCTION Phase**: Multi-Process Isolation (Future)
- Each module in separate process (multiprocessing.Process)
- EventBus becomes inter-process queue
- Module crashes don't affect main/ or other modules
- Auto-restart crashed modules

---

## Development Constraints

### ALPHA-Specific Constraints

#### File Organization Rules

**1 Class = 1 File** (Preferred, Not Strict):
- ✅ **PREFERRED**: Each class in its own file
  - Example: `EventBus` class → `event_bus.py`
  - Example: `ModuleLoader` class → `module_loader.py`
- ⚠️ **TOLERANCE**: Multiple small classes/dataclasses allowed in one file
  - Example: `ModuleConfig` dataclass in `module_loader.py` (acceptable)
  - Example: Helper functions with main class (acceptable)
- ❌ **AVOID**: Multiple large classes in same file

**File Size Limits**:
- **Max 1500 lines per file** (ALPHA tolerance)
- **Guideline**:
  - Models/Dataclasses: 200-350 lines
  - Services/Loaders: 250-450 lines
  - Complex Logic: 300-600 lines
- **Enforcement**: Warnings at 1000 lines, blocking at 1500+ lines
- **Current Status**: All existing files < 300 lines ✅

**Directory Structure**:
```
main/
├── src/
│   └── main_app/
│       ├── __init__.py
│       ├── __main__.py              # Entry point: python -m main_app
│       ├── core/
│       │   ├── __init__.py
│       │   ├── event_bus.py         # EventBus class
│       │   ├── module_loader.py     # ModuleLoader + ModuleConfig
│       │   ├── resource_manager.py  # ResourceManager + SystemResources
│       │   └── application.py       # Application class + main()
│       ├── logging/
│       │   ├── __init__.py
│       │   └── logger.py            # setup_logging() + get_logger()
│       ├── error_handling/
│       │   ├── __init__.py
│       │   ├── strategies.py        # Retry + circuit breaker decorators
│       │   └── webhook_notifier.py  # Webhook notifications (future)
│       └── threading/
│           ├── __init__.py
│           └── process_pool.py      # Process pool management (future)
├── config/
│   ├── main.yaml                    # Global configuration
│   ├── modules.yaml                 # Module declarations
│   └── logging.yaml                 # Logging configuration (future)
├── logs/                            # Rotating log files
├── tests/                           # Test files (ALPHA: manual testing OK)
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # Project documentation
```

#### Coding Standards

**Type Hints**:
- **ALPHA**: Preferred but not strictly enforced
- Use modern syntax: `str | None` instead of `Optional[str]`
- Annotate function signatures (args and return types)
- Use `dataclasses` for data structures
- Run `mypy` periodically, but don't block on warnings

**Naming Conventions**:
- Files: `snake_case.py` (e.g., `event_bus.py`)
- Classes: `PascalCase` (e.g., `EventBus`, `ModuleLoader`)
- Functions/methods: `snake_case` (e.g., `load_module`, `get_resources`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `PROCESS_MEMORY_MB`)
- Private members: `_leading_underscore` (e.g., `_subscribers`, `_lock`)

**Docstrings**:
- Required for: Classes, public methods, public functions
- Optional for: Private methods, simple getters/setters
- Format: Google-style docstrings
- Example:
  ```python
  def load_module(self, config: ModuleConfig) -> bool:
      """
      Load a module from configuration.

      Args:
          config: Module configuration

      Returns:
          True if module loaded successfully, False otherwise
      """
  ```

**Logging**:
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Levels:
  - `DEBUG`: Detailed flow (ALPHA default)
  - `INFO`: Major lifecycle events (module loaded, app started)
  - `WARNING`: Recoverable issues (module disabled, retry triggered)
  - `ERROR`: Failures with recovery (module load failed, subscriber error)
  - `CRITICAL`: Unrecoverable failures (system resource exhausted)
- Always include context: `logger.error(f"Failed to load '{name}': {e}")`

**Error Handling**:
- **Never** catch `Exception` without logging
- Use specific exception types when possible
- Isolate errors: Module failures shouldn't crash main/
- Log with `exc_info=True` for stack traces
- Use decorators for retry/circuit breaker:
  ```python
  @with_retry(max_attempts=3, exceptions=(ConnectionError,))
  def fetch_data():
      pass
  ```

#### Testing Strategy for ALPHA

**Manual Testing Acceptable**:
- Run application and verify logs
- Test module loading/unloading manually
- Validate event bus with dummy modules
- **No requirement** for 80% coverage in ALPHA

**Automated Tests as Bonus**:
- Write tests for critical paths (EventBus, ModuleLoader)
- Use pytest fixtures for setup/teardown
- Test error scenarios (module load failure, event errors)
- **Coverage Goal**: 40-60% in ALPHA (aspirational)

**Test Mode Implementation** (`--test` flag):
```python
# main_app/__main__.py
if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        # Test mode: Discover and run all module tests
        from .testing.test_runner import run_all_tests
        exit_code = run_all_tests()
        sys.exit(exit_code)
    else:
        # Normal mode: Run application
        from .core.application import main
        main()
```

**Test Discovery**:
- Load all modules from `modules.yaml`
- Call `get_tests()` on each module
- Aggregate test paths
- Run `pytest` with collected paths
- Generate consolidated report

---

## Project Structure

### Standard Directory Layout

```
main/
├── src/main_app/              # Source code
│   ├── core/                  # Core orchestration components
│   ├── logging/               # Logging utilities
│   ├── error_handling/        # Error strategies
│   └── threading/             # Process/thread management
├── config/                    # Configuration files (YAML)
├── logs/                      # Rotating log files (auto-created)
├── tests/                     # Test files (pytest)
├── .env                       # Environment variables (secrets)
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml             # Ruff + MyPy configuration
└── README.md                  # Project documentation
```

### Module Storage Convention

**Modules stored externally** (not in main/):
```
project-root/
├── main/                      # This orchestrator
└── modules-backend/           # All loadable modules
    ├── mod-dummy-producer/
    ├── mod-dummy-consumer/
    ├── mod-agents/
    └── ...
```

**Rationale**:
- Clean separation: main/ is pure infrastructure
- Modules can be developed independently
- Easier version control (separate repos possible)
- Modules can have own dependencies

---

## Integration Requirements

### Module Interface Requirements

**Required Functions**:
- `initialize(event_bus, config)`: Setup module with event bus access
- `shutdown()`: Cleanup before unload

**Optional Functions**:
- `get_tests()`: Return test paths for `--test` mode

**Configuration Access**:
- Modules receive their config from `modules.yaml` via `initialize()`
- Access global config: `config.get("api_key")` (from module-specific section)

### Event Bus Requirements

**Thread Safety**: All EventBus operations must be thread-safe
**Error Isolation**: Subscriber errors must not crash publisher
**Event Ordering**: No guaranteed order for subscribers
**Event Delivery**: Synchronous in ALPHA (async possible in BETA)

### Hot-Reload Requirements (Optional in ALPHA)

**File Monitoring**: Watch module directories for `.py` changes
**Reload Trigger**: File modification triggers `reload_module()`
**State Preservation**: Modules responsible for saving/restoring state
**Limitations**: Cannot reload if module has active event subscriptions (unsubscribe in shutdown)

---

## Performance Requirements

### ALPHA Performance Targets

**Startup Time**:
- Application startup: < 2 seconds
- Module loading (5 modules): < 5 seconds
- **Measurement**: Log timestamps in `app.started` event

**Event Latency**:
- Event publish to subscriber callback: < 10ms
- **Measurement**: Add debug logging for event timing

**Resource Usage**:
- Memory: < 200MB for main/ alone (modules add their own)
- CPU: < 5% idle, < 50% under load
- **Monitoring**: ResourceManager logs usage every 60 seconds

**Module Reload**:
- Hot-reload response time: < 1 second after file save
- **Measurement**: Log time between file event and module reloaded

### Scalability Targets (ALPHA)

**Module Count**: Support 10-20 modules loaded simultaneously
**Event Throughput**: 1000 events/second (in-process pub/sub)
**Concurrent Threads**: Auto-calculated (cpu_count * 2)
**Concurrent Processes**: Auto-calculated (available_ram / 512MB)

**Note**: These are ALPHA targets for validation. BETA will optimize and add process isolation.

---

## Security Considerations

### ALPHA Security Measures

**Secrets Management**:
- ✅ Use environment variables (`.env` file)
- ✅ Never commit secrets to Git (`.gitignore` includes `.env`)
- ❌ No encryption in ALPHA (filesystem protection only)

**Module Trust Model**:
- **ALPHA**: Modules are trusted (loaded from local filesystem)
- **BETA**: Add module signature verification
- **PRODUCTION**: Sandbox modules in separate processes

**File System Access**:
- Modules have full filesystem access (Python imports)
- **Mitigation**: Only load modules from trusted paths
- **Future**: Chroot or containerization in PRODUCTION

**Logging Sensitive Data**:
- Never log API keys, passwords, tokens
- Redact sensitive fields in config logging
- Example: `logger.info(f"Config: {redact_secrets(config)}")`

**Network Access**:
- Modules can make arbitrary HTTP requests
- **ALPHA**: No restrictions (trust model)
- **FUTURE**: Network policies in BETA/PRODUCTION

---

## Quality Assurance Standards

### Code Review Requirements (ALPHA)

**Self-Review Checklist**:
- [ ] Code follows 1-class-per-file guideline
- [ ] File size < 1500 lines
- [ ] Type hints on public functions
- [ ] Docstrings on classes and public methods
- [ ] Error handling with logging
- [ ] No hardcoded secrets
- [ ] Manual testing performed

**Peer Review** (if team > 1):
- One approval required for merge
- Focus on architecture and design patterns
- Don't block on style issues (ruff handles formatting)

### Automated Quality Checks

**Pre-Commit Hooks** (recommended, not required):
```bash
# Format with ruff
ruff format .

# Lint with ruff
ruff check . --fix

# Type check with mypy
mypy src/main_app
```

**CI/CD Pipeline** (future):
- Run tests: `pytest tests/`
- Check coverage: `pytest --cov=main_app --cov-report=term`
- Lint: `ruff check .`
- Type check: `mypy src/main_app`

### Testing Standards (ALPHA Relaxed)

**Required**:
- Manual testing of core features
- Validate event bus with dummy modules
- Test module loading/unloading

**Bonus** (not required):
- Unit tests for EventBus
- Unit tests for ModuleLoader
- Integration tests for Application
- Coverage: 40-60% aspirational

**Test Organization**:
```
tests/
├── unit/
│   ├── test_event_bus.py
│   ├── test_module_loader.py
│   └── test_resource_manager.py
├── integration/
│   └── test_application.py
└── fixtures/
    ├── dummy_module.py
    └── test_config.yaml
```

---

## Migration Path to BETA

### Planned Changes for BETA Transition

**Process Isolation**:
- Migrate modules to separate processes (multiprocessing.Process)
- Implement inter-process EventBus (multiprocessing.Queue or Redis)
- Auto-restart crashed modules

**Testing**:
- Increase coverage to 80%+
- Add integration tests for all module interactions
- Automated CI/CD pipeline

**Performance**:
- Benchmark event latency
- Optimize hot paths (event publishing, module loading)
- Add metrics collection (Prometheus/StatsD)

**Configuration**:
- Migrate to structured config validation (Pydantic)
- Add config schema validation
- Support multiple environments (dev/staging/prod)

**File Size Enforcement**:
- Strict 1000 line limit (down from 1500)
- Blocking violations instead of warnings

---

## Validation of Existing Code

### Code Alignment Assessment

✅ **EventBus** (`event_bus.py`):
- Follows 1-class-per-file: ✅
- File size (109 lines): ✅ Well under limit
- Type hints: ✅ Complete
- Docstrings: ✅ Comprehensive
- Error isolation: ✅ Try/except in publish()
- **Status**: Compliant, no changes needed

✅ **ModuleLoader** (`module_loader.py`):
- Follows 1-class-per-file: ⚠️ Has ModuleConfig dataclass (acceptable in ALPHA)
- File size (270 lines): ✅ Well under limit
- Type hints: ✅ Complete
- Docstrings: ✅ Comprehensive
- Hot-reload: ✅ Implemented with watchdog
- **Status**: Compliant, no changes needed

✅ **ResourceManager** (`resource_manager.py`):
- Follows 1-class-per-file: ⚠️ Has SystemResources dataclass (acceptable in ALPHA)
- File size (172 lines): ✅ Well under limit
- Type hints: ✅ Complete
- Docstrings: ✅ Comprehensive
- Auto-calculation: ✅ Implements reserve + limit logic
- **Status**: Compliant, no changes needed

✅ **Application** (`application.py`):
- Follows 1-class-per-file: ✅
- File size (125 lines): ✅ Well under limit
- Type hints: ⚠️ Missing on `_signal_handler` frame param (minor)
- Docstrings: ✅ Comprehensive
- Graceful shutdown: ✅ SIGINT/SIGTERM handlers
- **Status**: Compliant, minor type hint improvement optional

✅ **Logger** (`logger.py`):
- No classes: ✅ (utility functions)
- File size (87 lines): ✅ Well under limit
- Type hints: ✅ Complete
- Rotating files: ✅ Configured (10MB, 5 backups)
- **Status**: Compliant, no changes needed

✅ **Error Strategies** (`strategies.py`):
- Follows 1-class-per-file: ⚠️ Has decorators + ErrorStrategy class (acceptable)
- File size (168 lines): ✅ Well under limit
- Type hints: ✅ Complete
- Docstrings: ✅ Comprehensive
- **Status**: Compliant, no changes needed

### Required Adjustments

**Minimal Changes Needed**:
1. **Add Configuration Files**:
   - Create `config/main.yaml` (global settings)
   - Create `config/modules.yaml` (module declarations)
   - Add `.env.example` template

2. **Implement Test Mode**:
   - Modify `__main__.py` to detect `--test` flag
   - Create `testing/test_runner.py` for pytest integration
   - Implement module test discovery via `get_tests()`

3. **Integrate Components**:
   - Application currently doesn't load modules (just initializes loader)
   - Add config loading in `Application.__init__()`
   - Call `module_loader.load_modules()` in `Application.start()`

4. **Type Hint Improvement** (optional):
   - Add `Any` type to `_signal_handler` frame parameter

**Everything Else**: Existing code is architecture-compliant and ready for ALPHA development! 🚀

---

## Success Criteria

### ALPHA Success Metrics (v0.1.0 - v0.N.0)

**Functional Requirements**:
- ✅ Load N modules from `modules.yaml`
- ✅ EventBus delivers events between modules
- ✅ Hot-reload responds to file changes (< 1 second)
- ✅ Logs centralized in `logs/` directory
- ✅ ResourceManager calculates limits correctly
- ✅ Graceful shutdown (no orphaned processes)
- ✅ `--test` mode discovers and runs module tests

**Quality Requirements**:
- File sizes < 1500 lines
- Manual testing validates core scenarios
- No critical bugs in core components
- Code follows naming conventions

**Performance Requirements**:
- Startup < 2 seconds
- Module load (5 modules) < 5 seconds
- Event latency < 10ms
- Memory usage < 200MB (main/ alone)

### Demo Scenario (Minimal Validation)

**Setup**:
1. Create 2 dummy modules: `mod-dummy-producer`, `mod-dummy-consumer`
2. Configure in `modules.yaml`

**Execution**:
1. Start main/: `python -m main_app`
2. Producer publishes event: `test.ping` with `{"message": "hello"}`
3. Consumer receives event and logs message

**Success Criteria**:
- Both modules load without errors
- EventBus delivers event to consumer
- Consumer logs: `"Received test.ping: hello"`
- Logs written to `logs/app.log`
- Modify producer file → hot-reload triggers < 1 second
- Ctrl+C → graceful shutdown, no errors

---

## Next Steps

**Immediate Actions** (for Step 3: Task Decomposition):
1. Create `config/main.yaml` and `config/modules.yaml`
2. Implement config loading in Application
3. Create test mode implementation
4. Build 2 dummy modules for validation
5. Manual testing of core scenario
6. Version initialization: v0.1.0-alpha.1

**Future Enhancements** (BETA Scope):
- Process isolation for modules
- Inter-process EventBus
- Automated test coverage > 80%
- Performance benchmarking
- Module auto-restart on crash
- Metrics collection and monitoring

---

**Document Status**: ✅ Complete and Validated
**Workflow Version**: ALPHA
**Next Workflow Step**: Step 3 - Task Decomposition (@task-decomposer)
**Technical Foundation**: Ready for ALPHA development cycle
