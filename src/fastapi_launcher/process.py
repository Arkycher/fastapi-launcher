"""Process management utilities."""

import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import psutil


@dataclass
class ProcessStatus:
    """Process status information."""

    pid: int
    isRunning: bool
    name: Optional[str] = None
    cmdline: Optional[str] = None
    memoryMb: Optional[float] = None
    cpuPercent: Optional[float] = None
    startTime: Optional[datetime] = None
    uptime: Optional[timedelta] = None


def writePidFile(pidPath: Path, pid: Optional[int] = None) -> None:
    """
    Write PID to file.
    
    Args:
        pidPath: Path to PID file
        pid: Process ID (defaults to current process)
    """
    if pid is None:
        pid = os.getpid()
    
    pidPath.parent.mkdir(parents=True, exist_ok=True)
    pidPath.write_text(str(pid))


def readPidFile(pidPath: Path) -> Optional[int]:
    """
    Read PID from file.
    
    Args:
        pidPath: Path to PID file
    
    Returns:
        PID if file exists and valid, None otherwise
    """
    if not pidPath.exists():
        return None
    
    try:
        content = pidPath.read_text().strip()
        return int(content)
    except (ValueError, IOError):
        return None


def removePidFile(pidPath: Path) -> bool:
    """
    Remove PID file.
    
    Args:
        pidPath: Path to PID file
    
    Returns:
        True if file was removed, False if it didn't exist
    """
    if pidPath.exists():
        pidPath.unlink()
        return True
    return False


def isProcessRunning(pid: int) -> bool:
    """
    Check if a process is running.
    
    Args:
        pid: Process ID
    
    Returns:
        True if process is running, False otherwise
    """
    if pid <= 0:
        return False
    
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def getProcessStatus(pid: int) -> ProcessStatus:
    """
    Get detailed status of a process.
    
    Args:
        pid: Process ID
    
    Returns:
        ProcessStatus with process details
    """
    status = ProcessStatus(pid=pid, isRunning=False)
    
    try:
        proc = psutil.Process(pid)
        status.isRunning = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        
        if status.isRunning:
            status.name = proc.name()
            try:
                status.cmdline = " ".join(proc.cmdline())
            except (psutil.AccessDenied, psutil.ZombieProcess):
                status.cmdline = None
            
            try:
                memInfo = proc.memory_info()
                status.memoryMb = memInfo.rss / (1024 * 1024)
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            try:
                status.cpuPercent = proc.cpu_percent(interval=0.1)
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            try:
                status.startTime = datetime.fromtimestamp(proc.create_time())
                status.uptime = datetime.now() - status.startTime
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        status.isRunning = False
    
    return status


def sendSignal(pid: int, sig: signal.Signals) -> bool:
    """
    Send a signal to a process.
    
    Args:
        pid: Process ID
        sig: Signal to send
    
    Returns:
        True if signal was sent, False otherwise
    """
    try:
        os.kill(pid, sig)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def terminateProcess(pid: int, timeout: float = 5.0) -> bool:
    """
    Gracefully terminate a process (SIGTERM, then SIGKILL if needed).
    
    Args:
        pid: Process ID
        timeout: Seconds to wait before force kill
    
    Returns:
        True if process was terminated, False otherwise
    """
    if not isProcessRunning(pid):
        return True
    
    try:
        proc = psutil.Process(pid)
        
        # Send SIGTERM
        proc.terminate()
        
        try:
            proc.wait(timeout=timeout)
            return True
        except psutil.TimeoutExpired:
            # Force kill
            proc.kill()
            try:
                proc.wait(timeout=3)
                return True
            except psutil.TimeoutExpired:
                return False
                
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return not isProcessRunning(pid)


def killProcess(pid: int) -> bool:
    """
    Force kill a process (SIGKILL).
    
    Args:
        pid: Process ID
    
    Returns:
        True if process was killed, False otherwise
    """
    if not isProcessRunning(pid):
        return True
    
    try:
        proc = psutil.Process(pid)
        proc.kill()
        proc.wait(timeout=3)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        return not isProcessRunning(pid)


