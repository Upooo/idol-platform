#!/usr/bin/env bash
# =============================================================
# IDOL Platform — First-time VPS Setup
# =============================================================
# Supports Ubuntu 20.04+ / Debian 11+
# Automatically installs Python 3.10+ via deadsnakes PPA if needed.
#
# Usage:
#   ssh root@VPS_IP
#   git clone https://github.com/Upooo/idol-platform.git /opt/idol-platform
#   sudo bash /opt/idol-platform/scripts/setup.sh
# =============================================================
set -euo pipefail

APP_DIR="/opt/idol-platform"
APP_USER="idol"
MIN_PYTHON_MINOR=10  # minimum Python 3.10

echo "========================================"
echo "  IDOL Platform — VPS Setup"
echo "========================================"

# --- Helper: find a suitable Python >= 3.MIN_PYTHON_MINOR ---
find_python() {
    # Check from newest to oldest
    for minor in 12 11 10; do
        if [ "$minor" -lt "$MIN_PYTHON_MINOR" ]; then
            continue
        fi
        local cmd="python3.${minor}"
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return 0
        fi
    done

    # Check generic python3
    if command -v python3 &>/dev/null; then
        local ver
        ver=$(python3 -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
        if [ "$ver" -ge "$MIN_PYTHON_MINOR" ]; then
            echo "python3"
            return 0
        fi
    fi

    return 1
}

# --- 1. System dependencies ---
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq software-properties-common git curl

# --- 2. Ensure Python >= 3.10 ---
echo "[2/7] Checking Python version..."

PYTHON_CMD=""
if find_python &>/dev/null; then
    PYTHON_CMD=$(find_python)
    echo "  Found: $PYTHON_CMD ($($PYTHON_CMD --version))"
else
    echo "  System Python is too old. Installing via deadsnakes PPA..."
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y -qq python3.10 python3.10-venv python3.10-dev
    PYTHON_CMD="python3.10"
    echo "  Installed: $PYTHON_CMD ($($PYTHON_CMD --version))"
fi

# Ensure venv module is available
VENV_PKG="${PYTHON_CMD}-venv"
if ! $PYTHON_CMD -m venv --help &>/dev/null 2>&1; then
    echo "  Installing ${VENV_PKG}..."
    apt-get install -y -qq "${VENV_PKG}" 2>/dev/null || \
        apt-get install -y -qq python3-venv 2>/dev/null || true
fi

echo "  Using: $PYTHON_CMD ($($PYTHON_CMD --version))"

# --- 3. Install Docker (for PostgreSQL) ---
echo "[3/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "  Docker installed."
else
    echo "  Docker already installed, skipping."
fi

if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi

# --- 4. Create app user ---
echo "[4/7] Creating app user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$APP_DIR" "$APP_USER"
    usermod -aG docker "$APP_USER"
    echo "  Created user: $APP_USER"
else
    usermod -aG docker "$APP_USER" 2>/dev/null || true
    echo "  User $APP_USER already exists."
fi

# --- 5. Python venv + dependencies ---
echo "[5/7] Setting up Python environment..."
cd "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo -u "$APP_USER" $PYTHON_CMD -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -e "$APP_DIR" -q
echo "  Dependencies installed."

# --- 6. Setup .env + Start PostgreSQL ---
echo "[6/7] Environment & database..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo ""
    echo "  ⚠️  EDIT /opt/idol-platform/.env BEFORE starting!"
    echo "  Required: HQ_BOT_TOKEN, FOUNDER_TELEGRAM_ID"
    echo ""
else
    echo "  .env already exists."
fi

cd "$APP_DIR"
sudo -u "$APP_USER" docker compose up -d db
echo "  Waiting for PostgreSQL..."
for i in {1..30}; do
    if sudo -u "$APP_USER" docker compose exec -T db pg_isready -U idol -d idol_db &>/dev/null; then
        echo "  PostgreSQL ready!"
        break
    fi
    sleep 1
    [ "$i" -eq 30 ] && echo "  ⚠️  PostgreSQL slow to start. Check: docker compose logs db"
done

# --- 7. Install systemd service ---
echo "[7/7] Installing systemd service..."
cp "$APP_DIR/deploy/idol.service" /etc/systemd/system/idol.service
systemctl daemon-reload
systemctl enable idol
echo "  Service installed and enabled."

echo ""
echo "========================================"
echo "  Setup complete!  (Python: $($PYTHON_CMD --version))"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit config:      sudo nano /opt/idol-platform/.env"
echo "  2. Run migration:    sudo -u idol /opt/idol-platform/.venv/bin/alembic -c /opt/idol-platform/alembic.ini upgrade head"
echo "  3. Start bot:        sudo systemctl start idol"
echo "  4. Check status:     sudo systemctl status idol"
echo "  5. View logs:        sudo journalctl -u idol -f"
echo ""
