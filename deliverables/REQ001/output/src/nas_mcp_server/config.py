"""Configuration loading for NAS MCP Server.

Supports configuration via environment variables or defaults:
- NAS_ROOT_DIR: Root directory path for file operations (required)
- MCP_PORT: Server listening port (default: 8080)
- ARIA2_HOST: aria2 RPC host (default: localhost)
- ARIA2_PORT: aria2 RPC port (default: 6800)
- ARIA2_SECRET: aria2 RPC secret token (optional)
"""

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid or incomplete."""


@dataclass(frozen=True)
class ServerConfig:
    """Immutable server configuration."""

    root_dir: Path
    port: int
    aria2_host: str
    aria2_port: int
    aria2_secret: str

    def __post_init__(self) -> None:
        if not self.root_dir.is_absolute():
            raise ConfigError(
                f"NAS_ROOT_DIR must be an absolute path, got: {self.root_dir}"
            )
        if not (1 <= self.port <= 65535):
            raise ConfigError(
                f"MCP_PORT must be between 1 and 65535, got: {self.port}"
            )
        if not (1 <= self.aria2_port <= 65535):
            raise ConfigError(
                f"ARIA2_PORT must be between 1 and 65535, got: {self.aria2_port}"
            )


def load_config() -> ServerConfig:
    """Load configuration from environment variables.

    Returns:
        ServerConfig with validated settings.

    Raises:
        ConfigError: If required config is missing or invalid.
    """
    root_dir_str = os.environ.get("NAS_ROOT_DIR")
    if not root_dir_str:
        raise ConfigError("NAS_ROOT_DIR environment variable is required")

    port_str = os.environ.get("MCP_PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        raise ConfigError(f"MCP_PORT must be an integer, got: {port_str}")

    aria2_host = os.environ.get("ARIA2_HOST", "localhost")
    aria2_port_str = os.environ.get("ARIA2_PORT", "6800")
    try:
        aria2_port = int(aria2_port_str)
    except ValueError:
        raise ConfigError(f"ARIA2_PORT must be an integer, got: {aria2_port_str}")

    aria2_secret = os.environ.get("ARIA2_SECRET", "")

    return ServerConfig(
        root_dir=Path(root_dir_str),
        port=port,
        aria2_host=aria2_host,
        aria2_port=aria2_port,
        aria2_secret=aria2_secret,
    )
