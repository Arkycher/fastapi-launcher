"""Tests for access log functionality."""

from datetime import datetime
from pathlib import Path

import pytest

from fastapi_launcher.accessLog import (
    createAccessLogEntry,
    formatAccessLogEntry,
    isSlowRequest,
    parseAccessLogLine,
    readAccessLog,
    shouldLogRequest,
    writeAccessLog,
)
from fastapi_launcher.enums import LogFormat
from fastapi_launcher.schemas import AccessLogEntry


class TestParseAccessLogLine:
    """Tests for parsing access log lines."""

    def test_parse_standard_uvicorn_log(self) -> None:
        """Test parsing standard uvicorn access log."""
        line = 'INFO:     127.0.0.1:51234 - "GET /api/users HTTP/1.1" 200'
        
        entry = parseAccessLogLine(line)
        
        assert entry is not None
        assert entry.method == "GET"
        assert entry.path == "/api/users"
        assert entry.statusCode == 200
        assert entry.clientIp == "127.0.0.1"

    def test_parse_with_query_string(self) -> None:
        """Test parsing log with query string."""
        line = 'INFO:     127.0.0.1:1234 - "GET /search?q=test HTTP/1.1" 200'
        
        entry = parseAccessLogLine(line)
        
        assert entry is not None
        assert entry.path == "/search"
        assert entry.queryString == "q=test"

    def test_parse_post_request(self) -> None:
        """Test parsing POST request."""
        line = 'INFO:     192.168.1.1:5000 - "POST /api/data HTTP/1.1" 201'
        
        entry = parseAccessLogLine(line)
        
        assert entry is not None
        assert entry.method == "POST"
        assert entry.statusCode == 201

    def test_parse_invalid_line(self) -> None:
        """Test parsing invalid log line."""
        line = "This is not a valid access log"
        
        entry = parseAccessLogLine(line)
        
        assert entry is None


class TestFormatAccessLogEntry:
    """Tests for formatting access log entries."""

    def test_format_pretty(self) -> None:
        """Test pretty format."""
        entry = AccessLogEntry(
            method="GET",
            path="/api/users",
            status_code=200,
            response_time=0.05,
        )
        
        result = formatAccessLogEntry(entry, LogFormat.PRETTY)
        
        assert "GET" in result
        assert "/api/users" in result
        assert "200" in result

    def test_format_json(self) -> None:
        """Test JSON format."""
        entry = AccessLogEntry(
            method="POST",
            path="/api/data",
            status_code=201,
            response_time=0.1,
        )
        
        result = formatAccessLogEntry(entry, LogFormat.JSON)
        
        assert '"method":"POST"' in result
        assert '"status_code":201' in result


class TestShouldLogRequest:
    """Tests for request logging filter."""

    def test_should_log_normal_path(self) -> None:
        """Test logging normal paths."""
        excludePaths = ["/health", "/metrics"]
        
        assert shouldLogRequest("/api/users", excludePaths) is True

    def test_should_not_log_excluded_path(self) -> None:
        """Test excluding exact paths."""
        excludePaths = ["/health", "/metrics"]
        
        assert shouldLogRequest("/health", excludePaths) is False
        assert shouldLogRequest("/metrics", excludePaths) is False

    def test_should_not_log_excluded_prefix(self) -> None:
        """Test excluding path prefixes."""
        excludePaths = ["/internal"]
        
        assert shouldLogRequest("/internal/status", excludePaths) is False

    def test_empty_exclude_list(self) -> None:
        """Test with empty exclude list."""
        assert shouldLogRequest("/anything", []) is True


class TestIsSlowRequest:
    """Tests for slow request detection."""

    def test_fast_request(self) -> None:
        """Test fast request is not slow."""
        assert isSlowRequest(0.1, threshold=1.0) is False

    def test_slow_request(self) -> None:
        """Test slow request is detected."""
        assert isSlowRequest(2.0, threshold=1.0) is True

    def test_exact_threshold(self) -> None:
        """Test request at exact threshold."""
        assert isSlowRequest(1.0, threshold=1.0) is True

    def test_custom_threshold(self) -> None:
        """Test with custom threshold."""
        assert isSlowRequest(0.5, threshold=0.3) is True
        assert isSlowRequest(0.2, threshold=0.3) is False


