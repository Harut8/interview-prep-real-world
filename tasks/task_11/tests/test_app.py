import pytest
from pydantic import ValidationError
from app import AppConfig, DatabaseConfig, load_config, merge_configs


def test_default_config():
    config = AppConfig()
    assert config.database.host == "localhost"
    assert config.database.port == 5432


# FAILS — fix port validation
def test_negative_port_rejected():
    with pytest.raises(ValidationError):
        DatabaseConfig(port=-1)


# FAILS — fix to reject unknown keys
def test_unknown_keys_raise_error():
    with pytest.raises(ValidationError):
        AppConfig(unknown_field="value")


# FAILS — fix deep merge
def test_merge_configs_deep():
    base = {"database": {"host": "localhost", "port": 5432}}
    override = {"database": {"host": "remote"}}
    result = merge_configs(base, override)
    # Should deep-merge: port should still be present
    assert result["database"]["host"] == "remote"
    assert result["database"]["port"] == 5432


# FAILS — fix secret exposure
def test_password_not_in_repr():
    config = DatabaseConfig(password="supersecret")
    repr_str = repr(config)
    assert "supersecret" not in repr_str


# TODO: Add tests for environment variable override
# TODO: Add tests for cross-field validation (ssl + ssl_cert_path)
# TODO: Add tests for YAML loading
