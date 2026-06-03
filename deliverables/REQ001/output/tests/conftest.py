"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock the mcp module before any imports that depend on it
# This allows testing on Python 3.9 where mcp SDK cannot be installed
mcp_mock = MagicMock()
mcp_server_mock = MagicMock()
mcp_sse_mock = MagicMock()

# Create a mock Server class that behaves like the real one
class MockServer:
    def __init__(self, name):
        self.name = name
        self._tool_handlers = {}
        self._tool_schemas = {}

    def create_initialization_options(self):
        return {}

    async def run(self, read_stream, write_stream, options):
        pass

    def list_tools(self):
        """Decorator for listing tools."""
        def decorator(func):
            self._list_tools_handler = func
            return func
        return decorator

    def call_tool(self):
        """Decorator for calling tools."""
        def decorator(func):
            self._call_tool_handler = func
            return func
        return decorator


mcp_server_mock.Server = MockServer
mcp_sse_mock.SseServerTransport = MagicMock()

sys.modules.setdefault("mcp", mcp_mock)
sys.modules.setdefault("mcp.server", mcp_server_mock)
sys.modules.setdefault("mcp.server.sse", mcp_sse_mock)

# Mock starlette as well since it's a transitive dependency of mcp
starlette_mock = MagicMock()
starlette_apps_mock = MagicMock()
starlette_routing_mock = MagicMock()


class MockStarlette:
    def __init__(self, routes=None, **kwargs):
        self.routes = routes or []


class MockRoute:
    def __init__(self, path, endpoint=None, **kwargs):
        self.path = path
        self.endpoint = endpoint


class MockMount:
    def __init__(self, path, app=None, **kwargs):
        self.path = path
        self.app = app


starlette_apps_mock.Starlette = MockStarlette
starlette_routing_mock.Route = MockRoute
starlette_routing_mock.Mount = MockMount

sys.modules.setdefault("starlette", starlette_mock)
sys.modules.setdefault("starlette.applications", starlette_apps_mock)
sys.modules.setdefault("starlette.routing", starlette_routing_mock)

# Mock uvicorn
sys.modules.setdefault("uvicorn", MagicMock())

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
