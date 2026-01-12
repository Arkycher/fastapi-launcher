"""Tests for logging functionality."""

import logging
from pathlib import Path

import pytest

from fastapi_launcher.enums import LogFormat
from fastapi_launcher.logs import (
    JsonFormatter,
    cleanLogs,
    getLogFiles,
    printLogEntry,
    readLogFile,
    rotateLogs,
    setupLogging,
    _tailFile,
)
from fastapi_launcher.schemas import LogConfig


class TestSetupLogging:
    """Tests for logging setup."""

    def test_setup_pretty_logging(self, tempDir: Path) -> None:
        """Test setting up pretty log format."""
        config = LogConfig(log_dir=tempDir / "logs")
        
        logger = setupLogging(config, logFormat=LogFormat.PRETTY)
        
        assert logger.name == "fastapi_launcher"
        assert len(logger.handlers) >= 1

    def test_setup_json_logging(self, tempDir: Path) -> None:
        """Test setting up JSON log format."""
        config = LogConfig(log_dir=tempDir / "logs")
        
        logger = setupLogging(config, logFormat=LogFormat.JSON)
        
        # Check JSON formatter is used
        hasJsonFormatter = any(
            isinstance(h.formatter, JsonFormatter)
            for h in logger.handlers
        )
        assert hasJsonFormatter

    def test_creates_log_directory(self, tempDir: Path) -> None:
        """Test that log directory is created."""
        logDir = tempDir / "logs"
        config = LogConfig(log_dir=logDir)
        
        setupLogging(config)
        
        assert logDir.exists()


class TestJsonFormatter:
    """Tests for JSON log formatter."""

    def test_format_basic_message(self) -> None:
        """Test formatting basic log message."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        # JSON may have spaces after colons
        assert '"level"' in result and "INFO" in result
        assert '"message"' in result and "Test message" in result

    def test_format_with_exception(self) -> None:
        """Test formatting message with exception."""
        formatter = JsonFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            excInfo = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=excInfo,
        )
        
        result = formatter.format(record)
        
        assert '"exception"' in result


class TestReadLogFile:
    """Tests for reading log files."""

    def test_read_log_file(self, tempDir: Path) -> None:
        """Test reading log file."""
        logFile = tempDir / "test.log"
        logFile.write_text("Line 1\nLine 2\nLine 3\n")
        
        lines = list(readLogFile(logFile, lines=10))
        
        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[2] == "Line 3"

    def test_read_last_n_lines(self, tempDir: Path) -> None:
        """Test reading last N lines."""
        logFile = tempDir / "test.log"
        content = "\n".join(f"Line {i}" for i in range(100))
        logFile.write_text(content)
        
        lines = list(readLogFile(logFile, lines=10))
        
        assert len(lines) == 10
        assert "Line 90" in lines[0]

    def test_read_nonexistent_file(self, tempDir: Path) -> None:
        """Test reading non-existent file."""
        logFile = tempDir / "nonexistent.log"
        
        lines = list(readLogFile(logFile))
        
        assert lines == []


class TestTailFile:
    """Tests for tail file function."""

    def test_tail_file(self, tempDir: Path) -> None:
        """Test tailing file."""
        logFile = tempDir / "test.log"
        logFile.write_text("Line 1\nLine 2\nLine 3\n")
        
        lines = list(_tailFile(logFile, 2))
        
        assert len(lines) == 2
        assert lines[0] == "Line 2"
        assert lines[1] == "Line 3"


class TestGetLogFiles:
    """Tests for getting log file paths."""

    def test_get_log_files(self, tempDir: Path) -> None:
        """Test getting log file paths."""
        logFiles = getLogFiles(tempDir)
        
        assert "main" in logFiles
        assert "access" in logFiles
        assert "error" in logFiles
        assert logFiles["main"] == tempDir / "logs" / "fa.log"


class TestRotateLogs:
    """Tests for log rotation."""

    def test_rotate_large_file(self, tempDir: Path) -> None:
        """Test rotating large log file."""
        logsDir = tempDir / "logs"
        logsDir.mkdir()
        logFile = logsDir / "fa.log"
        
        # Create a file larger than threshold
        logFile.write_text("x" * 1000)
        
        rotateLogs(tempDir, maxBytes=500, backupCount=3)
        
        # Original should be empty/gone, .1 should exist
        assert (logsDir / "fa.log.1").exists()

    def test_rotate_small_file_unchanged(self, tempDir: Path) -> None:
        """Test that small files are not rotated."""
        logsDir = tempDir / "logs"
        logsDir.mkdir()
        logFile = logsDir / "fa.log"
        logFile.write_text("small content")
        
        rotateLogs(tempDir, maxBytes=10000)
        
        assert logFile.exists()
        assert not (logsDir / "fa.log.1").exists()


class TestCleanLogs:
    """Tests for cleaning logs."""

    def test_clean_logs(self, tempDir: Path) -> None:
        """Test cleaning log files."""
        logsDir = tempDir / "logs"
        logsDir.mkdir()
        
        (logsDir / "fa.log").write_text("content")
        (logsDir / "access.log").write_text("content")
        (logsDir / "error.log").write_text("content")
        
        count = cleanLogs(tempDir)
        
        assert count == 3
        assert not (logsDir / "fa.log").exists()

    def test_clean_logs_no_directory(self, tempDir: Path) -> None:
        """Test cleaning when logs directory doesn't exist."""
        count = cleanLogs(tempDir)
        
        assert count == 0


