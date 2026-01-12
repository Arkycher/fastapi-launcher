"""Tests for UI components."""

from datetime import timedelta
from io import StringIO

import pytest
from rich.console import Console

from fastapi_launcher.enums import RunMode
from fastapi_launcher.schemas import LauncherConfig
from fastapi_launcher.ui import (
    colorizeHttpMethod,
    colorizeStatusCode,
    printConfigTable,
    printErrorMessage,
    printErrorPanel,
    printHealthStatus,
    printInfoMessage,
    printStartupPanel,
    printStatusTable,
    printSuccessMessage,
    printWarningMessage,
    _formatUptime,
)


class TestFormatUptime:
    """Tests for uptime formatting."""

    def test_format_seconds(self) -> None:
        """Test formatting seconds only."""
        result = _formatUptime(timedelta(seconds=45))
        assert result == "45s"

    def test_format_minutes_seconds(self) -> None:
        """Test formatting minutes and seconds."""
        result = _formatUptime(timedelta(minutes=5, seconds=30))
        assert result == "5m 30s"

    def test_format_hours_minutes_seconds(self) -> None:
        """Test formatting hours, minutes, and seconds."""
        result = _formatUptime(timedelta(hours=2, minutes=30, seconds=15))
        assert result == "2h 30m 15s"

    def test_format_days(self) -> None:
        """Test formatting days."""
        result = _formatUptime(timedelta(days=3, hours=12))
        # Function omits zero minutes when no seconds context
        assert "3d" in result
        assert "12h" in result


class TestColorizeHttpMethod:
    """Tests for HTTP method colorization."""

    def test_get_method(self) -> None:
        """Test GET method color."""
        result = colorizeHttpMethod("GET")
        assert "[green]" in result
        assert "GET" in result

    def test_post_method(self) -> None:
        """Test POST method color."""
        result = colorizeHttpMethod("POST")
        assert "[yellow]" in result
        assert "POST" in result

    def test_delete_method(self) -> None:
        """Test DELETE method color."""
        result = colorizeHttpMethod("DELETE")
        assert "[red]" in result
        assert "DELETE" in result

    def test_unknown_method(self) -> None:
        """Test unknown method."""
        result = colorizeHttpMethod("CUSTOM")
        assert "CUSTOM" in result


class TestColorizeStatusCode:
    """Tests for status code colorization."""

    def test_2xx_success(self) -> None:
        """Test 2xx success codes."""
        result = colorizeStatusCode(200)
        assert "[green]" in result
        assert "200" in result

    def test_3xx_redirect(self) -> None:
        """Test 3xx redirect codes."""
        result = colorizeStatusCode(301)
        assert "[yellow]" in result

    def test_4xx_client_error(self) -> None:
        """Test 4xx client error codes."""
        result = colorizeStatusCode(404)
        assert "[red]" in result

    def test_5xx_server_error(self) -> None:
        """Test 5xx server error codes."""
        result = colorizeStatusCode(500)
        assert "[bold red]" in result


class TestPrintFunctions:
    """Tests for print functions with captured output."""

    def test_print_success_message(self, capsys) -> None:
        """Test printing success message."""
        printSuccessMessage("Operation completed")
        
        # Rich output goes through its own console
        # We can't easily capture it with capsys
        # Just verify no exception is raised

    def test_print_error_message(self) -> None:
        """Test printing error message."""
        # Just verify no exception
        printErrorMessage("Something went wrong")

    def test_print_warning_message(self) -> None:
        """Test printing warning message."""
        printWarningMessage("Be careful")

    def test_print_info_message(self) -> None:
        """Test printing info message."""
        printInfoMessage("FYI")


class TestPrintStartupPanel:
    """Tests for startup panel printing."""

    def test_print_dev_mode(self) -> None:
        """Test startup panel in dev mode."""
        config = LauncherConfig(
            app="main:app",
            mode=RunMode.DEV,
            reload=True,
        )
        
        # Just verify no exception
        printStartupPanel(config)

    def test_print_prod_mode(self) -> None:
        """Test startup panel in prod mode."""
        config = LauncherConfig(
            app="main:app",
            mode=RunMode.PROD,
            workers=4,
        )
        
        printStartupPanel(config)


class TestPrintStatusTable:
    """Tests for status table printing."""

    def test_print_running_status(self) -> None:
        """Test printing running server status."""
        status = {
            "running": True,
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8000,
        }
        
        printStatusTable(status)

    def test_print_stopped_status(self) -> None:
        """Test printing stopped server status."""
        status = {
            "running": False,
            "pid": None,
            "host": "127.0.0.1",
            "port": 8000,
        }
        
        printStatusTable(status)

    def test_print_with_process_info(self) -> None:
        """Test printing with process information."""
        status = {
            "running": True,
            "pid": 12345,
            "host": "127.0.0.1",
            "port": 8000,
        }
        processInfo = {
            "uptime": timedelta(hours=2, minutes=30),
            "memory_mb": 128.5,
            "cpu_percent": 5.2,
        }
        
        printStatusTable(status, processInfo)


class TestPrintErrorPanel:
    """Tests for error panel printing."""

    def test_print_error_no_suggestions(self) -> None:
        """Test printing error without suggestions."""
        printErrorPanel("Error Title", "Something went wrong")

    def test_print_error_with_suggestions(self) -> None:
        """Test printing error with suggestions."""
        printErrorPanel(
            "Connection Failed",
            "Could not connect to server",
            suggestions=[
                "Check if server is running",
                "Verify port is correct",
            ],
        )


class TestPrintConfigTable:
    """Tests for config table printing."""

    def test_print_config(self) -> None:
        """Test printing configuration table."""
        config = {
            "app": "main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "reload": True,
            "daemon": False,
            "not_set": None,
        }
        
        printConfigTable(config)


class TestPrintHealthStatus:
    """Tests for health status printing."""

    def test_print_healthy(self) -> None:
        """Test printing healthy status."""
        printHealthStatus(True, "http://localhost:8000/health", 50.0)

    def test_print_unhealthy(self) -> None:
        """Test printing unhealthy status."""
        printHealthStatus(False, "http://localhost:8000/health")
