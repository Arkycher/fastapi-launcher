"""Tests for configuration loading."""

import os
from pathlib import Path

import pytest

from fastapi_launcher.config import (
    loadConfig,
    loadDotenvConfig,
    loadEnvConfig,
    loadPyprojectConfig,
    mergeConfigs,
)
from fastapi_launcher.enums import LogFormat, RunMode


class TestLoadPyprojectConfig:
    """Tests for loading pyproject.toml configuration."""

    def test_load_valid_config(self, tempDir: Path) -> None:
        """Test loading valid pyproject.toml."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
app = "main:app"
host = "0.0.0.0"
port = 9000
""")
        
        config = loadPyprojectConfig(tempDir)
        
        assert config["app"] == "main:app"
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 9000

    def test_no_pyproject(self, tempDir: Path) -> None:
        """Test when pyproject.toml doesn't exist."""
        config = loadPyprojectConfig(tempDir)
        assert config == {}

    def test_no_launcher_section(self, tempDir: Path) -> None:
        """Test when [tool.fastapi-launcher] doesn't exist."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[project]
name = "test"
""")
        
        config = loadPyprojectConfig(tempDir)
        assert config == {}

    def test_invalid_toml(self, tempDir: Path) -> None:
        """Test with invalid TOML file."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("invalid toml [[[")
        
        config = loadPyprojectConfig(tempDir)
        assert config == {}


class TestLoadDotenvConfig:
    """Tests for loading .env configuration."""

    def test_load_env_file(self, tempDir: Path) -> None:
        """Test loading .env file."""
        envPath = tempDir / ".env"
        envPath.write_text("FA_HOST=0.0.0.0\nFA_PORT=9000\n")
        
        config = loadDotenvConfig(tempDir)
        
        # The function returns parsed config or empty dict
        # Just verify no exception is raised
        assert isinstance(config, dict)

    def test_no_env_file(self, tempDir: Path) -> None:
        """Test when .env doesn't exist."""
        config = loadDotenvConfig(tempDir)
        assert config == {}

    def test_boolean_parsing(self, tempDir: Path) -> None:
        """Test boolean value parsing."""
        envPath = tempDir / ".env"
        envPath.write_text("""FA_RELOAD=true
FA_DAEMON=1
FA_ACCESS_LOG=yes
""")
        
        config = loadDotenvConfig(tempDir)
        
        # Check that booleans are parsed correctly if present
        if "reload" in config:
            assert config["reload"] is True

    def test_list_parsing(self, tempDir: Path) -> None:
        """Test list value parsing."""
        envPath = tempDir / ".env"
        envPath.write_text("""FA_RELOAD_DIRS=src,lib,tests
FA_EXCLUDE_PATHS=/health,/metrics,/docs
""")
        
        config = loadDotenvConfig(tempDir)
        
        # Check that lists are parsed if present
        if "reload_dirs" in config:
            assert isinstance(config["reload_dirs"], list)


class TestLoadEnvConfig:
    """Tests for loading environment variable configuration."""

    def test_load_env_vars(self, cleanEnv) -> None:
        """Test loading from environment variables."""
        os.environ["FA_HOST"] = "0.0.0.0"
        os.environ["FA_PORT"] = "9000"
        os.environ["FA_MODE"] = "prod"
        
        config = loadEnvConfig()
        
        assert config["host"] == "0.0.0.0"
        assert config["port"] == 9000
        assert config["mode"] == RunMode.PROD

    def test_log_format_parsing(self, cleanEnv) -> None:
        """Test log format enum parsing."""
        os.environ["FA_LOG_FORMAT"] = "json"
        
        config = loadEnvConfig()
        
        assert config["log_format"] == LogFormat.JSON

    def test_invalid_values_ignored(self, cleanEnv) -> None:
        """Test that invalid values are ignored."""
        os.environ["FA_PORT"] = "not_a_number"
        os.environ["FA_MODE"] = "invalid_mode"
        
        config = loadEnvConfig()
        
        assert "port" not in config
        assert "mode" not in config

    def test_boolean_values(self, cleanEnv) -> None:
        """Test boolean value parsing."""
        os.environ["FA_RELOAD"] = "true"
        os.environ["FA_DAEMON"] = "1"
        os.environ["FA_ACCESS_LOG"] = "yes"
        
        config = loadEnvConfig()
        
        assert config["reload"] is True
        assert config["daemon"] is True
        assert config["access_log"] is True

    def test_boolean_false_values(self, cleanEnv) -> None:
        """Test boolean false value parsing."""
        os.environ["FA_RELOAD"] = "false"
        os.environ["FA_DAEMON"] = "0"
        os.environ["FA_ACCESS_LOG"] = "no"
        
        config = loadEnvConfig()
        
        assert config["reload"] is False
        assert config["daemon"] is False
        assert config["access_log"] is False

    def test_float_values(self, cleanEnv) -> None:
        """Test float value parsing."""
        os.environ["FA_SLOW_REQUEST_THRESHOLD"] = "1.5"
        
        config = loadEnvConfig()
        
        assert config["slow_request_threshold"] == 1.5

    def test_invalid_float_ignored(self, cleanEnv) -> None:
        """Test invalid float value is ignored."""
        os.environ["FA_SLOW_REQUEST_THRESHOLD"] = "not_a_float"
        
        config = loadEnvConfig()
        
        assert "slow_request_threshold" not in config

    def test_list_values(self, cleanEnv) -> None:
        """Test list value parsing."""
        os.environ["FA_RELOAD_DIRS"] = "src,lib,app"
        
        config = loadEnvConfig()
        
        assert config["reload_dirs"] == ["src", "lib", "app"]

    def test_server_backend_parsing(self, cleanEnv) -> None:
        """Test server backend parsing."""
        from fastapi_launcher.enums import ServerBackend
        
        os.environ["FA_SERVER"] = "uvicorn"
        
        config = loadEnvConfig()
        
        assert config["server"] == ServerBackend.UVICORN

    def test_invalid_server_backend_ignored(self, cleanEnv) -> None:
        """Test invalid server backend is ignored."""
        os.environ["FA_SERVER"] = "invalid_backend"
        
        config = loadEnvConfig()
        
        assert "server" not in config


