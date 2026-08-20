#!/usr/bin/env bash
# =============================================================
# IDOL Platform — First-time VPS Setup
# =============================================================
# Usage:
#   ssh root@VPS_IP
#   git clone https://github.com/Upooo/idol-platform.git /opt/idol-platform
#   sudo bash /opt/idol-platform/scripts/setup.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"

echo "========================================"
echo "  IDOL Platform — VPS Setup"
echo "========================================"

# --- 1. System dependencies ---
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3.11 python3.11-venv python3-pip git curl

# --- 2. Install Docker (for PostgreSQL) ---
echo "[2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "  Docker installed."
else
    echo "  Docker already installed, skipping."
fi

# Install docker compose plugin if missing
if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi

# --- 3. Create app user ---
echo "[3/7] Creating app user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$APP_DIR" "$APP_USER"
    usermod -aG docker "$APP_USER"
    echo "  Created user: $APP_USER (added to docker group)"
else
    usermod -aG docker "$APP_USER" 2>/dev/null || true
    echo "  User $APP_USER already exists, ensured docker group."
fi

# --- 4. Python venv + dependencies ---
echo "[4/7] Setting up Python environment..."
cd "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
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
    echo "  ⚠️  EDIT /opt/idol-platform/.env BEFORE starting!"
    echo "  Required: HQ_BOT_TOKEN, FOUNDER_TELEGRAM_ID"
    echo ""
else
    echo "  .env already exists, skipping."
fi

# --- 6. Start PostgreSQL via Docker ---
echo "[6/7] Starting PostgreSQL (Docker)..."
cd "$APP_DIR"
sudo -u "$APP_USER" docker compose up -d db

# Wait for PostgreSQL to be ready
echo "  Waiting for PostgreSQL..."
for i in {1..30}; do
    if sudo -u "$APP_USER" docker compose exec -T db pg_isready -U idol -d idol_db &>/dev/null; then
        echo "  PostgreSQL ready!"
        break
    fi
    sleep 1
    if [ "$i" -eq 30 ]; then
        echo "  ⚠️  PostgreSQL didn't start in 30s. Check: docker compose logs db"
    fi
done

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
echo "PostgreSQL:"
echo "  Status:   docker compose -f /opt/idol-platform/docker-compose.yml ps"
echo "  Logs:     docker compose -f /opt/idol-platform/docker-compose.yml logs db"
echo "  Shell:    docker compose -f /opt/idol-platform/docker-compose.yml exec db psql -U idol -d idol_db"
echo ""