class TestCreateAccessLogEntry:
    """Tests for creating access log entries."""

    def test_create_basic_entry(self) -> None:
        """Test creating basic entry."""
        entry = createAccessLogEntry(
            method="GET",
            path="/api/users",
            statusCode=200,
            responseTime=0.05,
        )
        
        assert entry.method == "GET"
        assert entry.path == "/api/users"
        assert entry.statusCode == 200
        assert entry.isSlow is False

    def test_create_slow_entry(self) -> None:
        """Test creating slow request entry."""
        entry = createAccessLogEntry(
            method="POST",
            path="/api/heavy",
            statusCode=200,
            responseTime=2.0,
            slowThreshold=1.0,
        )
        
        assert entry.isSlow is True

    def test_create_entry_with_all_fields(self) -> None:
        """Test creating entry with all optional fields."""
        entry = createAccessLogEntry(
            method="PUT",
            path="/api/data",
            statusCode=200,
            responseTime=0.1,
            clientIp="192.168.1.1",
            userAgent="TestClient/1.0",
            contentLength=1024,
            queryString="id=123",
        )
        
        assert entry.clientIp == "192.168.1.1"
        assert entry.userAgent == "TestClient/1.0"
        assert entry.contentLength == 1024
        assert entry.queryString == "id=123"


class TestWriteAccessLog:
    """Tests for writing access log."""

    def test_write_access_log(self, tempDir: Path) -> None:
        """Test writing access log entry."""
        logFile = tempDir / "access.log"
        entry = AccessLogEntry(
            method="GET",
            path="/test",
            status_code=200,
            response_time=0.01,
        )
        
        writeAccessLog(entry, logFile, LogFormat.PRETTY)
        
        assert logFile.exists()
        content = logFile.read_text()
        assert "GET" in content
        assert "/test" in content

    def test_write_creates_parent_dirs(self, tempDir: Path) -> None:
        """Test that parent directories are created."""
        logFile = tempDir / "logs" / "nested" / "access.log"
        entry = AccessLogEntry(
            method="GET",
            path="/test",
            status_code=200,
            response_time=0.01,
        )
        
        writeAccessLog(entry, logFile)
        
        assert logFile.exists()


class TestReadAccessLog:
    """Tests for reading access log."""

    def test_read_access_log(self, tempDir: Path) -> None:
        """Test reading access log entries."""
        logFile = tempDir / "access.log"
        
        # Write some entries
        entries = [
            AccessLogEntry(method="GET", path="/a", status_code=200, response_time=0.01),
            AccessLogEntry(method="POST", path="/b", status_code=201, response_time=0.02),
        ]
        for entry in entries:
            writeAccessLog(entry, logFile, LogFormat.JSON)
        
        result = readAccessLog(logFile)
        
        assert len(result) == 2

    def test_read_filter_by_method(self, tempDir: Path) -> None:
        """Test filtering by method."""
        logFile = tempDir / "access.log"
        
        entries = [
            AccessLogEntry(method="GET", path="/a", status_code=200, response_time=0.01),
            AccessLogEntry(method="POST", path="/b", status_code=201, response_time=0.02),
        ]
        for entry in entries:
            writeAccessLog(entry, logFile, LogFormat.JSON)
        
        result = readAccessLog(logFile, filterMethod="GET")
        
        assert len(result) == 1
        assert result[0].method == "GET"

    def test_read_nonexistent_file(self, tempDir: Path) -> None:
        """Test reading non-existent file."""
        logFile = tempDir / "nonexistent.log"
        
        result = readAccessLog(logFile)
        
        assert result == []
