"""Configuration loading for NAS MCP Server.

Supports configuration via environment variables or defaults:
- NAS_ROOT_DIR: Root directory path for file operations (required)
- MCP_PORT: Server listening port (default: 8080)
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

    def __post_init__(self) -> None:
        if not self.root_dir.is_absolute():
            raise ConfigError(
                f"NAS_ROOT_DIR must be an absolute path, got: {self.root_dir}"
            )
        if not (1 <= self.port <= 65535):
            raise ConfigError(
                f"MCP_PORT must be between 1 and 65535, got: {self.port}"
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

    return ServerConfig(root_dir=Path(root_dir_str), port=port)