def waitForExit(pid: int, timeout: float = 30.0) -> bool:
    """
    Wait for a process to exit.
    
    Args:
        pid: Process ID
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if process exited, False if timeout
    """
    try:
        proc = psutil.Process(pid)
        proc.wait(timeout=timeout)
        return True
    except psutil.TimeoutExpired:
        return False
    except psutil.NoSuchProcess:
        return True


def getChildProcesses(pid: int) -> list[int]:
    """
    Get child process IDs.
    
    Args:
        pid: Parent process ID
    
    Returns:
        List of child PIDs
    """
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=True)
        return [child.pid for child in children]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return []


def terminateProcessTree(pid: int, timeout: float = 5.0) -> bool:
    """
    Terminate a process and all its children.
    
    Args:
        pid: Process ID
        timeout: Seconds to wait before force kill
    
    Returns:
        True if all processes were terminated
    """
    if not isProcessRunning(pid):
        return True
    
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=True)
        
        # Terminate children first
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Terminate parent
        proc.terminate()
        
        # Wait for all
        gone, alive = psutil.wait_procs([proc] + children, timeout=timeout)
        
        # Force kill survivors
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return len(alive) == 0 or all(not p.is_running() for p in alive)
        
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return not isProcessRunning(pid)


def registerSignalHandlers(
    onTerminate: Optional[callable] = None,
    onInterrupt: Optional[callable] = None,
) -> None:
    """
    Register signal handlers for graceful shutdown.
    
    Args:
        onTerminate: Handler for SIGTERM
        onInterrupt: Handler for SIGINT (Ctrl+C)
    """
    def defaultHandler(signum: int, frame: any) -> None:
        sys.exit(0)
    
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, onTerminate or defaultHandler)
    
    signal.signal(signal.SIGINT, onInterrupt or defaultHandler)


@dataclass
class WorkerStatus:
    """Worker process status information."""

    pid: int
    cpuPercent: float
    memoryMb: float
    requestsHandled: int  # Not always available
    status: str  # running/idle/starting
    uptime: Optional[timedelta] = None


def getWorkerStatuses(mainPid: int) -> list[WorkerStatus]:
    """
    Get status information for all worker processes.
    
    Args:
        mainPid: Main/master process ID
    
    Returns:
        List of WorkerStatus for each worker
    """
    workers: list[WorkerStatus] = []
    
    try:
        mainProc = psutil.Process(mainPid)
        children = mainProc.children(recursive=True)
        
        for child in children:
            try:
                # Get worker process info
                cpuPercent = child.cpu_percent(interval=0.1)
                memInfo = child.memory_info()
                memoryMb = memInfo.rss / (1024 * 1024)
                
                # Determine status based on CPU usage
                if cpuPercent > 0.5:
                    status = "running"
                else:
                    status = "idle"
                
                # Calculate uptime
                try:
                    startTime = datetime.fromtimestamp(child.create_time())
                    uptime = datetime.now() - startTime
                except Exception:
                    uptime = None
                
                workers.append(WorkerStatus(
                    pid=child.pid,
                    cpuPercent=cpuPercent,
                    memoryMb=memoryMb,
                    requestsHandled=0,  # Not available without app instrumentation
                    status=status,
                    uptime=uptime,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    
    return workers


def getMasterAndWorkerStatus(pid: int) -> tuple[ProcessStatus, list[WorkerStatus]]:
    """
    Get master process status and all worker statuses.
    
    Args:
        pid: Master/main process ID
    
    Returns:
        Tuple of (master_status, worker_statuses)
    """
    masterStatus = getProcessStatus(pid)
    workerStatuses = getWorkerStatuses(pid) if masterStatus.isRunning else []
    
    return masterStatus, workerStatuses
