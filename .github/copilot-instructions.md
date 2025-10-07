# es_client Copilot Instructions

## Architecture Overview
This is an Elasticsearch client builder library that provides schema-validated configuration management and connection building. The core architecture centers on the `Builder` class in `src/es_client/builder.py`, which orchestrates:

- Configuration validation via `SchemaCheck` (voluptuous schemas)
- Secure credential storage via `SecretStore` (Fernet encryption)
- URL schema validation and normalization
- Version checking and master-only connections
- Integration with elasticsearch8 client

## Key Components
- **`Builder`**: Main class for constructing validated Elasticsearch clients
- **`utils.py`**: Core utilities including `verify_url_schema()`, `check_config()`, `password_filter()`
- **`schemacheck.py`**: Configuration validation with `SchemaCheck` class
- **`debug.py`**: Tiered debugging system with `@begin_end` decorator
- **`defaults.py`**: Configuration schemas and default values

## Critical Patterns

### Function Tracing
Always use `@begin_end()` decorator on new functions:
```python
@begin_end()
def my_function(param: str) -> str:
    debug.lv3(f'Processing param: {param}')
    # ... function logic ...
    debug.lv5(f'Return value = "{retval}"')
    return retval
```

### Debug Logging Levels
- `debug.lv1()`: High-level flow (rarely used)
- `debug.lv2()`: Function entry/exit (BEGIN/END messages)
- `debug.lv3()`: Important state changes and exceptions
- `debug.lv4()`: TRY blocks and external calls
- `debug.lv5()`: Return values and detailed state

### URL Validation
URLs must be http/https only. Use `verify_url_schema()` which:
- Rejects non-http/https schemes (ftp, etc.)
- Adds default ports (80 for http, 443 for https)
- Returns normalized format: `scheme:host:port`

### Configuration Validation
All configurations go through `SchemaCheck` with voluptuous schemas from `defaults.config_schema()`. Sensitive fields are automatically redacted in logs via `password_filter()`.

### Error Handling
Raise `ConfigurationError` for validation failures, `ESClientException` for connection issues, `NotMaster` for master-only violations.

## CLI Development
Use `@cfg.options_from_dict(OPTION_DEFAULTS)` decorator for consistent CLI options. Commands defined in `commands.py` with extensive option wrapping.

## Testing
- Unit tests in `tests/unit/`, integration in `tests/integration/`
- Use `pytest` with coverage reporting
- Mock elasticsearch8 client for unit tests
- Test both success and failure paths

## Security
- Sensitive fields encrypted in `SecretStore` using Fernet
- Passwords/API keys redacted in logs via `KEYS_TO_REDACT`
- SSL certificate paths validated for readability

## Development Workflow
```bash
# Run tests
hatch run test:run

# Lint and type check
hatch run lint:run
mypy src/

# Build
hatch build
```

## File Structure Reference
- `src/es_client/builder.py`: Core Builder class and SecretStore
- `src/es_client/utils.py`: Utility functions (URL validation, config checking)
- `src/es_client/defaults.py`: Schemas, defaults, and configuration constants
- `src/es_client/schemacheck.py`: SchemaCheck validation class
- `tests/unit/test_helpers_utils.py`: Example of comprehensive unit testing