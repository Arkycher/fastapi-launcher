"""Configuration loading and merging."""

import os
from pathlib import Path
from typing import Any, Optional

from dotenv import dotenv_values
from pydantic import ValidationError

from .enums import LogFormat, RunMode, ServerBackend
from .schemas import LauncherConfig

# Configuration priority (highest to lowest):
# 1. CLI arguments
# 2. Environment variables (FA_ prefix)
# 3. .env file
# 4. pyproject.toml [tool.fastapi-launcher.envs.<name>] section (if --env specified)
# 5. pyproject.toml [tool.fastapi-launcher]
# 6. Default values


def loadPyprojectConfig(projectDir: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml [tool.fastapi-launcher] section."""
    pyprojectPath = projectDir / "pyproject.toml"
    
    if not pyprojectPath.exists():
        return {}
    
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore
    
    try:
        with open(pyprojectPath, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("fastapi-launcher", {})
    except Exception:
        return {}


def loadDotenvConfig(projectDir: Path) -> dict[str, Any]:
    """Load configuration from .env file."""
    envPath = projectDir / ".env"
    
    if not envPath.exists():
        return {}
    
    values = dotenv_values(envPath)
    return _parseEnvValues(values)


def loadEnvConfig() -> dict[str, Any]:
    """Load configuration from environment variables with FA_ prefix."""
    envValues = {
        k[3:]: v for k, v in os.environ.items() 
        if k.startswith("FA_") and v is not None
    }
    return _parseEnvValues(envValues)


def _parseEnvValues(values: dict[str, Any]) -> dict[str, Any]:
    """Parse environment variable values to appropriate types."""
    result: dict[str, Any] = {}
    
    keyMapping = {
        "APP": "app",
        "APP_DIR": "app_dir",
        "HOST": "host",
        "PORT": "port",
        "MODE": "mode",
        "RELOAD": "reload",
        "RELOAD_DIRS": "reload_dirs",
        "WORKERS": "workers",
        "DAEMON": "daemon",
        "LOG_LEVEL": "log_level",
        "LOG_FORMAT": "log_format",
        "ACCESS_LOG": "access_log",
        "RUNTIME_DIR": "runtime_dir",
        "HEALTH_PATH": "health_path",
        "HEALTH_TIMEOUT": "health_timeout",
        "SLOW_REQUEST_THRESHOLD": "slow_request_threshold",
        "EXCLUDE_PATHS": "exclude_paths",
        "SERVER": "server",
        "TIMEOUT_GRACEFUL_SHUTDOWN": "timeout_graceful_shutdown",
        "MAX_REQUESTS": "max_requests",
        "MAX_REQUESTS_JITTER": "max_requests_jitter",
        "WORKER_CLASS": "worker_class",
    }
    
    for envKey, value in values.items():
        configKey = keyMapping.get(envKey.upper())
        if configKey is None:
            continue
        
        # Type conversion
        if configKey in ("port", "workers", "health_timeout", "timeout_graceful_shutdown", 
                         "max_requests", "max_requests_jitter"):
            try:
                result[configKey] = int(value)
            except (ValueError, TypeError):
                pass
        elif configKey in ("reload", "daemon", "access_log"):
            result[configKey] = str(value).lower() in ("true", "1", "yes")
        elif configKey == "slow_request_threshold":
            try:
                result[configKey] = float(value)
            except (ValueError, TypeError):
                pass
        elif configKey in ("reload_dirs", "exclude_paths"):
            if isinstance(value, str):
                result[configKey] = [p.strip() for p in value.split(",") if p.strip()]
            else:
                result[configKey] = value
        elif configKey == "mode":
            try:
                result[configKey] = RunMode(value.lower())
            except ValueError:
                pass
        elif configKey == "log_format":
            try:
                result[configKey] = LogFormat(value.lower())
            except ValueError:
                pass
        elif configKey == "server":
            try:
                result[configKey] = ServerBackend(value.lower())
            except ValueError:
                pass
        else:
            result[configKey] = value
    
    return result


def mergeConfigs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configurations, later ones take precedence."""
    result: dict[str, Any] = {}
    
    for config in configs:
        for key, value in config.items():
            if value is not None:
                result[key] = value
    
    return result


def loadConfig(
    projectDir: Optional[Path] = None,
    cliArgs: Optional[dict[str, Any]] = None,
    mode: Optional[RunMode] = None,
    envName: Optional[str] = None,
) -> LauncherConfig:
    """
    Load and merge configuration from all sources.
    
    Priority (highest to lowest):
    1. CLI arguments
    2. Environment variables (FA_ prefix)
    3. .env file
    4. pyproject.toml [tool.fastapi-launcher.envs.<name>] section (if envName specified)
    5. pyproject.toml [tool.fastapi-launcher]
    6. Default values
    
    Args:
        projectDir: Project directory to load configuration from
        cliArgs: CLI arguments to merge into config
        mode: Override run mode
        envName: Named environment to use (e.g., 'staging', 'qa')
    
    Returns:
        Merged LauncherConfig with environment-specific overrides applied
    
    Raises:
        ValueError: If configuration is invalid or environment not found
    """
    if projectDir is None:
        projectDir = Path.cwd()
    
    # Load from all sources
    pyprojectConfig = loadPyprojectConfig(projectDir)
    dotenvConfig = loadDotenvConfig(projectDir)
    osEnvConfig = loadEnvConfig()
    
    # Filter out None values from CLI args
    cliConfig = {k: v for k, v in (cliArgs or {}).items() if v is not None}
    
    # Merge configs (priority order)
    mergedConfig = mergeConfigs(
        pyprojectConfig,
        dotenvConfig,
        osEnvConfig,
        cliConfig,
    )
    
    # Apply mode override
    if mode is not None:
        mergedConfig["mode"] = mode
    
    # Set app_dir if not specified
    if "app_dir" not in mergedConfig:
        mergedConfig["app_dir"] = projectDir
    
    try:
        config = LauncherConfig(**mergedConfig)
        
        # Validate named environment exists if specified
        if envName and config.envs:
            if envName not in config.envs:
                availableEnvs = list(config.envs.keys())
                raise ValueError(
                    f"Environment '{envName}' not found in configuration. "
                    f"Available environments: {availableEnvs}"
                )
        elif envName and not config.envs:
            raise ValueError(
                f"Environment '{envName}' not found. "
                "No environments defined in [tool.fastapi-launcher.envs]"
            )
        
        return config.getEffectiveConfig(envName=envName)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}") from e


def getAvailableEnvs(projectDir: Optional[Path] = None) -> list[str]:
    """Get list of available named environments.
    
    Args:
        projectDir: Project directory to load configuration from
    
    Returns:
        List of environment names
    """
    if projectDir is None:
        projectDir = Path.cwd()
    
    pyprojectConfig = loadPyprojectConfig(projectDir)
    envs = pyprojectConfig.get("envs", {})
    return list(envs.keys())


def getConfigSummary(config: LauncherConfig) -> dict[str, Any]:
    """Get a summary of the current configuration for display."""
    return {
        "app": config.app,
        "host": config.host,
        "port": config.port,
        "mode": config.mode.value,
        "server": config.server.value,
        "reload": config.reload,
        "workers": config.workers,
        "daemon": config.daemon,
        "log_level": config.logLevel,
        "log_format": config.logFormat.value,
        "access_log": config.accessLog,
        "runtime_dir": str(config.runtimeDir),
        "health_path": config.healthPath,
        "timeout_graceful_shutdown": config.timeoutGracefulShutdown,
        "max_requests": config.maxRequests,
    }
