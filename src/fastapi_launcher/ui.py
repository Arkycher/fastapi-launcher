"""Rich UI components for beautiful terminal output."""

from datetime import timedelta
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .enums import RunMode
from .schemas import LauncherConfig

console = Console()


# Color scheme
COLORS = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "muted": "dim white",
}

# HTTP method colors
METHOD_COLORS = {
    "GET": "green",
    "POST": "yellow",
    "PUT": "blue",
    "PATCH": "magenta",
    "DELETE": "red",
    "HEAD": "cyan",
    "OPTIONS": "dim white",
}


def printStartupPanel(config: LauncherConfig) -> None:
    """Print startup information panel."""
    modeText = "[cyan]Development[/]" if config.mode == RunMode.DEV else "[yellow]Production[/]"
    
    content = Text()
    content.append("FastAPI Launcher\n", style="bold cyan")
    content.append(f"\nMode: {modeText}\n")
    content.append(f"App: ", style="dim")
    content.append(f"{config.app or 'auto-discover'}\n", style="cyan")
    content.append(f"URL: ", style="dim")
    content.append(f"http://{config.host}:{config.port}\n", style="bold green")
    
    if config.mode == RunMode.DEV and config.reload:
        content.append("\n✓ Auto-reload enabled", style="dim green")
    elif config.mode == RunMode.PROD:
        content.append(f"\n⚡ Workers: {config.workers}", style="dim yellow")
    
    panel = Panel(
        content,
        title="[bold]🚀 Starting Server[/]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def printStatusTable(
    status: dict[str, Any],
    processInfo: Optional[dict[str, Any]] = None,
    workerStatuses: Optional[list] = None,
) -> None:
    """Print status information as a table."""
    table = Table(
        title="Server Status",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    
    table.add_column("Property", style="dim")
    table.add_column("Value")
    
    # Status indicator
    isRunning = status.get("running", False)
    statusText = Text("● Running", style="bold green") if isRunning else Text("○ Stopped", style="dim red")
    table.add_row("Status", statusText)
    
    if isRunning:
        table.add_row("PID", str(status.get("pid", "N/A")))
        table.add_row("URL", f"http://{status.get('host', '127.0.0.1')}:{status.get('port', 8000)}")
        
        if processInfo:
            if processInfo.get("uptime"):
                table.add_row("Uptime", _formatUptime(processInfo["uptime"]))
            if processInfo.get("memory_mb"):
                table.add_row("Memory", f"{processInfo['memory_mb']:.1f} MB")
            if processInfo.get("cpu_percent") is not None:
                table.add_row("CPU", f"{processInfo['cpu_percent']:.1f}%")
        
        if workerStatuses:
            table.add_row("Workers", str(len(workerStatuses)))
    
    console.print(table)
    
    # Print worker status table if available
    if workerStatuses:
        printWorkerStatusTable(workerStatuses)


def printWorkerStatusTable(workerStatuses: list) -> None:
    """Print worker status information as a table."""
    if not workerStatuses:
        console.print("[dim]No worker processes found[/dim]")
        return
    
    table = Table(
        title="Worker Status",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Status")
    table.add_column("CPU %", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Uptime")
    
    for worker in workerStatuses:
        # Status indicator
        if worker.status == "running":
            statusText = Text("● running", style="green")
        elif worker.status == "idle":
            statusText = Text("○ idle", style="dim")
        else:
            statusText = Text(f"◐ {worker.status}", style="yellow")
        
        # Format uptime
        uptimeStr = _formatUptime(worker.uptime) if worker.uptime else "N/A"
        
        table.add_row(
            str(worker.pid),
            statusText,
            f"{worker.cpuPercent:.1f}%",
            f"{worker.memoryMb:.1f} MB",
            uptimeStr,
        )
    
    console.print(table)


def _formatUptime(uptime: timedelta) -> str:
    """Format uptime duration."""
    totalSeconds = int(uptime.total_seconds())
    
    days, remainder = divmod(totalSeconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)


def printErrorPanel(title: str, message: str, suggestions: Optional[list[str]] = None) -> None:
    """Print an error panel with optional suggestions."""
    content = Text()
    content.append(message, style="red")
    
    if suggestions:
        content.append("\n\nSuggestions:", style="bold yellow")
        for suggestion in suggestions:
            content.append(f"\n  • {suggestion}", style="yellow")
    
    panel = Panel(
        content,
        title=f"[bold red]❌ {title}[/]",
        border_style="red",
        padding=(1, 2),
    )
    console.print(panel)


def printSuccessMessage(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/] {message}")


def printWarningMessage(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/] {message}")


def printInfoMessage(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/] {message}")


def printErrorMessage(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/] {message}")


def createSpinner(message: str) -> Progress:
    """Create a spinner progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def printConfigTable(config: dict[str, Any], title: str = "Configuration") -> None:
    """Print configuration as a table."""
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Source", style="dim")
    
    for key, value in config.items():
        if isinstance(value, bool):
            valueStr = "[green]true[/]" if value else "[red]false[/]"
        elif value is None:
            valueStr = "[dim]not set[/]"
        else:
            valueStr = str(value)
        
        table.add_row(key, valueStr, "")
    
    console.print(table)


def colorizeHttpMethod(method: str) -> str:
    """Get Rich markup for HTTP method."""
    color = METHOD_COLORS.get(method.upper(), "white")
    return f"[{color}]{method:7}[/]"


def colorizeStatusCode(code: int) -> str:
    """Get Rich markup for HTTP status code."""
    if code < 200:
        color = "dim"
    elif code < 300:
        color = "green"
    elif code < 400:
        color = "yellow"
    elif code < 500:
        color = "red"
    else:
        color = "bold red"
    return f"[{color}]{code}[/]"


def printHealthStatus(healthy: bool, url: str, responseTime: Optional[float] = None) -> None:
    """Print health check status."""
    if healthy:
        status = Text("● Healthy", style="bold green")
        timeStr = f" ({responseTime:.0f}ms)" if responseTime else ""
        console.print(f"{status} {url}{timeStr}")
    else:
        status = Text("○ Unhealthy", style="bold red")
        console.print(f"{status} {url}")


def printPortConflict(port: int, processName: Optional[str], pid: Optional[int]) -> None:
    """Print port conflict information."""
    printErrorPanel(
        "Port Already in Use",
        f"Port {port} is already in use.",
        suggestions=[
            f"Kill the process: fa stop --force" if pid else None,
            f"Use a different port: fa dev --port {port + 1}",
            f"Process: {processName} (PID: {pid})" if processName and pid else None,
        ],
    )


def printAccessLogEntry(
    method: str,
    path: str,
    statusCode: int,
    responseTime: float,
    isSlow: bool = False,
) -> None:
    """Print a formatted access log entry."""
    methodStr = colorizeHttpMethod(method)
    statusStr = colorizeStatusCode(statusCode)
    timeColor = "red" if isSlow else "dim"
    slowMarker = " [bold red][SLOW][/]" if isSlow else ""
    
    console.print(
        f"{methodStr} {path:40} {statusStr} [{timeColor}]{responseTime:.3f}s[/]{slowMarker}"
    )
