"""Configuration schema models."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..enums import LogFormat, RunMode, ServerBackend


class UvicornConfig(BaseModel):
    """Uvicorn-specific configuration."""

    host: str = Field(default="127.0.0.1", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    reloadDirs: list[str] = Field(
        default_factory=list,
        alias="reload_dirs",
        description="Directories to watch for reload",
    )
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    logLevel: str = Field(default="info", alias="log_level", description="Log level")
    accessLog: bool = Field(
        default=True, alias="access_log", description="Enable access log"
    )
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")

    model_config = {"populate_by_name": True}


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration (dev/prod/custom)."""

    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    reload: Optional[bool] = None
    workers: Optional[int] = Field(default=None, ge=1)
    logLevel: Optional[str] = Field(default=None, alias="log_level")
    logFormat: Optional[LogFormat] = Field(default=None, alias="log_format")
    daemon: Optional[bool] = None
    accessLog: Optional[bool] = Field(default=None, alias="access_log")
    server: Optional[ServerBackend] = None
    timeoutGracefulShutdown: Optional[int] = Field(
        default=None, ge=0, alias="timeout_graceful_shutdown"
    )
    maxRequests: Optional[int] = Field(default=None, ge=0, alias="max_requests")
    maxRequestsJitter: Optional[int] = Field(
        default=None, ge=0, alias="max_requests_jitter"
    )
    workerClass: Optional[str] = Field(default=None, alias="worker_class")

    model_config = {"populate_by_name": True}


