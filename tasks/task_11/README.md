# Task 11: Config Manager with Pydantic — Fix Validation & Add Environment Override

**Time limit: 60 minutes**

## Existing Codebase
A configuration management module using Pydantic. Supports loading config from YAML files with validation.

## Problems to Fix
1. The `DatabaseConfig.port` field accepts negative numbers and strings.
2. Loading a YAML file with unknown keys silently ignores them instead of erroring.
3. The `merge_configs` function doesn't deep-merge nested dicts — it overwrites entirely.
4. Secret values (passwords, API keys) are exposed in `__repr__` and logging.

## Features to Implement
1. Add environment variable override: `APP_DATABASE__HOST=newhost` should override `database.host`.
2. Add config validation: a `validate()` method that checks cross-field constraints (e.g., if `ssl=True` then `ssl_cert_path` must be set).
3. Write tests for all validation rules and the merge logic.

## What We Evaluate
- Pydantic model design
- Input validation
- Security (secret handling)
- Configuration patterns
