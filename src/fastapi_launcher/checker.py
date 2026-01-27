"""Configuration and dependency checker."""

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import loadConfig, getConfigSummary
from .discover import discoverApp, validateAppPath, getAppPathCandidates
from .schemas import LauncherConfig
from .ui import (
    console,
    printConfigTable,
    printErrorMessage,
    printSuccessMessage,
    printWarningMessage,
)


@dataclass
class CheckResult:
    """Result of a check operation."""

    name: str
    passed: bool
    message: str
    suggestions: list[str] = field(default_factory=list)


@dataclass
class CheckReport:
    """Full check report."""

    results: list[CheckResult] = field(default_factory=list)

    @property
    def allPassed(self) -> bool:
        """Check if all checks passed."""
        return all(r.passed for r in self.results)

    @property
    def passedCount(self) -> int:
        """Number of passed checks."""
        return sum(1 for r in self.results if r.passed)

    @property
    def failedCount(self) -> int:
        """Number of failed checks."""
        return sum(1 for r in self.results if not r.passed)


def checkDependency(moduleName: str, packageName: Optional[str] = None) -> CheckResult:
    """
    Check if a Python package is installed.

    Args:
        moduleName: Module name to import
        packageName: Package name for install suggestion (if different)

    Returns:
        CheckResult
    """
    packageName = packageName or moduleName

    if importlib.util.find_spec(moduleName) is not None:
        return CheckResult(
            name=f"Dependency: {moduleName}",
            passed=True,
            message=f"{moduleName} is installed",
        )
    else:
        return CheckResult(
            name=f"Dependency: {moduleName}",
            passed=False,
            message=f"{moduleName} is not installed",
            suggestions=[f"Install with: pip install {packageName}"],
        )


def checkFastAPI() -> CheckResult:
    """Check if FastAPI is installed."""
    return checkDependency("fastapi")


def checkUvicorn() -> CheckResult:
    """Check if uvicorn is installed."""
    return checkDependency("uvicorn")


def checkAppPath(
    config: LauncherConfig, projectDir: Optional[Path] = None
) -> CheckResult:
    """
    Check if app path is valid.

    Args:
        config: Launcher configuration
        projectDir: Project directory

    Returns:
        CheckResult
    """
    if projectDir is None:
        projectDir = Path.cwd()

    appPath = config.app

    # Try auto-discovery if not specified
    if appPath is None:
        appPath = discoverApp(projectDir)
        if appPath:
            return CheckResult(
                name="App Path",
                passed=True,
                message=f"Auto-discovered app: {appPath}",
            )
        else:
            candidates = getAppPathCandidates(projectDir)
            return CheckResult(
                name="App Path",
                passed=False,
                message="Could not auto-discover FastAPI app",
                suggestions=[
                    "Create main.py with 'app = FastAPI()'",
                    "Specify app path in pyproject.toml: [tool.fastapi-launcher] app = 'main:app'",
                ]
                + (
                    [f"Found candidates: {', '.join(candidates)}"] if candidates else []
                ),
            )

    # Validate specified path
    if validateAppPath(appPath, projectDir):
        return CheckResult(
            name="App Path",
            passed=True,
            message=f"App path is valid: {appPath}",
        )
    else:
        return CheckResult(
            name="App Path",
            passed=False,
            message=f"Cannot import app from: {appPath}",
            suggestions=[
                "Check that the module exists",
                "Ensure the app variable is defined",
                "Verify FastAPI is installed",
            ],
        )


def checkConfig(projectDir: Optional[Path] = None) -> CheckResult:
    """
    Check if configuration is valid.

    Args:
        projectDir: Project directory

    Returns:
        CheckResult
    """
    try:
        loadConfig(projectDir)
        return CheckResult(
            name="Configuration",
            passed=True,
            message="Configuration is valid",
        )
    except ValueError as e:
        return CheckResult(
            name="Configuration",
            passed=False,
            message=f"Invalid configuration: {e}",
            suggestions=[
                "Check pyproject.toml [tool.fastapi-launcher] section",
                "Verify .env file format",
                "Check environment variables with FA_ prefix",
            ],
        )


def checkPyprojectToml(projectDir: Optional[Path] = None) -> CheckResult:
    """
    Check if pyproject.toml exists and has launcher config.

    Args:
        projectDir: Project directory

    Returns:
        CheckResult
    """
    if projectDir is None:
        projectDir = Path.cwd()

    pyprojectPath = projectDir / "pyproject.toml"

    if not pyprojectPath.exists():
        return CheckResult(
            name="pyproject.toml",
            passed=True,  # Not required
            message="No pyproject.toml found (using defaults)",
        )

    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        with open(pyprojectPath, "rb") as f:
            data = tomllib.load(f)

        if "tool" in data and "fastapi-launcher" in data["tool"]:
            return CheckResult(
                name="pyproject.toml",
                passed=True,
                message="Found [tool.fastapi-launcher] configuration",
            )
        else:
            return CheckResult(
                name="pyproject.toml",
                passed=True,
                message="No [tool.fastapi-launcher] section (using defaults)",
            )
    except Exception as e:
        return CheckResult(
            name="pyproject.toml",
            passed=False,
            message=f"Error reading pyproject.toml: {e}",
        )


def runAllChecks(projectDir: Optional[Path] = None) -> CheckReport:
    """
    Run all configuration and dependency checks.

    Args:
        projectDir: Project directory

    Returns:
        CheckReport with all results
    """
    if projectDir is None:
        projectDir = Path.cwd()

    report = CheckReport()

    # Dependency checks
    report.results.append(checkFastAPI())
    report.results.append(checkUvicorn())

    # Config checks
    report.results.append(checkPyprojectToml(projectDir))
    report.results.append(checkConfig(projectDir))

    # App check
    try:
        config = loadConfig(projectDir)
        report.results.append(checkAppPath(config, projectDir))
    except ValueError:
        report.results.append(
            CheckResult(
                name="App Path",
                passed=False,
                message="Cannot check app path due to config errors",
            )
        )

    return report


def printCheckReport(report: CheckReport) -> None:
    """
    Print check report to console.

    Args:
        report: Check report to print
    """
    console.print("\n[bold]Check Results[/]\n")

    for result in report.results:
        if result.passed:
            printSuccessMessage(f"{result.name}: {result.message}")
        else:
            printErrorMessage(f"{result.name}: {result.message}")
            for suggestion in result.suggestions:
                console.print(f"    → {suggestion}", style="dim")

    console.print()

    if report.allPassed:
        printSuccessMessage(f"All {report.passedCount} checks passed!")
    else:
        printWarningMessage(f"{report.passedCount} passed, {report.failedCount} failed")


def showConfig(projectDir: Optional[Path] = None, envName: Optional[str] = None) -> None:
    """
    Show current configuration.

    Args:
        projectDir: Project directory
        envName: Named environment from pyproject.toml (e.g., 'staging', 'prod')
    """
    try:
        config = loadConfig(projectDir, envName=envName)
        summary = getConfigSummary(config)
        printConfigTable(summary, title="Current Configuration")
    except ValueError as e:
        printErrorMessage(f"Error loading configuration: {e}")
