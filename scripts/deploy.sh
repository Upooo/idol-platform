#!/usr/bin/env bash
# =============================================================
# IDOL Platform — Deploy (pull + migrate + restart)
# =============================================================
# Usage: sudo bash scripts/deploy.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"

echo "=== IDOL Deploy ==="

# Pull latest
echo "[1/3] Pulling latest code..."
cd "$APP_DIR"
sudo -u "$APP_USER" git pull origin main

# Install deps (in case requirements.txt changed)
echo "[2/3] Updating dependencies..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r requirements.txt -q

# Run migrations
echo "[3/3] Running migrations..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/alembic" -c "$APP_DIR/alembic.ini" upgrade head

# Restart service
echo "Restarting service..."
systemctl restart idol

echo ""
echo "✅ Deploy complete!"
echo "Status: systemctl status idol"
echo "Logs:   journalctl -u idol -f"
