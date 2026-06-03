"""Tests for configuration loading."""

import os
from pathlib import Path

import pytest

from nas_mcp_server.config import ConfigError, ServerConfig, load_config


class TestServerConfig:
    """Tests for ServerConfig dataclass validation."""

    def test_valid_config(self, tmp_path):
        config = ServerConfig(
            root_dir=tmp_path, port=8080,
            aria2_host="localhost", aria2_port=6800, aria2_secret="",
        )
        assert config.root_dir == tmp_path
        assert config.port == 8080

    def test_relative_path_rejected(self):
        with pytest.raises(ConfigError, match="absolute path"):
            ServerConfig(
                root_dir=Path("relative/path"), port=8080,
                aria2_host="localhost", aria2_port=6800, aria2_secret="",
            )

    def test_port_zero_rejected(self):
        with pytest.raises(ConfigError, match="between 1 and 65535"):
            ServerConfig(
                root_dir=Path("/tmp"), port=0,
                aria2_host="localhost", aria2_port=6800, aria2_secret="",
            )

    def test_port_too_high_rejected(self):
        with pytest.raises(ConfigError, match="between 1 and 65535"):
            ServerConfig(
                root_dir=Path("/tmp"), port=70000,
                aria2_host="localhost", aria2_port=6800, aria2_secret="",
            )

    def test_config_is_immutable(self, tmp_path):
        config = ServerConfig(
            root_dir=tmp_path, port=8080,
            aria2_host="localhost", aria2_port=6800, aria2_secret="",
        )
        with pytest.raises(Exception):
            config.port = 9090  # type: ignore[misc]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NAS_ROOT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_PORT", "9090")
        config = load_config()
        assert config.root_dir == tmp_path
        assert config.port == 9090

    def test_default_port(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NAS_ROOT_DIR", str(tmp_path))
        monkeypatch.delenv("MCP_PORT", raising=False)
        config = load_config()
        assert config.port == 8080

    def test_missing_root_dir(self, monkeypatch):
        monkeypatch.delenv("NAS_ROOT_DIR", raising=False)
        with pytest.raises(ConfigError, match="NAS_ROOT_DIR.*required"):
            load_config()

    def test_invalid_port_not_integer(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NAS_ROOT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_PORT", "abc")
        with pytest.raises(ConfigError, match="must be an integer"):
            load_config()
