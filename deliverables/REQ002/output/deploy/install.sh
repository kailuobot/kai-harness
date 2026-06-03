#!/usr/bin/env bash
# NAS MCP Server installation script
# Run this script on the target NAS (e.g., ZimaSpace Z4Pro)
# Usage: bash deploy/install.sh [install_dir]

set -euo pipefail

INSTALL_DIR="${1:-/opt/nas-mcp-server}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== NAS MCP Server Installer ==="
echo "Source directory: $SCRIPT_DIR"
echo "Install directory: $INSTALL_DIR"
echo ""

# Create install directory
echo "[1/4] Creating install directory..."
mkdir -p "$INSTALL_DIR"

# Create Python virtual environment
echo "[2/4] Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"
source "$INSTALL_DIR/.venv/bin/activate"

# Install dependencies
echo "[3/4] Installing dependencies..."
pip install --upgrade pip
pip install -e "$SCRIPT_DIR"

# Copy configuration template
echo "[4/4] Setting up configuration..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env"
    echo "  Created $INSTALL_DIR/.env from template."
    echo "  Please edit it to set NAS_ROOT_DIR to your NAS file path."
else
    echo "  $INSTALL_DIR/.env already exists, skipping."
fi

# Copy start script
cp "$SCRIPT_DIR/start.sh" "$INSTALL_DIR/start.sh"
chmod +x "$INSTALL_DIR/start.sh"

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit $INSTALL_DIR/.env to configure NAS_ROOT_DIR"
echo "  2. Test: $INSTALL_DIR/start.sh"
echo "  3. Register systemd service:"
echo "     sudo cp $SCRIPT_DIR/deploy/nas-mcp-server.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable --now nas-mcp-server"
