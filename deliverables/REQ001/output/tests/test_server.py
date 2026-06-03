"""Tests for MCP server initialization."""

from pathlib import Path

from nas_mcp_server.config import ServerConfig
from nas_mcp_server.server import create_app, create_server


class TestCreateServer:
    """Tests for server creation."""

    def test_create_server_returns_server(self, tmp_path):
        config = ServerConfig(root_dir=tmp_path, port=8080)
        server = create_server(config)
        assert server is not None
        assert server.name == "nas-mcp-server"

    def test_server_stores_config(self, tmp_path):
        config = ServerConfig(root_dir=tmp_path, port=8080)
        server = create_server(config)
        assert server._nas_config == config


class TestCreateApp:
    """Tests for Starlette app creation."""

    def test_create_app_returns_starlette(self, tmp_path):
        config = ServerConfig(root_dir=tmp_path, port=8080)
        server = create_server(config)
        app = create_app(server)
        assert app is not None

    def test_app_has_sse_route(self, tmp_path):
        config = ServerConfig(root_dir=tmp_path, port=8080)
        server = create_server(config)
        app = create_app(server)
        route_paths = [r.path for r in app.routes]
        assert "/sse" in route_paths
