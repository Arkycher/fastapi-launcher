"""Tests for smart mode detection module."""

import os
from pathlib import Path

import pytest

from fastapi_launcher.enums import RunMode
from fastapi_launcher.smartMode import (
    _heuristicDetection,
    _normalizeEnv,
    detectEnvironment,
    getEnvironmentInfo,
)


class TestNormalizeEnv:
    """Tests for _normalizeEnv function."""

    def test_dev_environment(self) -> None:
        """Test development environment normalization."""
        assert _normalizeEnv("dev") == ("dev", RunMode.DEV)
        assert _normalizeEnv("development") == ("development", RunMode.DEV)
        assert _normalizeEnv("local") == ("local", RunMode.DEV)
        assert _normalizeEnv("DEV") == ("dev", RunMode.DEV)  # Case insensitive

    def test_prod_environment(self) -> None:
        """Test production environment normalization."""
        assert _normalizeEnv("prod") == ("prod", RunMode.PROD)
        assert _normalizeEnv("production") == ("production", RunMode.PROD)
        assert _normalizeEnv("PROD") == ("prod", RunMode.PROD)

    def test_custom_environment(self) -> None:
        """Test custom environment normalization defaults to PROD."""
        assert _normalizeEnv("staging") == ("staging", RunMode.PROD)
        assert _normalizeEnv("qa") == ("qa", RunMode.PROD)
        assert _normalizeEnv("test") == ("test", RunMode.PROD)


class TestDetectEnvironment:
    """Tests for detectEnvironment function."""

    def test_fa_env_priority(self, cleanEnv, tempDir: Path) -> None:
        """Test FA_ENV has highest priority."""
        os.environ["FA_ENV"] = "staging"
        os.environ["PYTHON_ENV"] = "development"
        os.environ["NODE_ENV"] = "production"
        
        envName, mode = detectEnvironment(tempDir)
        
        assert envName == "staging"
        assert mode == RunMode.PROD  # staging defaults to PROD

    def test_python_env_priority(self, cleanEnv, tempDir: Path) -> None:
        """Test PYTHON_ENV priority when FA_ENV not set."""
        os.environ["PYTHON_ENV"] = "development"
        os.environ["NODE_ENV"] = "production"
        
        envName, mode = detectEnvironment(tempDir)
        
        assert envName == "development"
        assert mode == RunMode.DEV

    def test_node_env_priority(self, cleanEnv, tempDir: Path) -> None:
        """Test NODE_ENV priority when FA_ENV and PYTHON_ENV not set."""
        os.environ["NODE_ENV"] = "production"
        
        envName, mode = detectEnvironment(tempDir)
        
        assert envName == "production"
        assert mode == RunMode.PROD

    def test_dotenv_fa_env(self, cleanEnv, tempDir: Path) -> None:
        """Test .env FA_ENV detection."""
        envPath = tempDir / ".env"
        envPath.write_text("FA_ENV=staging\n")
        
        envName, mode = detectEnvironment(tempDir)
        
        assert envName == "staging"
        assert mode == RunMode.PROD

    def test_dotenv_python_env(self, cleanEnv, tempDir: Path) -> None:
        """Test .env PYTHON_ENV detection."""
        envPath = tempDir / ".env"
        envPath.write_text("PYTHON_ENV=development\n")
        
        envName, mode = detectEnvironment(tempDir)
        
        assert envName == "development"
        assert mode == RunMode.DEV


class TestHeuristicDetection:
    """Tests for _heuristicDetection function."""

    def test_pre_commit_hook_indicates_dev(self, tempDir: Path) -> None:
        """Test pre-commit hook indicates development."""
        gitHooksDir = tempDir / ".git" / "hooks"
        gitHooksDir.mkdir(parents=True)
        (gitHooksDir / "pre-commit").write_text("#!/bin/bash\n")
        
        envName, mode = _heuristicDetection(tempDir)
        
        assert envName == "dev"
        assert mode == RunMode.DEV

    def test_dockerfile_indicates_prod(self, tempDir: Path) -> None:
        """Test Dockerfile indicates production."""
        (tempDir / "Dockerfile").write_text("FROM python:3.11\n")
        
        envName, mode = _heuristicDetection(tempDir)
        
        assert envName == "prod"
        assert mode == RunMode.PROD

    def test_docker_compose_indicates_prod(self, tempDir: Path) -> None:
        """Test docker-compose.yml indicates production."""
        (tempDir / "docker-compose.yml").write_text("version: '3'\n")
        
        envName, mode = _heuristicDetection(tempDir)
        
        assert envName == "prod"
        assert mode == RunMode.PROD

    def test_procfile_indicates_prod(self, tempDir: Path) -> None:
        """Test Procfile (Heroku) indicates production."""
        (tempDir / "Procfile").write_text("web: gunicorn main:app\n")
        
        envName, mode = _heuristicDetection(tempDir)
        
        assert envName == "prod"
        assert mode == RunMode.PROD

    def test_default_is_dev(self, tempDir: Path) -> None:
        """Test default environment is development."""
        envName, mode = _heuristicDetection(tempDir)
        
        assert envName == "dev"
        assert mode == RunMode.DEV


class TestGetEnvironmentInfo:
    """Tests for getEnvironmentInfo function."""

    def test_environment_info_structure(self, cleanEnv, tempDir: Path) -> None:
        """Test environment info returns expected structure."""
        info = getEnvironmentInfo(tempDir)
        
        assert "detected_env" in info
        assert "detected_mode" in info
        assert "fa_env" in info
        assert "python_env" in info
        assert "node_env" in info
        assert "project_dir" in info
        assert "has_pre_commit" in info
        assert "has_dockerfile" in info
        assert "has_docker_compose" in info

    def test_environment_info_with_env_vars(self, cleanEnv, tempDir: Path) -> None:
        """Test environment info includes env vars."""
        os.environ["FA_ENV"] = "staging"
        
        info = getEnvironmentInfo(tempDir)
        
        assert info["fa_env"] == "staging"
        assert info["detected_env"] == "staging"
