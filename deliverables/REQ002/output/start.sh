#!/usr/bin/env bash
# NAS MCP Server startup script
# Usage: ./start.sh
# Make executable: chmod +x start.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo "Warning: .env file not found at $SCRIPT_DIR/.env"
    echo "Copy .env.example to .env and configure it first."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Start MCP Server
echo "Starting NAS MCP Server..."
echo "  Root directory: ${NAS_ROOT_DIR:-not set}"
echo "  Port: ${MCP_PORT:-8080}"

exec python -m nas_mcp_server
