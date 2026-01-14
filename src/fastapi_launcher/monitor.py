"""Real-time monitoring module with TUI support."""

import time
from datetime import timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from .config import loadConfig
from .process import (
    ProcessStatus,
    WorkerStatus,
    getProcessStatus,
    getWorkerStatuses,
    isProcessRunning,
    readPidFile,
)


console = Console()


def _formatUptime(uptime: Optional[timedelta]) -> str:
    """Format uptime duration."""
    if uptime is None:
        return "N/A"

    totalSeconds = int(uptime.total_seconds())

    days, remainder = divmod(totalSeconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def _buildStatusTable(
    masterStatus: ProcessStatus,
    workerStatuses: list[WorkerStatus],
    config: any,
) -> Table:
    """Build the status table for display."""
    table = Table(
        title="FastAPI Launcher Monitor",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=True,
    )

    table.add_column("Property", style="dim", width=15)
    table.add_column("Value", width=50)

    # Status indicator
    if masterStatus.isRunning:
        statusText = Text("● Running", style="bold green")
    else:
        statusText = Text("○ Stopped", style="dim red")

    table.add_row("Status", statusText)
    table.add_row("PID", str(masterStatus.pid))
    table.add_row("URL", f"http://{config.host}:{config.port}")
    table.add_row("Uptime", _formatUptime(masterStatus.uptime))

    if masterStatus.memoryMb:
        table.add_row("Memory", f"{masterStatus.memoryMb:.1f} MB")
    if masterStatus.cpuPercent is not None:
        table.add_row("CPU", f"{masterStatus.cpuPercent:.1f}%")

    table.add_row("Workers", str(len(workerStatuses)))

    return table


def _buildWorkerTable(workerStatuses: list[WorkerStatus]) -> Table:
    """Build the worker status table."""
    table = Table(
        title="Workers",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=True,
    )

    table.add_column("PID", justify="right", width=8)
    table.add_column("Status", width=10)
    table.add_column("CPU %", justify="right", width=8)
    table.add_column("Memory", justify="right", width=10)
    table.add_column("Uptime", width=15)

    for worker in workerStatuses:
        if worker.status == "running":
            statusText = Text("● running", style="green")
        elif worker.status == "idle":
            statusText = Text("○ idle", style="dim")
        else:
            statusText = Text(f"◐ {worker.status}", style="yellow")

        table.add_row(
            str(worker.pid),
            statusText,
            f"{worker.cpuPercent:.1f}%",
            f"{worker.memoryMb:.1f} MB",
            _formatUptime(worker.uptime),
        )

    if not workerStatuses:
        table.add_row("-", Text("No workers", style="dim"), "-", "-", "-")

    return table


def runMonitorSimple(
    projectDir: Optional[Path] = None,
    refreshInterval: float = 1.0,
) -> None:
    """Run simple CLI monitor (fallback mode).

    Args:
        projectDir: Project directory
        refreshInterval: Refresh interval in seconds
    """
    if projectDir is None:
        projectDir = Path.cwd()

    config = loadConfig(projectDir=projectDir)
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = projectDir / runtimeDir

    pidFile = runtimeDir / "fa.pid"

    console.print("[bold cyan]FastAPI Launcher Monitor[/bold cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    def generateTables():
        pid = readPidFile(pidFile)

        if pid is None or not isProcessRunning(pid):
            return Text("Server is not running", style="dim red")

        masterStatus = getProcessStatus(pid)
        workerStatuses = getWorkerStatuses(pid)

        from rich.console import Group

        return Group(
            _buildStatusTable(masterStatus, workerStatuses, config),
            "",
            _buildWorkerTable(workerStatuses),
        )

    try:
        with Live(
            generateTables(), refresh_per_second=1 / refreshInterval, console=console
        ) as live:
            while True:
                time.sleep(refreshInterval)
                live.update(generateTables())
    except KeyboardInterrupt:
        console.print("\n[dim]Monitor stopped[/dim]")


def runMonitorTui(projectDir: Optional[Path] = None) -> None:
    """Run TUI monitor using Textual.

    Args:
        projectDir: Project directory
    """
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container
        from textual.widgets import Footer, Header, Static
    except ImportError:
        raise ImportError(
            "Textual is required for TUI monitor. "
            "Install with: pip install fastapi-launcher[monitor]"
        )

    if projectDir is None:
        projectDir = Path.cwd()

    config = loadConfig(projectDir=projectDir)
    runtimeDir = config.runtimeDir
    if not runtimeDir.is_absolute():
        runtimeDir = projectDir / runtimeDir

    pidFile = runtimeDir / "fa.pid"

    class StatusWidget(Static):
        """Widget to display server status."""

        def __init__(self):
            super().__init__()
            self.pid = None

        def on_mount(self) -> None:
            self.set_interval(1.0, self.refresh_status)

        def refresh_status(self) -> None:
            self.pid = readPidFile(pidFile)
            self.refresh()

        def render(self) -> str:
            if self.pid is None or not isProcessRunning(self.pid):
                return "[red]● Server is not running[/red]"

            status = getProcessStatus(self.pid)

            lines = [
                "[green]● Running[/green]",
                f"PID: {status.pid}",
                f"URL: http://{config.host}:{config.port}",
                f"Uptime: {_formatUptime(status.uptime)}",
            ]

            if status.memoryMb:
                lines.append(f"Memory: {status.memoryMb:.1f} MB")
            if status.cpuPercent is not None:
                lines.append(f"CPU: {status.cpuPercent:.1f}%")

            return "\n".join(lines)

    class WorkersWidget(Static):
        """Widget to display worker status."""

        def __init__(self):
            super().__init__()
            self.pid = None

        def on_mount(self) -> None:
            self.set_interval(1.0, self.refresh_workers)

        def refresh_workers(self) -> None:
            self.pid = readPidFile(pidFile)
            self.refresh()

        def render(self) -> str:
            if self.pid is None or not isProcessRunning(self.pid):
                return "[dim]No workers[/dim]"

            workers = getWorkerStatuses(self.pid)

            if not workers:
                return "[dim]No worker processes[/dim]"

            lines = [f"[bold]Workers ({len(workers)})[/bold]", ""]

            for w in workers:
                status = "●" if w.status == "running" else "○"
                lines.append(
                    f"{status} PID {w.pid}: {w.cpuPercent:.1f}% CPU, {w.memoryMb:.1f} MB"
                )

            return "\n".join(lines)

    class MonitorApp(App):
        """FastAPI Launcher Monitor TUI Application."""

        TITLE = "FastAPI Launcher Monitor"

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
        ]

        CSS = """
        Screen {
            layout: vertical;
        }
        
        #status {
            height: auto;
            min-height: 8;
            padding: 1;
            border: solid green;
            margin: 1;
        }
        
        #workers {
            height: auto;
            min-height: 5;
            padding: 1;
            border: solid cyan;
            margin: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Container(
                StatusWidget(id="status"),
                WorkersWidget(id="workers"),
            )
            yield Footer()

        def action_refresh(self) -> None:
            self.query_one("#status", StatusWidget).refresh_status()
            self.query_one("#workers", WorkersWidget).refresh_workers()

    app = MonitorApp()
    app.run()


def checkTextualInstalled() -> bool:
    """Check if Textual is installed."""
    try:
        import importlib.util

        return importlib.util.find_spec("textual") is not None
    except Exception:
        return False
