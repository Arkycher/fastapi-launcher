"""CLI entry point using Typer."""

import sys
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .checker import printCheckReport, runAllChecks, showConfig
from .config import loadConfig
from .daemon import checkDaemonSupport, daemonize, setupDaemonLogging
from .enums import RunMode
from .health import checkHealth, printHealthResult
from .launcher import LaunchError, launch
from .logs import cleanLogs, getLogFiles, printLogEntry, readLogFile
from .port import getPortInfo, isPortInUse, waitForPortFree
from .process import (
    getProcessStatus,
    isProcessRunning,
    readPidFile,
    removePidFile,
    terminateProcess,
)
from .ui import (
    console,
    createSpinner,
    printErrorMessage,
    printInfoMessage,
    printStatusTable,
    printSuccessMessage,
    printWarningMessage,
)

app = typer.Typer(
    name="fa",
    help="FastAPI Launcher - A universal CLI for FastAPI applications",
    add_completion=True,
    rich_markup_mode="rich",
)


def versionCallback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"FastAPI Launcher v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=versionCallback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """FastAPI Launcher - Universal CLI for FastAPI applications."""
    pass


@app.command()
def dev(
    app_path: Optional[str] = typer.Option(
        None,
        "--app",
        "-a",
        help="FastAPI app import path (e.g., 'main:app')",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Bind host",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Bind port",
    ),
    reload: bool = typer.Option(
        True,
        "--reload/--no-reload",
        "-r/-R",
        help="Enable auto-reload",
    ),
    reload_dirs: Optional[str] = typer.Option(
        None,
        "--reload-dirs",
        help="Directories to watch for reload (comma-separated)",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Log level",
    ),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Named environment from pyproject.toml (e.g., staging, qa)",
    ),
) -> None:
    """Start development server with auto-reload."""
    reloadDirsList = None
    if reload_dirs:
        reloadDirsList = [d.strip() for d in reload_dirs.split(",")]

    cliArgs = {
        "app": app_path,
        "host": host,
        "port": port,
        "reload": reload,
        "reload_dirs": reloadDirsList,
        "log_level": log_level,
    }

    try:
        launch(cliArgs=cliArgs, mode=RunMode.DEV, envName=env)
    except LaunchError:
        raise typer.Exit(1)
    except KeyboardInterrupt:
        printInfoMessage("Server stopped")


@app.command()
def start(
    app_path: Optional[str] = typer.Option(
        None,
        "--app",
        "-a",
        help="FastAPI app import path",
    ),
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Bind host",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Bind port",
    ),
    workers: int = typer.Option(
        4,
        "--workers",
        "-w",
        help="Number of worker processes",
    ),
    daemon_mode: bool = typer.Option(
        False,
        "--daemon",
        "-d",
        help="Run as daemon (background process)",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Log level",
    ),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Named environment from pyproject.toml (e.g., staging, prod)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server backend (uvicorn/gunicorn)",
    ),
    timeout_graceful_shutdown: Optional[int] = typer.Option(
        None,
        "--timeout-graceful-shutdown",
        help="Graceful shutdown timeout in seconds",
    ),
    max_requests: Optional[int] = typer.Option(
        None,
        "--max-requests",
        help="Max requests per worker before restart (Gunicorn only)",
    ),
) -> None:
    """Start production server."""
    from .enums import ServerBackend

    # Parse server backend
    serverBackend = None
    if server:
        try:
            serverBackend = ServerBackend(server.lower())
        except ValueError:
            printErrorMessage(
                f"Invalid server backend: {server}. Use 'uvicorn' or 'gunicorn'"
            )
            raise typer.Exit(1)

    cliArgs = {
        "app": app_path,
        "host": host,
        "port": port,
        "workers": workers,
        "daemon": daemon_mode,
        "log_level": log_level,
        "server": serverBackend,
        "timeout_graceful_shutdown": timeout_graceful_shutdown,
        "max_requests": max_requests,
    }

    if daemon_mode:
        supported, msg = checkDaemonSupport()
        if not supported:
            printWarningMessage(msg)
        else:
            # Setup logging before daemonizing
            config = loadConfig(cliArgs=cliArgs, envName=env)
            runtimeDir = config.runtimeDir
            if not runtimeDir.is_absolute():
                runtimeDir = Path.cwd() / runtimeDir

            logFile = setupDaemonLogging(runtimeDir)
            pidFile = runtimeDir / "fa.pid"

            printInfoMessage(f"Starting daemon... (PID file: {pidFile})")
            daemonize(pidFile=pidFile, logFile=logFile, workDir=Path.cwd())

    try:
        launch(
            cliArgs=cliArgs, mode=RunMode.PROD, showBanner=not daemon_mode, envName=env
        )
    except LaunchError:
        raise typer.Exit(1)
    except KeyboardInterrupt:
        printInfoMessage("Server stopped")


@app.command()
def stop(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force kill (SIGKILL instead of SIGTERM)",
    ),
    timeout: float = typer.Option(
        10.0,
        "--timeout",
        "-t",
        help="Timeout in seconds before force kill",
    ),
) -> None:
    """Stop running server."""
    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    pidFile = runtimeDir / "fa.pid"
    pid = readPidFile(pidFile)

    if pid is None:
        printWarningMessage("No PID file found. Server may not be running.")
        raise typer.Exit(1)

    if not isProcessRunning(pid):
        printWarningMessage(f"Process {pid} is not running. Cleaning up PID file.")
        removePidFile(pidFile)
        raise typer.Exit(0)

    printInfoMessage(f"Stopping server (PID: {pid})...")

    with createSpinner("Stopping...") as progress:
        progress.add_task("Stopping server...", total=None)

        if terminateProcess(pid, timeout=timeout):
            removePidFile(pidFile)

            # Wait for port to be free
            waitForPortFree(config.port, timeout=5.0)

    printSuccessMessage("Server stopped successfully")


@app.command()
def restart(
    timeout: float = typer.Option(
        10.0,
        "--timeout",
        "-t",
        help="Timeout for stopping server",
    ),
) -> None:
    """Restart server (stop + start)."""
    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    pidFile = runtimeDir / "fa.pid"
    pid = readPidFile(pidFile)

    wasDaemon = False

    if pid and isProcessRunning(pid):
        printInfoMessage("Stopping current server...")
        wasDaemon = True  # Assume daemon if PID file exists

        if terminateProcess(pid, timeout=timeout):
            removePidFile(pidFile)
            waitForPortFree(config.port, timeout=5.0)
            printSuccessMessage("Server stopped")
        else:
            printErrorMessage("Failed to stop server")
            raise typer.Exit(1)

    # Start in the same mode
    printInfoMessage("Starting server...")

    if wasDaemon:
        # Re-daemonize
        logFile = setupDaemonLogging(runtimeDir)
        daemonize(pidFile=pidFile, logFile=logFile, workDir=Path.cwd())

    try:
        launch(mode=config.mode, showBanner=True)
    except LaunchError:
        raise typer.Exit(1)


@app.command()
def status(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed worker status",
    ),
) -> None:
    """Show server status."""
    from .process import getWorkerStatuses

    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    pidFile = runtimeDir / "fa.pid"
    pid = readPidFile(pidFile)

    statusInfo = {
        "running": False,
        "pid": None,
        "host": config.host,
        "port": config.port,
    }

    processInfo = None
    workerStatuses = None

    if pid:
        processStatus = getProcessStatus(pid)
        statusInfo["running"] = processStatus.isRunning
        statusInfo["pid"] = pid

        if processStatus.isRunning:
            processInfo = {
                "uptime": processStatus.uptime,
                "memory_mb": processStatus.memoryMb,
                "cpu_percent": processStatus.cpuPercent,
            }

            # Get worker statuses if verbose
            if verbose:
                workerStatuses = getWorkerStatuses(pid)
    elif isPortInUse(config.port, config.host):
        # Server running but no PID file (started externally)
        portInfo = getPortInfo(config.port)
        statusInfo["running"] = True
        statusInfo["pid"] = portInfo.pid

        # Try to get worker statuses if verbose
        if verbose and portInfo.pid:
            workerStatuses = getWorkerStatuses(portInfo.pid)

    printStatusTable(statusInfo, processInfo, workerStatuses)


@app.command()
def logs(
    lines: int = typer.Option(
        100,
        "--lines",
        "-n",
        help="Number of lines to show",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output",
    ),
    log_type: str = typer.Option(
        "main",
        "--type",
        "-t",
        help="Log type: main, access, error",
    ),
) -> None:
    """View server logs."""
    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    logFiles = getLogFiles(runtimeDir)

    if log_type not in logFiles:
        printErrorMessage(f"Unknown log type: {log_type}")
        printInfoMessage(f"Available types: {', '.join(logFiles.keys())}")
        raise typer.Exit(1)

    logFile = logFiles[log_type]

    if not logFile.exists():
        printWarningMessage(f"Log file not found: {logFile}")
        raise typer.Exit(0)

    try:
        for line in readLogFile(logFile, lines=lines, follow=follow):
            printLogEntry(line, config.logFormat)
    except KeyboardInterrupt:
        pass


@app.command()
def health(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Server host",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Server port",
    ),
    path: Optional[str] = typer.Option(
        None,
        "--path",
        help="Health check endpoint path",
    ),
    timeout: float = typer.Option(
        5.0,
        "--timeout",
        "-t",
        help="Request timeout in seconds",
    ),
) -> None:
    """Check server health."""
    config = loadConfig()

    checkHost = host or config.host
    checkPort = port or config.port
    checkPath = path or config.healthPath

    url = f"http://{checkHost}:{checkPort}{checkPath}"

    result = checkHealth(
        host=checkHost,
        port=checkPort,
        path=checkPath,
        timeout=timeout,
    )

    printHealthResult(result, url)

    if not result.healthy:
        if result.error:
            printErrorMessage(result.error)
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    showConfig()


@app.command()
def check() -> None:
    """Check configuration and dependencies."""
    report = runAllChecks()
    printCheckReport(report)

    if not report.allPassed:
        raise typer.Exit(1)


@app.command()
def clean(
    logs_only: bool = typer.Option(
        False,
        "--logs",
        "-l",
        help="Only clean log files",
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """Clean runtime files (PID, logs)."""
    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    if not runtimeDir.exists():
        printInfoMessage("Runtime directory does not exist. Nothing to clean.")
        raise typer.Exit(0)

    if not confirm:
        confirmClean = typer.confirm("Are you sure you want to clean runtime files?")
        if not confirmClean:
            raise typer.Exit(0)

    cleanedCount = 0

    # Clean logs
    logsCount = cleanLogs(runtimeDir)
    cleanedCount += logsCount
    if logsCount > 0:
        printSuccessMessage(f"Cleaned {logsCount} log file(s)")

    if not logs_only:
        # Clean PID file
        pidFile = runtimeDir / "fa.pid"
        if pidFile.exists():
            # Check if process is running
            pid = readPidFile(pidFile)
            if pid and isProcessRunning(pid):
                printWarningMessage(
                    f"Server is still running (PID: {pid}). Stop it first."
                )
            else:
                pidFile.unlink()
                cleanedCount += 1
                printSuccessMessage("Cleaned PID file")

    if cleanedCount == 0:
        printInfoMessage("Nothing to clean")
    else:
        printSuccessMessage(f"Cleaned {cleanedCount} file(s)")


@app.command(name="init")
def initCmd(
    env: bool = typer.Option(
        False,
        "--env",
        "-e",
        help="Also generate .env.example template",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration",
    ),
) -> None:
    """Initialize FastAPI Launcher configuration in pyproject.toml."""
    from .init import initConfig

    success, message = initConfig(
        projectDir=Path.cwd(),
        force=force,
        generateEnv=env,
    )

    if success:
        printSuccessMessage(message)
    else:
        printWarningMessage(message)
        if not force and "already exists" in message:
            raise typer.Exit(0)
        raise typer.Exit(1)


@app.command(name="run")
def run(
    app_path: Optional[str] = typer.Option(
        None,
        "--app",
        "-a",
        help="FastAPI app import path",
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Bind host",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Bind port",
    ),
) -> None:
    """Smart start - auto-detect dev/prod mode based on environment."""
    from .smartMode import detectEnvironment

    detectedEnv, detectedMode = detectEnvironment()

    printInfoMessage(
        f"Detected environment: {detectedEnv} (mode: {detectedMode.value})"
    )

    cliArgs = {
        "app": app_path,
        "host": host,
        "port": port,
    }

    # Use detected environment if it's a named env
    envName = detectedEnv if detectedEnv not in ("dev", "prod") else None

    try:
        launch(cliArgs=cliArgs, mode=detectedMode, envName=envName)
    except LaunchError:
        raise typer.Exit(1)
    except KeyboardInterrupt:
        printInfoMessage("Server stopped")


@app.command()
def reload() -> None:
    """Trigger hot reload on running server (dev mode only)."""
    import signal

    # Check platform
    if sys.platform == "win32":
        printWarningMessage("Reload command is not supported on Windows")
        raise typer.Exit(1)

    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    pidFile = runtimeDir / "fa.pid"
    pid = readPidFile(pidFile)

    if pid is None:
        printErrorMessage("No server is running (PID file not found)")
        raise typer.Exit(1)

    if not isProcessRunning(pid):
        printErrorMessage(f"Server process {pid} is not running")
        removePidFile(pidFile)
        raise typer.Exit(1)

    # Send SIGHUP signal
    try:
        from .process import sendSignal

        if sendSignal(pid, signal.SIGHUP):
            printSuccessMessage(f"Reload triggered (sent SIGHUP to PID {pid})")
        else:
            printErrorMessage("Failed to send SIGHUP signal")
            raise typer.Exit(1)
    except Exception as e:
        printErrorMessage(f"Failed to trigger reload: {e}")
        raise typer.Exit(1)


@app.command()
def monitor(
    no_tui: bool = typer.Option(
        False,
        "--no-tui",
        help="Use simple CLI output instead of TUI",
    ),
    refresh: float = typer.Option(
        1.0,
        "--refresh",
        "-r",
        help="Refresh interval in seconds",
    ),
) -> None:
    """Real-time monitor for server status (requires textual for TUI)."""
    from .monitor import checkTextualInstalled, runMonitorSimple, runMonitorTui

    # Check if server is running first
    config = loadConfig()
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = Path.cwd() / runtimeDir

    pidFile = runtimeDir / "fa.pid"
    pid = readPidFile(pidFile)

    if pid is None or not isProcessRunning(pid):
        printWarningMessage(
            "Server is not running. Start the server first with 'fa start' or 'fa dev'."
        )

    if no_tui:
        runMonitorSimple(refreshInterval=refresh)
    else:
        if not checkTextualInstalled():
            printWarningMessage(
                "Textual is not installed. Using simple CLI output.\n"
                "For TUI mode, install with: pip install fastapi-launcher[monitor]"
            )
            runMonitorSimple(refreshInterval=refresh)
        else:
            try:
                runMonitorTui()
            except Exception as e:
                printErrorMessage(f"TUI failed: {e}")
                printInfoMessage("Falling back to simple CLI output...")
                runMonitorSimple(refreshInterval=refresh)


if __name__ == "__main__":
    app()