class LauncherConfig(BaseModel):
    """Main launcher configuration model."""

    # App configuration
    app: Optional[str] = Field(
        default=None, description="FastAPI app import path (e.g., 'main:app')"
    )
    appDir: Optional[Path] = Field(
        default=None, alias="app_dir", description="Application directory"
    )

    # Server configuration
    host: str = Field(default="127.0.0.1", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")

    # Run mode
    mode: RunMode = Field(default=RunMode.DEV, description="Run mode")

    # Server backend
    server: ServerBackend = Field(
        default=ServerBackend.UVICORN, description="Server backend (uvicorn/gunicorn)"
    )

    # Reload settings (dev mode)
    reload: bool = Field(default=False, description="Enable auto-reload")
    reloadDirs: list[str] = Field(
        default_factory=list,
        alias="reload_dirs",
        description="Directories to watch for reload",
    )

    # Production settings
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    daemon: bool = Field(default=False, description="Run as daemon (Unix only)")

    # Graceful shutdown
    timeoutGracefulShutdown: int = Field(
        default=10,
        ge=0,
        alias="timeout_graceful_shutdown",
        description="Graceful shutdown timeout in seconds",
    )

    # Gunicorn-specific settings
    maxRequests: int = Field(
        default=0,
        ge=0,
        alias="max_requests",
        description="Max requests per worker before restart (0 = disable)",
    )
    maxRequestsJitter: int = Field(
        default=0,
        ge=0,
        alias="max_requests_jitter",
        description="Random jitter for max_requests",
    )
    workerClass: str = Field(
        default="uvicorn.workers.UvicornWorker",
        alias="worker_class",
        description="Gunicorn worker class",
    )

    # Logging
    logLevel: str = Field(default="info", alias="log_level", description="Log level")
    logFormat: LogFormat = Field(
        default=LogFormat.PRETTY, alias="log_format", description="Log output format"
    )
    accessLog: bool = Field(
        default=True, alias="access_log", description="Enable access log"
    )

    # Runtime directories
    runtimeDir: Path = Field(
        default=Path("runtime"), alias="runtime_dir", description="Runtime directory"
    )

    # Health check
    healthPath: str = Field(
        default="/health", alias="health_path", description="Health check endpoint path"
    )
    healthTimeout: int = Field(
        default=5,
        ge=1,
        alias="health_timeout",
        description="Health check timeout in seconds",
    )

    # Request logging
    slowRequestThreshold: float = Field(
        default=1.0,
        ge=0,
        alias="slow_request_threshold",
        description="Slow request threshold in seconds",
    )
    excludePaths: list[str] = Field(
        default_factory=lambda: ["/health", "/metrics"],
        alias="exclude_paths",
        description="Paths to exclude from access logging",
    )

    # Environment-specific overrides (legacy dev/prod)
    dev: Optional[EnvironmentConfig] = Field(
        default=None, description="Development environment overrides"
    )
    prod: Optional[EnvironmentConfig] = Field(
        default=None, description="Production environment overrides"
    )

    # Named environments (new: envs.staging, envs.qa, etc.)
    envs: Optional[dict[str, EnvironmentConfig]] = Field(
        default=None, description="Named environment configurations"
    )

    model_config = {"populate_by_name": True}

    def getEffectiveConfig(self, envName: Optional[str] = None) -> "LauncherConfig":
        """Get configuration with environment-specific overrides applied.

        Args:
            envName: Named environment to use (e.g., 'staging', 'qa').
                    If None, uses dev/prod based on mode.
        """
        # Determine which environment config to use
        envConfig: Optional[EnvironmentConfig] = None

        if envName and self.envs:
            envConfig = self.envs.get(envName)
        elif not envName:
            # Fall back to legacy dev/prod
            envConfig = self.dev if self.mode == RunMode.DEV else self.prod

        if envConfig is None:
            return self

        # Create a copy with overrides
        data = self.model_dump(by_alias=False, exclude={"dev", "prod", "envs"})

        # Apply all non-None overrides
        if envConfig.host is not None:
            data["host"] = envConfig.host
        if envConfig.port is not None:
            data["port"] = envConfig.port
        if envConfig.reload is not None:
            data["reload"] = envConfig.reload
        if envConfig.workers is not None:
            data["workers"] = envConfig.workers
        if envConfig.logLevel is not None:
            data["logLevel"] = envConfig.logLevel
        if envConfig.logFormat is not None:
            data["logFormat"] = envConfig.logFormat
        if envConfig.daemon is not None:
            data["daemon"] = envConfig.daemon
        if envConfig.accessLog is not None:
            data["accessLog"] = envConfig.accessLog
        if envConfig.server is not None:
            data["server"] = envConfig.server
        if envConfig.timeoutGracefulShutdown is not None:
            data["timeoutGracefulShutdown"] = envConfig.timeoutGracefulShutdown
        if envConfig.maxRequests is not None:
            data["maxRequests"] = envConfig.maxRequests
        if envConfig.maxRequestsJitter is not None:
            data["maxRequestsJitter"] = envConfig.maxRequestsJitter
        if envConfig.workerClass is not None:
            data["workerClass"] = envConfig.workerClass

        return LauncherConfig(**data)

    def toUvicornKwargs(self) -> dict[str, Any]:
        """Convert config to uvicorn.run() keyword arguments."""
        kwargs: dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "log_level": self.logLevel.lower(),
            "access_log": self.accessLog,
        }

        if self.mode == RunMode.DEV:
            kwargs["reload"] = self.reload
            if self.reloadDirs:
                kwargs["reload_dirs"] = self.reloadDirs
        else:
            # Production mode
            if self.workers > 1:
                kwargs["workers"] = self.workers

        # Add graceful shutdown timeout
        if self.timeoutGracefulShutdown > 0:
            kwargs["timeout_graceful_shutdown"] = self.timeoutGracefulShutdown

        return kwargs

    def toGunicornConfig(self) -> dict[str, Any]:
        """Convert config to Gunicorn configuration dict."""
        config: dict[str, Any] = {
            "bind": f"{self.host}:{self.port}",
            "workers": self.workers,
            "worker_class": self.workerClass,
            "accesslog": "-" if self.accessLog else None,
            "errorlog": "-",
            "loglevel": self.logLevel.lower(),
            "graceful_timeout": self.timeoutGracefulShutdown,
        }

        if self.maxRequests > 0:
            config["max_requests"] = self.maxRequests
            config["max_requests_jitter"] = self.maxRequestsJitter

        return config
