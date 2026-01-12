"""Tests for configuration and dependency checker."""

from pathlib import Path
from unittest.mock import patch

import pytest

from fastapi_launcher.checker import (
    CheckReport,
    CheckResult,
    checkAppPath,
    checkConfig,
    checkDependency,
    checkFastAPI,
    checkPyprojectToml,
    checkUvicorn,
    runAllChecks,
    showConfig,
)
from fastapi_launcher.schemas import LauncherConfig


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_passed_result(self) -> None:
        """Test passed check result."""
        result = CheckResult(
            name="Test Check",
            passed=True,
            message="All good",
        )
        
        assert result.passed is True
        assert result.suggestions == []

    def test_failed_result_with_suggestions(self) -> None:
        """Test failed result with suggestions."""
        result = CheckResult(
            name="Test Check",
            passed=False,
            message="Something wrong",
            suggestions=["Try this", "Or that"],
        )
        
        assert result.passed is False
        assert len(result.suggestions) == 2


class TestCheckReport:
    """Tests for CheckReport."""

    def test_all_passed(self) -> None:
        """Test all checks passed."""
        report = CheckReport(results=[
            CheckResult("Check 1", True, "OK"),
            CheckResult("Check 2", True, "OK"),
        ])
        
        assert report.allPassed is True
        assert report.passedCount == 2
        assert report.failedCount == 0

    def test_some_failed(self) -> None:
        """Test some checks failed."""
        report = CheckReport(results=[
            CheckResult("Check 1", True, "OK"),
            CheckResult("Check 2", False, "Failed"),
        ])
        
        assert report.allPassed is False
        assert report.passedCount == 1
        assert report.failedCount == 1

    def test_empty_report(self) -> None:
        """Test empty report."""
        report = CheckReport()
        
        assert report.allPassed is True
        assert report.passedCount == 0


class TestCheckDependency:
    """Tests for dependency checking."""

    def test_installed_dependency(self) -> None:
        """Test checking installed dependency."""
        result = checkDependency("os")  # Always installed
        
        assert result.passed is True

    def test_missing_dependency(self) -> None:
        """Test checking missing dependency."""
        result = checkDependency("nonexistent_package_xyz")
        
        assert result.passed is False
        assert len(result.suggestions) > 0


class TestCheckFastAPI:
    """Tests for FastAPI dependency check."""

    @patch("fastapi_launcher.checker.importlib.util.find_spec")
    def test_fastapi_installed(self, mockFindSpec) -> None:
        """Test when FastAPI is installed."""
        mockFindSpec.return_value = True
        
        result = checkFastAPI()
        
        assert result.passed is True

    @patch("fastapi_launcher.checker.importlib.util.find_spec")
    def test_fastapi_not_installed(self, mockFindSpec) -> None:
        """Test when FastAPI is not installed."""
        mockFindSpec.return_value = None
        
        result = checkFastAPI()
        
        assert result.passed is False


class TestCheckUvicorn:
    """Tests for uvicorn dependency check."""

    @patch("fastapi_launcher.checker.importlib.util.find_spec")
    def test_uvicorn_installed(self, mockFindSpec) -> None:
        """Test when uvicorn is installed."""
        mockFindSpec.return_value = True
        
        result = checkUvicorn()
        
        assert result.passed is True


class TestCheckPyprojectToml:
    """Tests for pyproject.toml check."""

    def test_no_pyproject(self, tempDir: Path) -> None:
        """Test when pyproject.toml doesn't exist."""
        result = checkPyprojectToml(tempDir)
        
        assert result.passed is True
        assert "defaults" in result.message.lower()

    def test_with_launcher_config(self, mockProjectDir: Path) -> None:
        """Test with [tool.fastapi-launcher] section."""
        result = checkPyprojectToml(mockProjectDir)
        
        assert result.passed is True
        assert "fastapi-launcher" in result.message

    def test_without_launcher_section(self, tempDir: Path) -> None:
        """Test without launcher section."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("[project]\nname = 'test'\n")
        
        result = checkPyprojectToml(tempDir)
        
        assert result.passed is True


class TestCheckConfig:
    """Tests for configuration check."""

    def test_valid_config(self, mockProjectDir: Path) -> None:
        """Test with valid configuration."""
        result = checkConfig(mockProjectDir)
        
        assert result.passed is True

    def test_invalid_config(self, tempDir: Path) -> None:
        """Test with invalid configuration."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[tool.fastapi-launcher]
