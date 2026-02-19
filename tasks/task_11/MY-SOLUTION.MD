1. Port validation — accepts negative numbers (line 8)
    - fix: `port: int = Field(5432, gt=0, le=65535)`
    - Pydantic v2 already rejects non-numeric strings like "abc"
    - numeric strings like "5432" are coerced to int (fine behavior)

2. Secret values exposed in repr/logging (lines 11, 19, 28)
    - ALL three sensitive fields need `SecretStr`, not just database password:
        - `DatabaseConfig.password: SecretStr`
        - `RedisConfig.password: SecretStr`
        - `AppConfig.secret_key: SecretStr`
    - `SecretStr` masks value in repr/logs as `'**********'`
    - NOTE: `config_to_dict` (line 61) uses `model_dump()` which would serialize
      SecretStr values — need `model_dump(mode="json")` or custom serialization

3. `extra = "forbid"` — reject unknown keys (line 32)
    - change `extra = "ignore"` to `extra = "forbid"`
    - Pydantic v2 style: `model_config = ConfigDict(extra="forbid")`
    - NOTE: `class Config:` is Pydantic v1 style — should use `model_config` for v2
    - must apply to ALL models, not just AppConfig — `DatabaseConfig` and `RedisConfig`
      also need it, otherwise unknown keys in nested configs silently ignored

4. Deep merge — recursive merge with deepcopy
    - current code (line 52) uses `base.copy()` (shallow) and overwrites nested dicts
    - fix:
        ```
        def merge_configs(base, override):
            result = copy.deepcopy(base)
            for key, value in override.items():
                if isinstance(value, dict) and isinstance(result.get(key), dict):
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
            return result
        ```

5. Environment variable override — `BaseSettings` with `env_nested_delimiter`
    - switch `AppConfig` from `BaseModel` to `BaseSettings`
    - configure: `model_config = SettingsConfigDict(env_prefix="APP_", env_nested_delimiter="__")`
    - `APP_DATABASE__HOST=newhost` auto-overrides `database.host`
    - NOTE: Pydantic v2 requires `pydantic-settings` as separate package — check requirements.txt

6. Cross-field validation — ssl requires ssl_cert_path
    - use Pydantic `@model_validator`:
        ```
        @model_validator(mode="after")
        def validate_ssl(self):
            if self.ssl and not self.ssl_cert_path:
                raise ValueError("ssl_cert_path required when ssl=True")
            return self
        ```

7. `load_config` returns default on missing file (line 39)
    - silently succeeds when config file doesn't exist
    - consider raising `FileNotFoundError` instead, or at least logging a warning

8. YAML safe_load type safety (line 42)
    - `yaml.safe_load` can return strings, lists, None — not just dicts
    - `AppConfig(**data)` crashes if data is a list
    - fix: validate `isinstance(data, dict)` before passing to AppConfig

9. Tests to write
    - negative port rejected with ValidationError
    - port > 65535 rejected
    - unknown keys raise ValidationError (on AppConfig AND nested configs)
    - password not in repr for all three SecretStr fields
    - `config_to_dict` doesn't expose secrets
    - deep merge: nested override keeps unrelated keys
    - deep merge: non-dict override replaces entirely
    - env var override: `APP_DATABASE__HOST` overrides database.host
    - cross-field: ssl=True without ssl_cert_path raises ValidationError
    - cross-field: ssl=True with ssl_cert_path passes
    - load missing YAML file: returns default or raises (per chosen behavior)
    - load YAML with non-dict content: handled gracefully