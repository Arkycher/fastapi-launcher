"""Access log handling and formatting."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .enums import LogFormat
from .schemas import AccessLogEntry


def parseAccessLogLine(line: str) -> Optional[AccessLogEntry]:
    """
    Parse a uvicorn access log line into AccessLogEntry.
    
    Standard uvicorn format: 
    INFO:     127.0.0.1:51234 - "GET /api/users HTTP/1.1" 200
    
    Args:
        line: Raw log line
    
    Returns:
        Parsed AccessLogEntry or None if parsing fails
    """
    # Pattern for uvicorn access log
    pattern = r'(\S+)\s+-\s+"(\w+)\s+(\S+)\s+HTTP/[\d.]+"[\s]+(\d+)'
    
    match = re.search(pattern, line)
    if not match:
        return None
    
    clientIp = match.group(1).split(":")[0] if ":" in match.group(1) else match.group(1)
    method = match.group(2)
    path = match.group(3)
    statusCode = int(match.group(4))
    
    # Extract query string if present
    queryString = None
    if "?" in path:
        path, queryString = path.split("?", 1)
    
    return AccessLogEntry(
        method=method,
        path=path,
        queryString=queryString,
        statusCode=statusCode,
        responseTime=0.0,  # Not available in standard uvicorn log
        clientIp=clientIp,
    )


def formatAccessLogEntry(
    entry: AccessLogEntry,
    logFormat: LogFormat = LogFormat.PRETTY,
) -> str:
    """
    Format access log entry for output.
    
    Args:
        entry: Access log entry
        logFormat: Output format
    
    Returns:
        Formatted log string
    """
    if logFormat == LogFormat.JSON:
        return entry.toJsonStr()
    else:
        return entry.toPrettyStr()


def shouldLogRequest(path: str, excludePaths: list[str]) -> bool:
    """
    Check if a request should be logged.
    
    Args:
        path: Request path
        excludePaths: List of paths to exclude
    
    Returns:
        True if should log, False otherwise
    """
    for excludePath in excludePaths:
        if path == excludePath or path.startswith(excludePath + "/"):
            return False
    return True


def isSlowRequest(responseTime: float, threshold: float = 1.0) -> bool:
    """
    Check if a request is considered slow.
    
    Args:
        responseTime: Response time in seconds
        threshold: Slow request threshold in seconds
    
    Returns:
        True if slow, False otherwise
    """
    return responseTime >= threshold


def writeAccessLog(
    entry: AccessLogEntry,
    logFile: Path,
    logFormat: LogFormat = LogFormat.PRETTY,
) -> None:
    """
    Write access log entry to file.
    
    Args:
        entry: Access log entry
        logFile: Path to log file
        logFormat: Output format
    """
    logFile.parent.mkdir(parents=True, exist_ok=True)
    
    formattedLine = formatAccessLogEntry(entry, logFormat)
    
    with open(logFile, "a") as f:
        f.write(formattedLine + "\n")


def createAccessLogEntry(
    method: str,
    path: str,
    statusCode: int,
    responseTime: float,
    clientIp: Optional[str] = None,
    userAgent: Optional[str] = None,
    contentLength: Optional[int] = None,
    slowThreshold: float = 1.0,
    queryString: Optional[str] = None,
) -> AccessLogEntry:
    """
    Create an access log entry.
    
    Args:
        method: HTTP method
        path: Request path
        statusCode: HTTP status code
        responseTime: Response time in seconds
        clientIp: Client IP address
        userAgent: User agent string
        contentLength: Response content length
        slowThreshold: Threshold for marking slow requests
        queryString: Query string
    
    Returns:
        AccessLogEntry
    """
    return AccessLogEntry(
        timestamp=datetime.now(),
        method=method,
        path=path,
        queryString=queryString,
        statusCode=statusCode,
        responseTime=responseTime,
        clientIp=clientIp,
        userAgent=userAgent,
        contentLength=contentLength,
        isSlow=isSlowRequest(responseTime, slowThreshold),
    )


def readAccessLog(
    logFile: Path,
    lines: int = 100,
    filterMethod: Optional[str] = None,
    filterPath: Optional[str] = None,
    filterStatus: Optional[int] = None,
    slowOnly: bool = False,
) -> list[AccessLogEntry]:
    """
    Read and filter access log entries.
    
    Args:
        logFile: Path to access log file
        lines: Number of lines to read
        filterMethod: Filter by HTTP method
        filterPath: Filter by path (prefix match)
        filterStatus: Filter by status code
        slowOnly: Only return slow requests
    
    Returns:
        List of matching AccessLogEntry objects
    """
    if not logFile.exists():
        return []
    
    entries: list[AccessLogEntry] = []
    
    with open(logFile, "r") as f:
        allLines = f.readlines()
        
        for line in allLines[-lines:]:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as JSON first
            try:
                data = json.loads(line)
                entry = AccessLogEntry(**data)
            except (json.JSONDecodeError, ValueError):
                # Try to parse as pretty format
                entry = parseAccessLogLine(line)
                if entry is None:
                    continue
            
            # Apply filters
            if filterMethod and entry.method.upper() != filterMethod.upper():
                continue
            if filterPath and not entry.path.startswith(filterPath):
                continue
            if filterStatus and entry.statusCode != filterStatus:
                continue
            if slowOnly and not entry.isSlow:
                continue
            
            entries.append(entry)
    
    return entries
