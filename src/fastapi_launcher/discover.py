"""FastAPI app auto-discovery."""

import importlib.util
import sys
from pathlib import Path
from typing import Optional

# Common entry point patterns to check
COMMON_ENTRY_POINTS = [
    "main:app",
    "app:app",
    "src.main:app",
    "src.app:app",
    "api:app",
    "server:app",
    "application:app",
]

# Common file names to check
COMMON_FILES = [
    "main.py",
    "app.py",
    "api.py",
    "server.py",
    "application.py",
]


def discoverApp(projectDir: Optional[Path] = None) -> Optional[str]:
    """
    Auto-discover FastAPI app in the project directory.

    Returns the app import path (e.g., 'main:app') or None if not found.
    """
    if projectDir is None:
        projectDir = Path.cwd()

    # Check common file locations
    for fileName in COMMON_FILES:
        filePath = projectDir / fileName
        if filePath.exists():
            appPath = _findAppInFile(filePath)
            if appPath:
                moduleName = fileName[:-3]  # Remove .py
                return f"{moduleName}:{appPath}"

    # Check src directory
    srcDir = projectDir / "src"
    if srcDir.exists():
        for fileName in COMMON_FILES:
            filePath = srcDir / fileName
            if filePath.exists():
                appPath = _findAppInFile(filePath)
                if appPath:
                    moduleName = fileName[:-3]
                    return f"src.{moduleName}:{appPath}"

    return None


def _findAppInFile(filePath: Path) -> Optional[str]:
    """Find FastAPI app variable name in a Python file."""
    try:
        content = filePath.read_text()
    except Exception:
        return None

    # Look for common patterns
    # 1. app = FastAPI(...)
    # 2. application = FastAPI(...)
    # 3. api = FastAPI(...)

    appNames = ["app", "application", "api"]

    for appName in appNames:
        # Check for FastAPI instantiation
        if f"{appName} = FastAPI(" in content or f"{appName}=FastAPI(" in content:
            return appName
        # Check for variable assignment from create_app()
        if f"{appName} = create_app(" in content or f"{appName}=create_app(" in content:
            return appName

    return None


def validateAppPath(appPath: str, projectDir: Optional[Path] = None) -> bool:
    """
    Validate that the app path can be imported and contains a FastAPI app.

    Args:
        appPath: Import path like 'main:app'
        projectDir: Project directory to add to sys.path

    Returns:
        True if valid, False otherwise
    """
    if projectDir is None:
        projectDir = Path.cwd()

    if ":" not in appPath:
        return False

    modulePath, attrName = appPath.rsplit(":", 1)

    # Temporarily add project dir to path
    projectDirStr = str(projectDir)
    addedToPath = False
    if projectDirStr not in sys.path:
        sys.path.insert(0, projectDirStr)
        addedToPath = True

    try:
        # Try to import the module
        module = importlib.import_module(modulePath)

        # Check if the attribute exists
        if not hasattr(module, attrName):
            return False

        app = getattr(module, attrName)

        # Check if it's a FastAPI app (duck typing)
        # FastAPI apps have routes and add_api_route method
        if hasattr(app, "routes") and hasattr(app, "add_api_route"):
            return True

        # Could also be a factory function
        if callable(app):
            return True

        return False

    except (ImportError, ModuleNotFoundError, AttributeError):
        return False
    finally:
        if addedToPath and projectDirStr in sys.path:
            sys.path.remove(projectDirStr)


def getAppPathCandidates(projectDir: Optional[Path] = None) -> list[str]:
    """
    Get a list of potential app paths found in the project.

    Returns a list of import paths that could be FastAPI apps.
    """
    if projectDir is None:
        projectDir = Path.cwd()

    candidates: list[str] = []

    # Check root directory
    for fileName in COMMON_FILES:
        filePath = projectDir / fileName
        if filePath.exists():
            appPath = _findAppInFile(filePath)
            if appPath:
                moduleName = fileName[:-3]
                candidates.append(f"{moduleName}:{appPath}")

    # Check src directory
    srcDir = projectDir / "src"
    if srcDir.exists():
        for fileName in COMMON_FILES:
            filePath = srcDir / fileName
            if filePath.exists():
                appPath = _findAppInFile(filePath)
                if appPath:
                    moduleName = fileName[:-3]
                    candidates.append(f"src.{moduleName}:{appPath}")

    return candidates
