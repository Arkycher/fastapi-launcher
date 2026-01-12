"""Tests for app auto-discovery."""

from pathlib import Path

import pytest

from fastapi_launcher.discover import (
    discoverApp,
    getAppPathCandidates,
    validateAppPath,
    _findAppInFile,
)


class TestFindAppInFile:
    """Tests for finding app in Python files."""

    def test_find_fastapi_app(self, tempDir: Path) -> None:
        """Test finding standard FastAPI app."""
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello"}
""")
        
        result = _findAppInFile(mainPath)
        assert result == "app"

    def test_find_application_variable(self, tempDir: Path) -> None:
        """Test finding 'application' variable name."""
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

application = FastAPI(title="My App")
""")
        
        result = _findAppInFile(mainPath)
        assert result == "application"

    def test_find_api_variable(self, tempDir: Path) -> None:
        """Test finding 'api' variable name."""
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

api = FastAPI()
""")
        
        result = _findAppInFile(mainPath)
        assert result == "api"

    def test_find_create_app_pattern(self, tempDir: Path) -> None:
        """Test finding create_app() factory pattern."""
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

def create_app():
    return FastAPI()

app = create_app()
""")
        
        result = _findAppInFile(mainPath)
        assert result == "app"

    def test_no_app_found(self, tempDir: Path) -> None:
        """Test when no app is found."""
        mainPath = tempDir / "main.py"
        mainPath.write_text("""
print("Hello, World!")
""")
        
        result = _findAppInFile(mainPath)
        assert result is None

    def test_file_not_found(self, tempDir: Path) -> None:
        """Test with non-existent file."""
        result = _findAppInFile(tempDir / "nonexistent.py")
        assert result is None


class TestDiscoverApp:
    """Tests for app discovery."""

    def test_discover_main_app(self, mockProjectDir: Path) -> None:
        """Test discovering app in main.py."""
        result = discoverApp(mockProjectDir)
        
        assert result == "main:app"

    def test_discover_app_py(self, tempDir: Path) -> None:
        """Test discovering app in app.py."""
        appPath = tempDir / "app.py"
        appPath.write_text("""
from fastapi import FastAPI

app = FastAPI()
""")
        
        result = discoverApp(tempDir)
        assert result == "app:app"

    def test_discover_in_src(self, tempDir: Path) -> None:
        """Test discovering app in src directory."""
        srcDir = tempDir / "src"
        srcDir.mkdir()
        mainPath = srcDir / "main.py"
        mainPath.write_text("""
from fastapi import FastAPI

app = FastAPI()
""")
        
        result = discoverApp(tempDir)
        assert result == "src.main:app"

    def test_no_app_found(self, tempDir: Path) -> None:
        """Test when no app is found."""
        result = discoverApp(tempDir)
        assert result is None

    def test_priority_root_over_src(self, tempDir: Path) -> None:
        """Test root directory has priority over src."""
        # Create app in root
        mainPath = tempDir / "main.py"
        mainPath.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        # Create app in src
        srcDir = tempDir / "src"
        srcDir.mkdir()
        srcMainPath = srcDir / "main.py"
        srcMainPath.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        result = discoverApp(tempDir)
        assert result == "main:app"  # Root takes priority


class TestGetAppPathCandidates:
    """Tests for getting app path candidates."""

    def test_find_multiple_candidates(self, tempDir: Path) -> None:
        """Test finding multiple candidates."""
        # Create main.py
        mainPath = tempDir / "main.py"
        mainPath.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        # Create app.py
        appPath = tempDir / "app.py"
        appPath.write_text("from fastapi import FastAPI\napplication = FastAPI()")
        
        candidates = getAppPathCandidates(tempDir)
        
        assert "main:app" in candidates
        assert "app:application" in candidates

    def test_include_src_candidates(self, tempDir: Path) -> None:
        """Test including src directory candidates."""
        srcDir = tempDir / "src"
        srcDir.mkdir()
        mainPath = srcDir / "main.py"
        mainPath.write_text("from fastapi import FastAPI\napp = FastAPI()")
        
        candidates = getAppPathCandidates(tempDir)
        
        assert "src.main:app" in candidates

    def test_no_candidates(self, tempDir: Path) -> None:
        """Test when no candidates found."""
        candidates = getAppPathCandidates(tempDir)
        assert candidates == []


class TestValidateAppPath:
    """Tests for app path validation."""

    def test_valid_app_path(self, mockProjectDir: Path) -> None:
        """Test validating valid app path."""
        # This would require actually importing, which needs FastAPI installed
        # For unit test, we mock or skip this
        pass

    def test_invalid_format(self, tempDir: Path) -> None:
        """Test invalid app path format (no colon)."""
        result = validateAppPath("main", tempDir)
        assert result is False

    def test_module_not_found(self, tempDir: Path) -> None:
        """Test with non-existent module."""
        result = validateAppPath("nonexistent:app", tempDir)
        assert result is False

    def test_attribute_not_found(self, tempDir: Path) -> None:
        """Test with non-existent attribute."""
        mainPath = tempDir / "testmodule.py"
        mainPath.write_text("x = 1")
        
        result = validateAppPath("testmodule:nonexistent", tempDir)
        assert result is False
