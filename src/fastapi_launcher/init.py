"""Configuration initialization module."""

from pathlib import Path
from typing import Optional

from loguru import logger


# Default configuration template
DEFAULT_CONFIG_TEMPLATE = """
[tool.fastapi-launcher]
app = "main:app"
host = "127.0.0.1"
port = 8000
log_level = "info"
runtime_dir = "runtime"

# Development environment overrides
[tool.fastapi-launcher.dev]
reload = true
log_level = "debug"

# Production environment overrides
[tool.fastapi-launcher.prod]
host = "0.0.0.0"
workers = 4
daemon = false
log_level = "warning"

# Custom environments (optional)
# [tool.fastapi-launcher.envs.staging]
# host = "0.0.0.0"
# workers = 2
# log_level = "info"

# [tool.fastapi-launcher.envs.qa]
# host = "0.0.0.0"
# workers = 2
# log_level = "debug"
"""

# .env template
ENV_TEMPLATE = """# FastAPI Launcher Environment Configuration
# See https://github.com/fastapi-launcher/fastapi-launcher for more info

# Environment mode (dev/prod/staging/qa)
# FA_ENV=dev

# Server configuration
# FA_HOST=127.0.0.1
# FA_PORT=8000

# Worker configuration
# FA_WORKERS=4
# FA_SERVER=uvicorn

# Graceful shutdown
# FA_TIMEOUT_GRACEFUL_SHUTDOWN=10

# Gunicorn-specific (when FA_SERVER=gunicorn)
# FA_MAX_REQUESTS=1000
# FA_MAX_REQUESTS_JITTER=100

# Logging
# FA_LOG_LEVEL=info
# FA_LOG_FORMAT=pretty
# FA_ACCESS_LOG=true

# Runtime
# FA_RUNTIME_DIR=runtime
# FA_HEALTH_PATH=/health
"""


def hasFastAPILauncherConfig(pyprojectPath: Path) -> bool:
    """Check if pyproject.toml has [tool.fastapi-launcher] section.

    Args:
        pyprojectPath: Path to pyproject.toml

    Returns:
        True if the section exists
    """
    if not pyprojectPath.exists():
        return False

    try:
        content = pyprojectPath.read_text()
        return "[tool.fastapi-launcher]" in content
    except Exception:
        return False


def initConfig(
    projectDir: Optional[Path] = None,
    force: bool = False,
    generateEnv: bool = False,
) -> tuple[bool, str]:
    """Initialize FastAPI Launcher configuration in a project.

    Args:
        projectDir: Project directory (defaults to current directory)
        force: Force overwrite existing configuration
        generateEnv: Also generate .env.example file

    Returns:
        Tuple of (success, message)
    """
    if projectDir is None:
        projectDir = Path.cwd()

    pyprojectPath = projectDir / "pyproject.toml"

    # Check if pyproject.toml exists
    if not pyprojectPath.exists():
        logger.warning(f"pyproject.toml not found at {projectDir}")
        return False, "pyproject.toml not found. Create it first or run 'pip init'."

    # Check for existing configuration
    if hasFastAPILauncherConfig(pyprojectPath):
        if not force:
            logger.info("Configuration already exists | path={}", pyprojectPath)
            return False, (
                "Configuration already exists in pyproject.toml. "
                "Use --force to overwrite."
            )
        logger.info("Force overwriting existing configuration | path={}", pyprojectPath)

    # Read existing content
    try:
        existingContent = pyprojectPath.read_text()
    except Exception as e:
        logger.error(f"Failed to read pyproject.toml | error={e}")
        return False, f"Failed to read pyproject.toml: {e}"

    # Remove existing [tool.fastapi-launcher] section if force
    if force and "[tool.fastapi-launcher]" in existingContent:
        lines = existingContent.split("\n")
        newLines = []
        skipSection = False

        for line in lines:
            # Check if we're entering the fastapi-launcher section
            if line.strip().startswith("[tool.fastapi-launcher"):
                skipSection = True
                continue
            # Check if we're entering a new section (end of fastapi-launcher)
            if (
                skipSection
                and line.strip().startswith("[")
                and "fastapi-launcher" not in line
            ):
                skipSection = False

            if not skipSection:
                newLines.append(line)

        existingContent = "\n".join(newLines)
        # Clean up excessive newlines
        while "\n\n\n" in existingContent:
            existingContent = existingContent.replace("\n\n\n", "\n\n")

    # Append configuration
    newContent = (
        existingContent.rstrip() + "\n" + DEFAULT_CONFIG_TEMPLATE.strip() + "\n"
    )

    try:
        pyprojectPath.write_text(newContent)
        logger.info("Configuration added to pyproject.toml | path={}", pyprojectPath)
    except Exception as e:
        logger.error(f"Failed to write pyproject.toml | error={e}")
        return False, f"Failed to write pyproject.toml: {e}"

    # Generate .env.example if requested
    envMessage = ""
    if generateEnv:
        envSuccess, envMsg = generateEnvTemplate(projectDir, force)
        envMessage = f"\n{envMsg}"

    return True, f"Configuration added to pyproject.toml{envMessage}"


def generateEnvTemplate(
    projectDir: Optional[Path] = None,
    force: bool = False,
) -> tuple[bool, str]:
    """Generate .env.example file.

    Args:
        projectDir: Project directory (defaults to current directory)
        force: Force overwrite existing file

    Returns:
        Tuple of (success, message)
    """
    if projectDir is None:
        projectDir = Path.cwd()

    envExamplePath = projectDir / ".env.example"

    # Check for existing file
    if envExamplePath.exists() and not force:
        logger.info(".env.example already exists | path={}", envExamplePath)
        return False, ".env.example already exists. Use --force to overwrite."

    try:
        envExamplePath.write_text(ENV_TEMPLATE.strip() + "\n")
        logger.info("Generated .env.example | path={}", envExamplePath)
        return True, "Generated .env.example"
    except Exception as e:
        logger.error(f"Failed to write .env.example | error={e}")
        return False, f"Failed to write .env.example: {e}"
