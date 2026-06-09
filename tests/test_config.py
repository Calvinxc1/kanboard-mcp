import pytest

from kanboard_mcp.config import (
    Config,
    KanboardConfig,
    MCPServerConfig,
    get_example_env,
    load_config,
)


def test_kanboard_url_is_normalized_to_jsonrpc_endpoint():
    config = KanboardConfig(url="https://kanboard.example.test", password="token")

    assert config.url == "https://kanboard.example.test/jsonrpc.php"


def test_kanboard_url_requires_http_scheme():
    with pytest.raises(ValueError, match="URL must start"):
        KanboardConfig(url="kanboard.example.test", password="token")


def test_server_retry_validation_rejects_negative_values():
    with pytest.raises(ValueError, match="Max retries must be non-negative"):
        MCPServerConfig(max_retries=-1)


def test_config_from_env_reads_expected_values(monkeypatch):
    monkeypatch.setenv("KANBOARD_URL", "https://kanboard.example.test")
    monkeypatch.setenv("KANBOARD_API_TOKEN", "token")
    monkeypatch.setenv("KANBOARD_USERNAME", "api")
    monkeypatch.setenv("KANBOARD_VERIFY_SSL", "false")
    monkeypatch.setenv("KANBOARD_MAX_RETRIES", "5")
    monkeypatch.setenv("KANBOARD_TOOL_PROFILE", "core")
    monkeypatch.setenv("KANBOARD_ENABLED_TOOL_MODULES", "tasks, comments")

    config = Config.from_env()

    assert config.kanboard.url == "https://kanboard.example.test/jsonrpc.php"
    assert config.kanboard.username == "api"
    assert config.kanboard.password == "token"
    assert config.kanboard.verify_ssl is False
    assert config.server.max_retries == 5
    assert config.server.tool_profile == "core"
    assert config.server.enabled_tool_modules == ("tasks", "comments")


def test_config_defaults_to_core_tool_profile(monkeypatch):
    monkeypatch.setenv("KANBOARD_URL", "https://kanboard.example.test")
    monkeypatch.setenv("KANBOARD_API_TOKEN", "token")
    monkeypatch.delenv("KANBOARD_TOOL_PROFILE", raising=False)

    config = Config.from_env()

    assert config.server.tool_profile == "core"


def test_load_config_wraps_missing_required_env(monkeypatch):
    monkeypatch.delenv("KANBOARD_URL", raising=False)
    monkeypatch.delenv("KANBOARD_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="Configuration error"):
        load_config()


def test_config_from_env_rejects_invalid_numeric_values(monkeypatch):
    monkeypatch.setenv("KANBOARD_URL", "https://kanboard.example.test")
    monkeypatch.setenv("KANBOARD_API_TOKEN", "token")
    monkeypatch.setenv("KANBOARD_TIMEOUT", "not-an-int")

    with pytest.raises(ValueError, match="invalid literal"):
        Config.from_env()


def test_config_validation_rejects_bad_timeout_and_retry_delay():
    with pytest.raises(ValueError, match="Timeout must be positive"):
        KanboardConfig(url="https://kanboard.example.test", password="token", timeout=0)

    with pytest.raises(ValueError, match="Retry delay must be non-negative"):
        MCPServerConfig(retry_delay=-1)

    with pytest.raises(ValueError, match="Tool profile must be"):
        MCPServerConfig(tool_profile="minimal")

    with pytest.raises(ValueError, match="Unknown tool module"):
        MCPServerConfig(enabled_tool_modules=("tasks", "widgets"))


def test_get_example_env_contains_required_keys():
    example = get_example_env()

    assert "KANBOARD_URL=" in example
    assert "KANBOARD_API_TOKEN=" in example
    assert "KANBOARD_TOOL_PROFILE=" in example
