"""Entry point for NAS MCP Server."""

import sys

import uvicorn

from .config import ConfigError, load_config
from .server import create_app, create_server


def main() -> None:
    """Start the NAS MCP Server with SSE transport."""
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    if not config.root_dir.exists():
        print(
            f"Error: NAS_ROOT_DIR does not exist: {config.root_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    server = create_server(config)
    app = create_app(server)

    print(f"Starting NAS MCP Server on port {config.port}")
    print(f"Root directory: {config.root_dir}")
    print(f"SSE endpoint: http://0.0.0.0:{config.port}/sse")

    uvicorn.run(app, host="0.0.0.0", port=config.port)


if __name__ == "__main__":
    main()
