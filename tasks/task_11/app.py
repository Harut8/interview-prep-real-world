import yaml
from pathlib import Path
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432  # BUG: no validation — accepts negative numbers
    name: str = "mydb"
    user: str = "admin"
    password: str = "secret"  # BUG: exposed in repr/logging
    ssl: bool = False
    ssl_cert_path: str | None = None


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: str = ""  # BUG: also exposed


class AppConfig(BaseModel):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    secret_key: str = "change-me"  # BUG: also exposed

    # BUG: unknown keys in YAML are silently ignored
    class Config:
        extra = "ignore"


def load_config(filepath: str | Path) -> AppConfig:
    """Load configuration from a YAML file."""
    path = Path(filepath)
    if not path.exists():
        return AppConfig()

    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        return AppConfig()

    return AppConfig(**data)


def merge_configs(base: dict, override: dict) -> dict:
    """Deep merge two config dictionaries."""
    result = base.copy()
    for key, value in override.items():
        # BUG: doesn't deep-merge nested dicts — overwrites entirely
        result[key] = value
    return result


def config_to_dict(config: AppConfig) -> dict:
    """Convert config to dictionary for serialization."""
    return config.model_dump()


# TODO: Add environment variable override support
# TODO: Add cross-field validation (ssl requires ssl_cert_path)
