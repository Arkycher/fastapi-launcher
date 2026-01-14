"""Pytest configuration and fixtures for FastAPI Launcher tests."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tempDir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mockProjectDir(tempDir: Path) -> Path:
    """Create a mock FastAPI project directory structure."""
    # Create pyproject.toml with fastapi-launcher config
    pyprojectPath = tempDir / "pyproject.toml"
    pyprojectPath.write_text("""
[project]
name = "test-project"
version = "0.1.0"

[tool.fastapi-launcher]
app = "main:app"
host = "127.0.0.1"
port = 8000
""")

    # Create main.py with a FastAPI app
    mainPath = tempDir / "main.py"
    mainPath.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
def health():
    return {"status": "healthy"}
""")

    return tempDir


@pytest.fixture
def mockEnvFile(tempDir: Path) -> Path:
    """Create a mock .env file."""
    envPath = tempDir / ".env"
    envPath.write_text("""
FA_HOST=0.0.0.0
FA_PORT=9000
FA_RELOAD=true
""")
    return envPath


@pytest.fixture
def cleanEnv() -> Generator[None, None, None]:
    """Clean up FA_ prefixed and environment detection variables."""
    # Variables to clean
    envPrefixes = ("FA_",)
    envVars = ("PYTHON_ENV", "NODE_ENV")
    
    # Save original values
    originalEnv = {}
    for k, v in os.environ.items():
        if k.startswith(envPrefixes) or k in envVars:
            originalEnv[k] = v
    
    # Remove all target variables
    for key in list(os.environ.keys()):
        if key.startswith(envPrefixes) or key in envVars:
            del os.environ[key]
    
    yield
    
    # Clean up any variables set during test
    for key in list(os.environ.keys()):
        if key.startswith(envPrefixes) or key in envVars:
            del os.environ[key]
    
    # Restore original variables
    os.environ.update(originalEnv)


@pytest.fixture
def mockRuntimeDir(tempDir: Path) -> Path:
    """Create a mock runtime directory."""
    runtimeDir = tempDir / "runtime"
    runtimeDir.mkdir(parents=True, exist_ok=True)
    logsDir = runtimeDir / "logs"
    logsDir.mkdir(parents=True, exist_ok=True)
    return runtimeDir


@pytest.fixture
def mockPidFile(mockRuntimeDir: Path) -> Path:
    """Create a mock PID file."""
    pidFile = mockRuntimeDir / "fa.pid"
    pidFile.write_text(str(os.getpid()))
    return pidFile
