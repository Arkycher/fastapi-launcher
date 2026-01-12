"""Tests for enum definitions."""

import pytest

from fastapi_launcher.enums import LogFormat, RunMode


class TestRunMode:
    """Tests for RunMode enum."""

    def test_dev_value(self) -> None:
        """Test DEV mode value."""
        assert RunMode.DEV.value == "dev"

    def test_prod_value(self) -> None:
        """Test PROD mode value."""
        assert RunMode.PROD.value == "prod"

    def test_from_string(self) -> None:
        """Test creating from string value."""
        assert RunMode("dev") == RunMode.DEV
        assert RunMode("prod") == RunMode.PROD

    def test_string_conversion(self) -> None:
        """Test string conversion via .value."""
        assert RunMode.DEV.value == "dev"
        assert RunMode.PROD.value == "prod"

    def test_is_string_enum(self) -> None:
        """Test that RunMode is a string enum."""
        assert isinstance(RunMode.DEV, str)
        assert isinstance(RunMode.PROD, str)


class TestLogFormat:
    """Tests for LogFormat enum."""

    def test_pretty_value(self) -> None:
        """Test PRETTY format value."""
        assert LogFormat.PRETTY.value == "pretty"

    def test_json_value(self) -> None:
        """Test JSON format value."""
        assert LogFormat.JSON.value == "json"

    def test_from_string(self) -> None:
        """Test creating from string value."""
        assert LogFormat("pretty") == LogFormat.PRETTY
        assert LogFormat("json") == LogFormat.JSON

    def test_string_conversion(self) -> None:
        """Test string conversion via .value."""
        assert LogFormat.PRETTY.value == "pretty"
        assert LogFormat.JSON.value == "json"

    def test_is_string_enum(self) -> None:
        """Test that LogFormat is a string enum."""
        assert isinstance(LogFormat.PRETTY, str)
        assert isinstance(LogFormat.JSON, str)
