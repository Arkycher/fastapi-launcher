"""Configuration schema models."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..enums import LogFormat, RunMode


class UvicornConfig(BaseModel):
    """Uvicorn-specific configuration."""

    host: str = Field(default="127.0.0.1", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    reloadDirs: list[str] = Field(
        default_factory=list, alias="reload_dirs", description="Directories to watch for reload"
    )
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    logLevel: str = Field(default="info", alias="log_level", description="Log level")
    accessLog: bool = Field(default=True, alias="access_log", description="Enable access log")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    
    model_config = {"populate_by_name": True}


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration (dev/prod)."""

    reload: Optional[bool] = None
    workers: Optional[int] = Field(default=None, ge=1)
    logLevel: Optional[str] = Field(default=None, alias="log_level")
    logFormat: Optional[LogFormat] = Field(default=None, alias="log_format")
    
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
    
    # Reload settings (dev mode)
    reload: bool = Field(default=False, description="Enable auto-reload")
    reloadDirs: list[str] = Field(
        default_factory=list, alias="reload_dirs", description="Directories to watch for reload"
    )
    
    # Production settings
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    daemon: bool = Field(default=False, description="Run as daemon (Unix only)")
    
    # Logging
    logLevel: str = Field(default="info", alias="log_level", description="Log level")
    logFormat: LogFormat = Field(
        default=LogFormat.PRETTY, alias="log_format", description="Log output format"
    )
    accessLog: bool = Field(default=True, alias="access_log", description="Enable access log")
    
    # Runtime directories
    runtimeDir: Path = Field(
        default=Path("runtime"), alias="runtime_dir", description="Runtime directory"
    )
    
    # Health check
    healthPath: str = Field(
        default="/health", alias="health_path", description="Health check endpoint path"
    )
    healthTimeout: int = Field(
        default=5, ge=1, alias="health_timeout", description="Health check timeout in seconds"
    )
    
    # Request logging
    slowRequestThreshold: float = Field(
        default=1.0, ge=0, alias="slow_request_threshold", 
        description="Slow request threshold in seconds"
    )
    excludePaths: list[str] = Field(
        default_factory=lambda: ["/health", "/metrics"],
        alias="exclude_paths",
        description="Paths to exclude from access logging"
    )
    
    # Environment-specific overrides
    dev: Optional[EnvironmentConfig] = Field(
        default=None, description="Development environment overrides"
    )
    prod: Optional[EnvironmentConfig] = Field(
        default=None, description="Production environment overrides"
    )

    model_config = {"populate_by_name": True}

    def getEffectiveConfig(self) -> "LauncherConfig":
        """Get configuration with environment-specific overrides applied."""
        envConfig = self.dev if self.mode == RunMode.DEV else self.prod
        
        if envConfig is None:
            return self
        
        # Create a copy with overrides
        data = self.model_dump(by_alias=False, exclude={"dev", "prod"})
        
        if envConfig.reload is not None:
            data["reload"] = envConfig.reload
        if envConfig.workers is not None:
            data["workers"] = envConfig.workers
        if envConfig.logLevel is not None:
            data["logLevel"] = envConfig.logLevel
        if envConfig.logFormat is not None:
            data["logFormat"] = envConfig.logFormat
        
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
        
        return kwargs
