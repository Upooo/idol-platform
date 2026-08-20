#!/usr/bin/env bash
# =============================================================
# IDOL Platform — Deploy (pull + migrate + restart)
# =============================================================
# Usage: sudo bash /opt/idol-platform/scripts/deploy.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"
PIP="$APP_DIR/.venv/bin/python -m pip"

echo "=== IDOL Deploy ==="

# Ensure PostgreSQL is running
echo "[1/4] Checking PostgreSQL..."
cd "$APP_DIR"
sudo -u "$APP_USER" docker compose up -d db
sleep 2

# Pull latest
echo "[2/4] Pulling latest code..."
sudo -u "$APP_USER" git pull origin main

# Update build tools + deps
echo "[3/4] Updating dependencies..."
sudo -u "$APP_USER" $PIP install --upgrade pip "setuptools>=68" wheel -q
sudo -u "$APP_USER" $PIP install -e "$APP_DIR" -q

# Migrations
echo "[4/4] Running migrations..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/alembic" -c "$APP_DIR/alembic.ini" upgrade head

# Restart
systemctl restart idol

echo ""
echo "✅ Deploy complete!"
echo "Status: systemctl status idol"
echo "Logs:   journalctl -u idol -f"