class TestPrintLogEntry:
    """Tests for printing log entries."""

    def test_print_info_log(self) -> None:
        """Test printing info log."""
        # Just verify no exception
        printLogEntry("2024-01-01 12:00:00 | INFO | Test message")

    def test_print_error_log(self) -> None:
        """Test printing error log."""
        printLogEntry("2024-01-01 12:00:00 | ERROR | Test error")

    def test_print_warning_log(self) -> None:
        """Test printing warning log."""
        printLogEntry("2024-01-01 12:00:00 | WARNING | Test warning")

    def test_print_json_format(self) -> None:
        """Test printing in JSON format."""
        printLogEntry('{"level": "INFO", "message": "test"}', LogFormat.JSON)


class TestFollowFile:
    """Tests for file following."""

    def test_follow_file_initial_lines(self, tempDir: Path) -> None:
        """Test follow file returns initial lines."""
        logFile = tempDir / "test.log"
        content = "\n".join(f"Line {i}" for i in range(20))
        logFile.write_text(content)
        
        from fastapi_launcher.logs import _followFile
        
        # Get first few lines (non-blocking test)
        lines = []
        gen = _followFile(logFile, initialLines=5)
        
        # Just get initial lines
        import itertools
        for line in itertools.islice(gen, 5):
            lines.append(line)
        
        assert len(lines) == 5


class TestRotateLogsExtended:
    """Extended tests for log rotation."""

    def test_rotate_multiple_backups(self, tempDir: Path) -> None:
        """Test rotating with multiple existing backups."""
        logsDir = tempDir / "logs"
        logsDir.mkdir()
        
        # Create main log and backups
        (logsDir / "fa.log").write_text("x" * 2000)
        (logsDir / "fa.log.1").write_text("backup 1")
        (logsDir / "fa.log.2").write_text("backup 2")
        
        rotateLogs(tempDir, maxBytes=1000, backupCount=3)
        
        # fa.log should be rotated to fa.log.1
        # old fa.log.1 should be fa.log.2
        assert (logsDir / "fa.log.1").exists()
        assert (logsDir / "fa.log.2").exists()

    def test_rotate_removes_oldest(self, tempDir: Path) -> None:
        """Test that rotation removes oldest backup."""
        logsDir = tempDir / "logs"
        logsDir.mkdir()
        
        # Create log with max backups
        (logsDir / "fa.log").write_text("x" * 2000)
        (logsDir / "fa.log.1").write_text("backup 1")
        (logsDir / "fa.log.2").write_text("backup 2")
        (logsDir / "fa.log.3").write_text("backup 3")
        
        rotateLogs(tempDir, maxBytes=1000, backupCount=3)
        
        # fa.log.3 should be removed
        assert not (logsDir / "fa.log.4").exists()


class TestSetupLoggingExtended:
    """Extended tests for logging setup."""

    def test_setup_with_log_level(self, tempDir: Path) -> None:
        """Test setup with different log levels."""
        config = LogConfig(log_dir=tempDir / "logs")
        
        logger = setupLogging(config, logLevel="DEBUG")
        
        assert logger.level == logging.DEBUG

    def test_setup_json_format_handler(self, tempDir: Path) -> None:
        """Test setup adds correct handler for JSON format."""
        config = LogConfig(log_dir=tempDir / "logs")
        
        logger = setupLogging(config, logFormat=LogFormat.JSON)
        
        # Should have at least one JsonFormatter
        hasJson = any(
            isinstance(h.formatter, JsonFormatter) 
            for h in logger.handlers
        )
        assert hasJson