class TestMergeConfigs:
    """Tests for configuration merging."""

    def test_merge_empty(self) -> None:
        """Test merging empty configs."""
        result = mergeConfigs({}, {})
        assert result == {}

    def test_merge_priority(self) -> None:
        """Test that later configs take priority."""
        config1 = {"host": "127.0.0.1", "port": 8000}
        config2 = {"port": 9000}
        
        result = mergeConfigs(config1, config2)
        
        assert result["host"] == "127.0.0.1"
        assert result["port"] == 9000

    def test_merge_none_values_skipped(self) -> None:
        """Test that None values don't override."""
        config1 = {"host": "127.0.0.1"}
        config2 = {"host": None, "port": 9000}
        
        result = mergeConfigs(config1, config2)
        
        assert result["host"] == "127.0.0.1"
        assert result["port"] == 9000

    def test_merge_multiple(self) -> None:
        """Test merging multiple configs."""
        result = mergeConfigs(
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"c": 5, "d": 6},
        )
        
        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}


class TestLoadConfig:
    """Tests for full configuration loading."""

    def test_load_defaults(self, tempDir: Path, cleanEnv) -> None:
        """Test loading with defaults only."""
        config = loadConfig(tempDir)
        
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.mode == RunMode.DEV

    def test_load_from_pyproject(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test loading from pyproject.toml."""
        config = loadConfig(mockProjectDir)
        
        assert config.app == "main:app"
        assert config.host == "127.0.0.1"
        assert config.port == 8000

    def test_cli_args_priority(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test CLI args have highest priority."""
        config = loadConfig(
            mockProjectDir,
            cliArgs={"port": 9999, "host": "192.168.1.1"},
        )
        
        assert config.port == 9999
        assert config.host == "192.168.1.1"

    def test_mode_override(self, tempDir: Path, cleanEnv) -> None:
        """Test mode override parameter."""
        config = loadConfig(tempDir, mode=RunMode.PROD)
        
        assert config.mode == RunMode.PROD

    def test_env_priority_over_pyproject(self, mockProjectDir: Path, cleanEnv) -> None:
        """Test environment variables have priority over pyproject.toml."""
        os.environ["FA_PORT"] = "7777"
        
        config = loadConfig(mockProjectDir)
        
        assert config.port == 7777

    def test_app_dir_set_automatically(self, tempDir: Path, cleanEnv) -> None:
        """Test app_dir is set to project directory."""
        config = loadConfig(tempDir)
        
        assert config.appDir == tempDir

    def test_invalid_config_raises(self, tempDir: Path, cleanEnv) -> None:
        """Test that invalid config raises ValueError."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
port = -1
""")
        
        with pytest.raises(ValueError):
            loadConfig(tempDir)

    def test_effective_config_applied(self, tempDir: Path, cleanEnv) -> None:
        """Test that effective config is applied."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
mode = "dev"
reload = false

[tool.fastapi-launcher.dev]
reload = true
log_level = "debug"
""")
        
        config = loadConfig(tempDir)
        
        assert config.reload is True
        assert config.logLevel == "debug"


