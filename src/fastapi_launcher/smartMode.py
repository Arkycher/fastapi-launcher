"""Smart environment detection module."""

import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values
from loguru import logger

from .enums import RunMode


# Environment detection priority:
# 1. FA_ENV environment variable
# 2. PYTHON_ENV environment variable
# 3. NODE_ENV environment variable (for full-stack projects)
# 4. .env file FA_ENV or PYTHON_ENV
# 5. Heuristic detection


def detectEnvironment(projectDir: Optional[Path] = None) -> tuple[str, RunMode]:
    """Detect the current environment and run mode.

    Args:
        projectDir: Project directory to check (defaults to cwd)

    Returns:
        Tuple of (environment_name, run_mode)
    """
    if projectDir is None:
        projectDir = Path.cwd()

    # 1. Check FA_ENV
    faEnv = os.environ.get("FA_ENV")
    if faEnv:
        logger.debug(f"Environment detected from FA_ENV | env={faEnv}")
        return _normalizeEnv(faEnv)

    # 2. Check PYTHON_ENV
    pythonEnv = os.environ.get("PYTHON_ENV")
    if pythonEnv:
        logger.debug(f"Environment detected from PYTHON_ENV | env={pythonEnv}")
        return _normalizeEnv(pythonEnv)

    # 3. Check NODE_ENV (for full-stack projects)
    nodeEnv = os.environ.get("NODE_ENV")
    if nodeEnv:
        logger.debug(f"Environment detected from NODE_ENV | env={nodeEnv}")
        return _normalizeEnv(nodeEnv)

    # 4. Check .env file
    envPath = projectDir / ".env"
    if envPath.exists():
        try:
            dotenvValues = dotenv_values(envPath)

            # Check for FA_ENV in .env
            dotenvFaEnv = dotenvValues.get("FA_ENV")
            if dotenvFaEnv:
                logger.debug(
                    f"Environment detected from .env FA_ENV | env={dotenvFaEnv}"
                )
                return _normalizeEnv(dotenvFaEnv)

            # Check for PYTHON_ENV in .env
            dotenvPythonEnv = dotenvValues.get("PYTHON_ENV")
            if dotenvPythonEnv:
                logger.debug(
                    f"Environment detected from .env PYTHON_ENV | env={dotenvPythonEnv}"
                )
                return _normalizeEnv(dotenvPythonEnv)
        except Exception as e:
            logger.warning(f"Failed to read .env file | error={e}")

    # 5. Heuristic detection
    return _heuristicDetection(projectDir)


def _normalizeEnv(envValue: str) -> tuple[str, RunMode]:
    """Normalize environment value to (env_name, run_mode).

    Args:
        envValue: Raw environment value

    Returns:
        Tuple of (normalized_name, run_mode)
    """
    envLower = envValue.lower().strip()

    # Map common environment names to modes
    devEnvNames = ("dev", "development", "local")
    prodEnvNames = ("prod", "production")

    if envLower in devEnvNames:
        return envLower, RunMode.DEV
    elif envLower in prodEnvNames:
        return envLower, RunMode.PROD
    else:
        # Custom environment names (staging, qa, test, etc.)
        # Default to prod mode for safety
        return envLower, RunMode.PROD


def _heuristicDetection(projectDir: Path) -> tuple[str, RunMode]:
    """Use heuristics to detect environment.

    Detection rules:
    - If .git/hooks/pre-commit exists -> dev
    - If Dockerfile or docker-compose.yml exists -> prod
    - Default -> dev

    Args:
        projectDir: Project directory

    Returns:
        Tuple of (env_name, run_mode)
    """
    # Check for development indicators
    devIndicators = [
        projectDir / ".git" / "hooks" / "pre-commit",
        projectDir / ".pre-commit-config.yaml",
    ]

    for indicator in devIndicators:
        if indicator.exists():
            logger.debug(f"Development indicator found | path={indicator}")
            return "dev", RunMode.DEV

    # Check for production indicators
    prodIndicators = [
        projectDir / "Dockerfile",
        projectDir / "docker-compose.yml",
        projectDir / "docker-compose.yaml",
        projectDir / "Procfile",  # Heroku
        projectDir / "app.yaml",  # Google App Engine
    ]

    for indicator in prodIndicators:
        if indicator.exists():
            logger.debug(f"Production indicator found | path={indicator}")
            return "prod", RunMode.PROD

    # Default to development
    logger.debug("No indicators found, defaulting to dev mode")
    return "dev", RunMode.DEV


def getEnvironmentInfo(projectDir: Optional[Path] = None) -> dict:
    """Get detailed environment detection information.

    Args:
        projectDir: Project directory

    Returns:
        Dictionary with detection details
    """
    if projectDir is None:
        projectDir = Path.cwd()

    detectedEnv, detectedMode = detectEnvironment(projectDir)

    return {
        "detected_env": detectedEnv,
        "detected_mode": detectedMode.value,
        "fa_env": os.environ.get("FA_ENV"),
        "python_env": os.environ.get("PYTHON_ENV"),
        "node_env": os.environ.get("NODE_ENV"),
        "project_dir": str(projectDir),
        "has_pre_commit": (projectDir / ".git" / "hooks" / "pre-commit").exists(),
        "has_dockerfile": (projectDir / "Dockerfile").exists(),
        "has_docker_compose": (
            (projectDir / "docker-compose.yml").exists()
            or (projectDir / "docker-compose.yaml").exists()
        ),
    }
