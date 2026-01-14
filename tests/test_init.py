"""Tests for init module."""

from pathlib import Path

import pytest

from fastapi_launcher.init import (
    DEFAULT_CONFIG_TEMPLATE,
    ENV_TEMPLATE,
    generateEnvTemplate,
    hasFastAPILauncherConfig,
    initConfig,
)


class TestHasFastAPILauncherConfig:
    """Tests for hasFastAPILauncherConfig function."""

    def test_no_pyproject(self, tempDir: Path) -> None:
        """Test when pyproject.toml doesn't exist."""
        result = hasFastAPILauncherConfig(tempDir / "pyproject.toml")
        assert result is False

    def test_no_launcher_section(self, tempDir: Path) -> None:
        """Test when [tool.fastapi-launcher] section doesn't exist."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[project]
name = "test"
""")
        result = hasFastAPILauncherConfig(pyprojectPath)
        assert result is False

    def test_has_launcher_section(self, tempDir: Path) -> None:
        """Test when [tool.fastapi-launcher] section exists."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""
[project]
name = "test"

[tool.fastapi-launcher]
app = "main:app"
""")
        result = hasFastAPILauncherConfig(pyprojectPath)
        assert result is True


class TestInitConfig:
    """Tests for initConfig function."""

    def test_no_pyproject_file(self, tempDir: Path) -> None:
        """Test init when pyproject.toml doesn't exist."""
        success, message = initConfig(tempDir)
        assert success is False
        assert "pyproject.toml not found" in message

    def test_add_config_to_existing_pyproject(self, tempDir: Path) -> None:
        """Test adding config to existing pyproject.toml."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test"
version = "0.1.0"
""")
        
        success, message = initConfig(tempDir)
        
        assert success is True
        assert "Configuration added" in message
        
        content = pyprojectPath.read_text()
        assert "[tool.fastapi-launcher]" in content
        assert 'app = "main:app"' in content

    def test_config_already_exists(self, tempDir: Path) -> None:
        """Test when config already exists."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test"

[tool.fastapi-launcher]
app = "existing:app"
""")
        
        success, message = initConfig(tempDir)
        
        assert success is False
        assert "already exists" in message

    def test_force_overwrite(self, tempDir: Path) -> None:
        """Test force overwrite of existing config."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test"

[tool.fastapi-launcher]
app = "old:app"
""")
        
        success, message = initConfig(tempDir, force=True)
        
        assert success is True
        content = pyprojectPath.read_text()
        assert '[tool.fastapi-launcher]' in content
        # Old config should be replaced
        assert 'app = "main:app"' in content

    def test_generate_env_file(self, tempDir: Path) -> None:
        """Test generating .env.example along with config."""
        pyprojectPath = tempDir / "pyproject.toml"
        pyprojectPath.write_text("""[project]
name = "test"
""")
        
        success, message = initConfig(tempDir, generateEnv=True)
        
        assert success is True
        
        envExamplePath = tempDir / ".env.example"
        assert envExamplePath.exists()
        
        content = envExamplePath.read_text()
        assert "FA_ENV" in content
        assert "FA_HOST" in content


class TestGenerateEnvTemplate:
    """Tests for generateEnvTemplate function."""

    def test_generate_env_template(self, tempDir: Path) -> None:
        """Test generating .env.example file."""
        success, message = generateEnvTemplate(tempDir)
        
        assert success is True
        
        envExamplePath = tempDir / ".env.example"
        assert envExamplePath.exists()
        
        content = envExamplePath.read_text()
        assert "FA_ENV" in content
        assert "FA_PORT" in content
        assert "FA_WORKERS" in content

    def test_env_template_already_exists(self, tempDir: Path) -> None:
        """Test when .env.example already exists."""
        envExamplePath = tempDir / ".env.example"
        envExamplePath.write_text("# Existing content")
        
        success, message = generateEnvTemplate(tempDir)
        
        assert success is False
        assert "already exists" in message
        
        # Content should not change
        content = envExamplePath.read_text()
        assert content == "# Existing content"

    def test_force_overwrite_env(self, tempDir: Path) -> None:
        """Test force overwrite of existing .env.example."""
        envExamplePath = tempDir / ".env.example"
        envExamplePath.write_text("# Old content")
        
        success, message = generateEnvTemplate(tempDir, force=True)
        
        assert success is True
        
        content = envExamplePath.read_text()
        assert "FA_ENV" in content
