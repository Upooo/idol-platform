#!/usr/bin/env bash
# =============================================================
# IDOL Platform — Deploy (pull + migrate + restart)
# =============================================================
# Usage: sudo bash /opt/idol-platform/scripts/deploy.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"

echo "=== IDOL Deploy ==="

# Ensure PostgreSQL is running
echo "[1/4] Checking PostgreSQL..."
cd "$APP_DIR"
sudo -u "$APP_USER" docker compose up -d db
sleep 2

# Pull latest
echo "[2/4] Pulling latest code..."
sudo -u "$APP_USER" git pull origin main

# Install deps (in case requirements.txt changed)
echo "[3/4] Updating dependencies..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r requirements.txt -q

# Run migrations
echo "[4/4] Running migrations..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/alembic" -c "$APP_DIR/alembic.ini" upgrade head

# Restart service
echo "Restarting service..."
systemctl restart idol

echo ""
echo "✅ Deploy complete!"
echo "Status: systemctl status idol"
echo "Logs:   journalctl -u idol -f"
