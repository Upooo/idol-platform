#!/usr/bin/env bash
# =============================================================
# IDOL Platform — First-time VPS Setup
# =============================================================
# Usage: curl the repo, then run this script.
#   sudo bash scripts/setup.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"
REPO_URL="https://github.com/Upooo/idol-platform.git"

echo "========================================"
echo "  IDOL Platform — VPS Setup"
echo "========================================"

# --- 1. System dependencies ---
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib git curl

# --- 2. Create app user ---
echo "[2/7] Creating app user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$APP_DIR" "$APP_USER"
    echo "  Created user: $APP_USER"
else
    echo "  User $APP_USER already exists, skipping."
fi

# --- 3. Clone repo ---
echo "[3/7] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  Repo already exists, pulling latest..."
    cd "$APP_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --- 4. Python venv + dependencies ---
echo "[4/7] Setting up Python environment..."
sudo -u "$APP_USER" python3.11 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
echo "  Dependencies installed."

# --- 5. Setup .env ---
echo "[5/7] Environment config..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo ""
    echo "  ⚠️  IMPORTANT: Edit /opt/idol-platform/.env before starting!"
    echo "  Required: HQ_BOT_TOKEN, FOUNDER_TELEGRAM_ID, DATABASE_URL"
    echo ""
else
    echo "  .env already exists, skipping."
fi

# --- 6. PostgreSQL database ---
echo "[6/7] Setting up PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='idol'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER idol WITH PASSWORD 'idol_secret';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='idol_db'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE idol_db OWNER idol;"
echo "  Database ready. (Change the default password in production!)"

# --- 7. Install systemd service ---
echo "[7/7] Installing systemd service..."
cp "$APP_DIR/deploy/idol.service" /etc/systemd/system/idol.service
systemctl daemon-reload
systemctl enable idol
echo "  Service installed and enabled."

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit config:      sudo nano /opt/idol-platform/.env"
echo "  2. Run migration:    sudo -u idol /opt/idol-platform/.venv/bin/alembic -c /opt/idol-platform/alembic.ini upgrade head"
echo "  3. Start bot:        sudo systemctl start idol"
echo "  4. Check status:     sudo systemctl status idol"
echo "  5. View logs:        sudo journalctl -u idol -f"
echo ""