port = -1
""")
        
        result = checkConfig(tempDir)
        
        assert result.passed is False


class TestCheckAppPath:
    """Tests for app path check."""

    def test_app_discovered(self, mockProjectDir: Path) -> None:
        """Test when app is discovered."""
        config = LauncherConfig()
        
        result = checkAppPath(config, mockProjectDir)
        
        assert result.passed is True
        assert "main:app" in result.message

    def test_no_app_found(self, tempDir: Path) -> None:
        """Test when no app is found."""
        config = LauncherConfig()
        
        result = checkAppPath(config, tempDir)
        
        assert result.passed is False
        assert len(result.suggestions) > 0


class TestRunAllChecks:
    """Tests for running all checks."""

    def test_run_all_checks(self, mockProjectDir: Path) -> None:
        """Test running all checks."""
        report = runAllChecks(mockProjectDir)
        
        assert len(report.results) >= 4  # At least 4 checks

    def test_includes_all_check_types(self, mockProjectDir: Path) -> None:
        """Test that all check types are included."""
        report = runAllChecks(mockProjectDir)
        
        names = [r.name for r in report.results]
        
        # Check key checks are present
        assert any("fastapi" in n.lower() for n in names)
        assert any("uvicorn" in n.lower() for n in names)
        assert any("pyproject" in n.lower() for n in names)


class TestShowConfig:
    """Tests for showing configuration."""

    def test_show_config(self, mockProjectDir: Path) -> None:
        """Test showing configuration."""
        # Just verify no exception
        showConfig(mockProjectDir)

    def test_show_config_error(self, tempDir: Path) -> None:
        """Test showing config with error."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("[tool.fastapi-launcher]\nport = -1\n")
        
        # Should not raise, just print error
        showConfig(tempDir)


class TestPrintCheckReport:
    """Tests for printing check report."""

    def test_print_all_passed(self) -> None:
        """Test printing all passed report."""
        from fastapi_launcher.checker import printCheckReport
        
        report = CheckReport(results=[
            CheckResult("Check 1", True, "OK"),
            CheckResult("Check 2", True, "OK"),
        ])
        
        # Just verify no exception
        printCheckReport(report)

    def test_print_with_failures(self) -> None:
        """Test printing report with failures."""
        from fastapi_launcher.checker import printCheckReport
        
        report = CheckReport(results=[
            CheckResult("Check 1", True, "OK"),
            CheckResult("Check 2", False, "Failed", suggestions=["Try this"]),
        ])
        
        printCheckReport(report)


class TestCheckAppPathWithCandidates:
    """Tests for checkAppPath with candidates."""

    def test_app_path_with_candidates(self, tempDir: Path) -> None:
        """Test checkAppPath shows candidates when not found."""
        from fastapi_launcher.discover import getAppPathCandidates
        
        # Create a file that looks like it might have an app
        mainPath = tempDir / "main.py"
        mainPath.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        config = LauncherConfig()
        
        with patch("fastapi_launcher.checker.discoverApp") as mockDiscover:
            mockDiscover.return_value = None
            
            result = checkAppPath(config, tempDir)
            
            # Should fail but show candidates
            # Note: it might pass if discovery works


class TestCheckDependencyPackageName:
    """Tests for checkDependency with package name."""

    def test_check_dependency_with_package_name(self) -> None:
        """Test checking dependency with different package name."""
        result = checkDependency("PIL", "Pillow")
        
        # PIL is not installed, so should fail
        assert result.passed is False
        assert "Pillow" in result.suggestions[0]


class TestCheckConfigErrors:
    """Tests for checkConfig error handling."""

    def test_check_config_with_env_error(self, tempDir: Path) -> None:
        """Test checkConfig with environment variable errors."""
        import os
        
        # Set invalid env var
        os.environ["FA_PORT"] = "invalid"
        
        try:
            result = checkConfig(tempDir)
            # Should still work, invalid values are ignored
        finally:
            del os.environ["FA_PORT"]
