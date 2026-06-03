"""MCP Server setup and SSE transport initialization."""

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from .config import ServerConfig
from .tools import register_tools


def create_server(config: ServerConfig) -> Server:
    """Create and configure the MCP server instance.

    Args:
        config: Validated server configuration.

    Returns:
        Configured MCP Server instance with file operation tools registered.
    """
    server = Server("nas-mcp-server")
    # Store config on server instance for tool implementations to access
    server._nas_config = config  # type: ignore[attr-defined]
    # Register all file operation tools
    register_tools(server, config)
    return server


def create_app(server: Server) -> Starlette:
    """Create the Starlette ASGI app with SSE transport.

    Args:
        server: Configured MCP Server instance.

    Returns:
        Starlette application ready to serve SSE connections.
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    return app
