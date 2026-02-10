#!/bin/bash
# Install the BR daemon as a user systemd service.
# Usage: bash scripts/install_br_service.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="priapos"
SERVICE_FILE="$PROJECT_DIR/systemd/$SERVICE_NAME.service"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "Installing $SERVICE_NAME service..."
echo "  Project: $PROJECT_DIR"

# Ensure .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ERROR: $PROJECT_DIR/.env not found."
    echo "Create it with LEEKWARS_USER and LEEKWARS_PASS."
    exit 1
fi

# Create user systemd directory
mkdir -p "$USER_SYSTEMD_DIR"

# Symlink service file (so updates auto-apply)
ln -sf "$SERVICE_FILE" "$USER_SYSTEMD_DIR/$SERVICE_NAME.service"
echo "  Linked: $USER_SYSTEMD_DIR/$SERVICE_NAME.service"

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
echo "  Enabled: $SERVICE_NAME"

echo ""
echo "Commands:"
echo "  systemctl --user start $SERVICE_NAME    # Start now"
echo "  systemctl --user stop $SERVICE_NAME     # Stop"
echo "  systemctl --user status $SERVICE_NAME   # Check status"
echo "  journalctl --user -u $SERVICE_NAME -f   # Follow logs"
echo "  tail -f $PROJECT_DIR/logs/br_daemon.log # File logs"
