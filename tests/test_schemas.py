"""Tests for schema models."""

from datetime import datetime
from pathlib import Path

import pytest

from fastapi_launcher.enums import LogFormat, RunMode
from fastapi_launcher.schemas import (
    AccessLogEntry,
    EnvironmentConfig,
    LauncherConfig,
    LogConfig,
    UvicornConfig,
)


class TestUvicornConfig:
    """Tests for UvicornConfig schema."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = UvicornConfig()
        
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.reload is False
        assert config.reloadDirs == []
        assert config.workers == 1
        assert config.logLevel == "info"
        assert config.accessLog is True
        assert config.timeout == 30

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = UvicornConfig(
            host="0.0.0.0",
            port=9000,
            reload=True,
            workers=4,
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.reload is True
        assert config.workers == 4

    def test_port_validation(self) -> None:
        """Test port number validation."""
        # Valid port
        config = UvicornConfig(port=8080)
        assert config.port == 8080
        
        # Invalid port (too low)
        with pytest.raises(ValueError):
            UvicornConfig(port=0)
        
        # Invalid port (too high)
        with pytest.raises(ValueError):
            UvicornConfig(port=70000)

    def test_workers_validation(self) -> None:
        """Test workers validation."""
        # Valid workers
        config = UvicornConfig(workers=8)
        assert config.workers == 8
        
        # Invalid workers
        with pytest.raises(ValueError):
            UvicornConfig(workers=0)

    def test_alias_support(self) -> None:
        """Test alias support for snake_case keys."""
        config = UvicornConfig(
            log_level="debug",
            access_log=False,
            reload_dirs=["src"],
        )
        
        assert config.logLevel == "debug"
        assert config.accessLog is False
        assert config.reloadDirs == ["src"]


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig schema."""

    def test_all_optional(self) -> None:
        """Test that all fields are optional."""
        config = EnvironmentConfig()
        
        assert config.reload is None
        assert config.workers is None
        assert config.logLevel is None
        assert config.logFormat is None

    def test_partial_config(self) -> None:
        """Test partial configuration."""
        config = EnvironmentConfig(reload=True, workers=2)
        
        assert config.reload is True
        assert config.workers == 2
        assert config.logLevel is None


class TestLauncherConfig:
    """Tests for LauncherConfig schema."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = LauncherConfig()
        
        assert config.app is None
        assert config.appDir is None
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.mode == RunMode.DEV
        assert config.reload is False
        assert config.workers == 1
        assert config.daemon is False
        assert config.logLevel == "info"
        assert config.logFormat == LogFormat.PRETTY
        assert config.accessLog is True
        assert config.runtimeDir == Path("runtime")
        assert config.healthPath == "/health"
        assert config.healthTimeout == 5
        assert config.slowRequestThreshold == 1.0
        assert "/health" in config.excludePaths
        assert "/metrics" in config.excludePaths

    def test_get_effective_config_dev(self) -> None:
        """Test getting effective config for dev mode."""
        config = LauncherConfig(
            mode=RunMode.DEV,
            reload=False,
            dev=EnvironmentConfig(reload=True, log_level="debug"),
        )
        
        effective = config.getEffectiveConfig()
        
        assert effective.reload is True
        assert effective.logLevel == "debug"

    def test_get_effective_config_prod(self) -> None:
        """Test getting effective config for prod mode."""
        config = LauncherConfig(
            mode=RunMode.PROD,
            workers=1,
            prod=EnvironmentConfig(workers=4, log_format=LogFormat.JSON),
        )
        
        effective = config.getEffectiveConfig()
        
        assert effective.workers == 4
        assert effective.logFormat == LogFormat.JSON

    def test_get_effective_config_no_override(self) -> None:
        """Test effective config without environment override."""
        config = LauncherConfig(reload=True)
        effective = config.getEffectiveConfig()
        
        assert effective.reload is True

    def test_to_uvicorn_kwargs_dev(self) -> None:
        """Test converting to uvicorn kwargs for dev mode."""
        config = LauncherConfig(
            mode=RunMode.DEV,
            host="0.0.0.0",
            port=9000,
            reload=True,
            reload_dirs=["src", "lib"],
        )
        
        kwargs = config.toUvicornKwargs()
        
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 9000
        assert kwargs["reload"] is True
        assert kwargs["reload_dirs"] == ["src", "lib"]
        assert "workers" not in kwargs

    def test_to_uvicorn_kwargs_prod(self) -> None:
        """Test converting to uvicorn kwargs for prod mode."""
        config = LauncherConfig(
            mode=RunMode.PROD,
            host="0.0.0.0",
            port=8000,
            workers=4,
        )
        
        kwargs = config.toUvicornKwargs()
        
        assert kwargs["workers"] == 4
        assert "reload" not in kwargs


class TestLogConfig:
    """Tests for LogConfig schema."""

    def test_default_values(self) -> None:
        """Test default log configuration."""
        config = LogConfig()
        
        assert config.logDir == Path("runtime/logs")
        assert config.logFile == "fa.log"
        assert config.accessLogFile == "access.log"
        assert config.errorLogFile == "error.log"
        assert config.logFormat == LogFormat.PRETTY
        assert config.maxBytes == 10 * 1024 * 1024
        assert config.backupCount == 5


class TestAccessLogEntry:
    """Tests for AccessLogEntry schema."""

    def test_create_entry(self) -> None:
        """Test creating access log entry."""
        entry = AccessLogEntry(
            method="GET",
            path="/api/users",
            status_code=200,
            response_time=0.05,
        )
        
        assert entry.method == "GET"
        assert entry.path == "/api/users"
        assert entry.statusCode == 200
        assert entry.responseTime == 0.05
        assert entry.isSlow is False

    def test_slow_request_flag(self) -> None:
        """Test slow request flag."""
        entry = AccessLogEntry(
            method="POST",
            path="/api/data",
            status_code=201,
            response_time=2.5,
            is_slow=True,
        )
        
        assert entry.isSlow is True

    def test_to_pretty_str(self) -> None:
        """Test pretty string format."""
        entry = AccessLogEntry(
            method="GET",
            path="/health",
            status_code=200,
            response_time=0.001,
        )
        
        prettyStr = entry.toPrettyStr()
        
        assert "GET" in prettyStr
        assert "/health" in prettyStr
        assert "200" in prettyStr
        assert "0.001s" in prettyStr

    def test_to_pretty_str_slow(self) -> None:
        """Test pretty string format for slow request."""
        entry = AccessLogEntry(
            method="POST",
            path="/api/heavy",
            status_code=200,
            response_time=5.0,
            is_slow=True,
        )
        
        prettyStr = entry.toPrettyStr()
        
        assert "[SLOW]" in prettyStr

    def test_to_json_str(self) -> None:
        """Test JSON string format."""
        entry = AccessLogEntry(
            method="GET",
            path="/api/users",
            status_code=200,
            response_time=0.1,
        )
        
        jsonStr = entry.toJsonStr()
        
        assert '"method":"GET"' in jsonStr
        assert '"path":"/api/users"' in jsonStr
        assert '"status_code":200' in jsonStr

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        entry = AccessLogEntry(
            method="GET",
            path="/test",
            status_code=200,
            response_time=0.01,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            content_length=1024,
            query_string="page=1",
        )
        
        assert entry.clientIp == "192.168.1.1"
        assert entry.userAgent == "Mozilla/5.0"
        assert entry.contentLength == 1024
        assert entry.queryString == "page=1"