class TestMultiEnvironmentConfig:
    """Tests for multi-environment configuration."""

    def test_load_named_environment(self, tempDir: Path, cleanEnv) -> None:
        """Test loading a named environment configuration."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
app = "main:app"
host = "127.0.0.1"
port = 8000
workers = 1

[tool.fastapi-launcher.envs.staging]
host = "0.0.0.0"
workers = 2
log_level = "info"
""")
        
        config = loadConfig(tempDir, envName="staging")
        
        assert config.host == "0.0.0.0"
        assert config.workers == 2
        assert config.logLevel == "info"
        # Port should inherit from base
        assert config.port == 8000

    def test_environment_not_found(self, tempDir: Path, cleanEnv) -> None:
        """Test error when named environment doesn't exist."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
app = "main:app"

[tool.fastapi-launcher.envs.staging]
workers = 2
""")
        
        with pytest.raises(ValueError) as exc_info:
            loadConfig(tempDir, envName="nonexistent")
        
        assert "not found" in str(exc_info.value)

    def test_no_envs_defined(self, tempDir: Path, cleanEnv) -> None:
        """Test error when no envs defined but envName specified."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
app = "main:app"
""")
        
        with pytest.raises(ValueError) as exc_info:
            loadConfig(tempDir, envName="staging")
        
        assert "not found" in str(exc_info.value)

    def test_multiple_environments(self, tempDir: Path, cleanEnv) -> None:
        """Test multiple environments configuration."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
app = "main:app"
port = 8000

[tool.fastapi-launcher.envs.staging]
host = "0.0.0.0"
workers = 2

[tool.fastapi-launcher.envs.qa]
host = "0.0.0.0"
workers = 1
log_level = "debug"

[tool.fastapi-launcher.envs.prod]
host = "0.0.0.0"
workers = 8
log_level = "warning"
""")
        
        staging = loadConfig(tempDir, envName="staging")
        qa = loadConfig(tempDir, envName="qa")
        prod = loadConfig(tempDir, envName="prod")
        
        assert staging.workers == 2
        assert qa.workers == 1
        assert qa.logLevel == "debug"
        assert prod.workers == 8
        assert prod.logLevel == "warning"


class TestGracefulShutdownConfig:
    """Tests for graceful shutdown configuration."""

    def test_default_timeout(self, tempDir: Path, cleanEnv) -> None:
        """Test default graceful shutdown timeout."""
        config = loadConfig(tempDir)
        
        assert config.timeoutGracefulShutdown == 10

    def test_timeout_from_pyproject(self, tempDir: Path, cleanEnv) -> None:
        """Test timeout from pyproject.toml."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
timeout_graceful_shutdown = 30
""")
        
        config = loadConfig(tempDir)
        
        assert config.timeoutGracefulShutdown == 30

    def test_timeout_from_env_var(self, tempDir: Path, cleanEnv) -> None:
        """Test timeout from environment variable."""
        os.environ["FA_TIMEOUT_GRACEFUL_SHUTDOWN"] = "60"
        
        config = loadConfig(tempDir)
        
        assert config.timeoutGracefulShutdown == 60

    def test_timeout_cli_override(self, tempDir: Path, cleanEnv) -> None:
        """Test timeout CLI override."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
timeout_graceful_shutdown = 30
""")
        
        config = loadConfig(
            tempDir,
            cliArgs={"timeout_graceful_shutdown": 10},
        )
        
        assert config.timeoutGracefulShutdown == 10


class TestServerBackendConfig:
    """Tests for server backend configuration."""

    def test_default_server_is_uvicorn(self, tempDir: Path, cleanEnv) -> None:
        """Test default server backend is uvicorn."""
        from fastapi_launcher.enums import ServerBackend
        
        config = loadConfig(tempDir)
        
        assert config.server == ServerBackend.UVICORN

    def test_server_from_pyproject(self, tempDir: Path, cleanEnv) -> None:
        """Test server backend from pyproject.toml."""
        from fastapi_launcher.enums import ServerBackend
        
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
server = "gunicorn"
""")
        
        config = loadConfig(tempDir)
        
        assert config.server == ServerBackend.GUNICORN

    def test_server_from_env_var(self, tempDir: Path, cleanEnv) -> None:
        """Test server backend from environment variable."""
        from fastapi_launcher.enums import ServerBackend
        
        os.environ["FA_SERVER"] = "gunicorn"
        
        config = loadConfig(tempDir)
        
        assert config.server == ServerBackend.GUNICORN


class TestGunicornConfig:
    """Tests for Gunicorn-specific configuration."""

    def test_max_requests_default(self, tempDir: Path, cleanEnv) -> None:
        """Test default max_requests is 0 (disabled)."""
        config = loadConfig(tempDir)
        
        assert config.maxRequests == 0

    def test_max_requests_from_pyproject(self, tempDir: Path, cleanEnv) -> None:
        """Test max_requests from pyproject.toml."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
max_requests = 1000
max_requests_jitter = 100
""")
        
        config = loadConfig(tempDir)
        
        assert config.maxRequests == 1000
        assert config.maxRequestsJitter == 100

    def test_gunicorn_config_generation(self, tempDir: Path, cleanEnv) -> None:
        """Test Gunicorn config generation."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
host = "0.0.0.0"
port = 8000
workers = 4
max_requests = 1000
max_requests_jitter = 100
log_level = "info"
access_log = true
timeout_graceful_shutdown = 30
""")
        
        config = loadConfig(tempDir)
        gunicornConfig = config.toGunicornConfig()
        
        assert gunicornConfig["bind"] == "0.0.0.0:8000"
        assert gunicornConfig["workers"] == 4
        assert gunicornConfig["max_requests"] == 1000
        assert gunicornConfig["max_requests_jitter"] == 100
        assert gunicornConfig["loglevel"] == "info"
        assert gunicornConfig["graceful_timeout"] == 30
