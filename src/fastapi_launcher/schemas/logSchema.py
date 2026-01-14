"""Log-related schema models."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..enums import LogFormat


class LogConfig(BaseModel):
    """Logging configuration."""

    logDir: Path = Field(default=Path("runtime/logs"), alias="log_dir")
    logFile: str = Field(default="fa.log", alias="log_file")
    accessLogFile: str = Field(default="access.log", alias="access_log_file")
    errorLogFile: str = Field(default="error.log", alias="error_log_file")
    logFormat: LogFormat = Field(default=LogFormat.PRETTY, alias="log_format")
    maxBytes: int = Field(default=10 * 1024 * 1024, alias="max_bytes")  # 10MB
    backupCount: int = Field(default=5, alias="backup_count")

    model_config = {"populate_by_name": True}


class AccessLogEntry(BaseModel):
    """Access log entry model."""

    timestamp: datetime = Field(default_factory=datetime.now)
    method: str = Field(description="HTTP method")
    path: str = Field(description="Request path")
    queryString: Optional[str] = Field(default=None, alias="query_string")
    statusCode: int = Field(alias="status_code", description="HTTP status code")
    responseTime: float = Field(
        alias="response_time", description="Response time in seconds"
    )
    clientIp: Optional[str] = Field(default=None, alias="client_ip")
    userAgent: Optional[str] = Field(default=None, alias="user_agent")
    contentLength: Optional[int] = Field(default=None, alias="content_length")
    isSlow: bool = Field(
        default=False, alias="is_slow", description="Whether this is a slow request"
    )

    model_config = {"populate_by_name": True}

    def toPrettyStr(self) -> str:
        """Format log entry for pretty output."""
        slowMarker = " [SLOW]" if self.isSlow else ""
        timeStr = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"{timeStr} | {self.method:7} {self.path} | "
            f"{self.statusCode} | {self.responseTime:.3f}s{slowMarker}"
        )

    def toJsonStr(self) -> str:
        """Format log entry for JSON output."""
        return self.model_dump_json(by_alias=True)
