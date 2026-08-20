# Deployment Guide — IDOL Platform

## Arsitektur Deploy

```
VPS lu
├── PostgreSQL (Docker container, auto-restart)
├── IDOL Bot (systemd service, auto-restart)
└── .env (config, chmod 600)
```

PostgreSQL jalan di Docker biar ga perlu install/config manual.
Bot jalan di systemd biar auto-restart + auto-start on boot.

## Prerequisites

- VPS Ubuntu 22.04+ (atau Debian 12+)
- Python 3.11+
- Akses root/sudo
- Docker (di-install otomatis sama setup script)

## Quick Setup (Pertama Kali)

### 1. SSH ke VPS

```bash
ssh root@IP_VPS_LU
```

### 2. Clone repo & jalanin setup

```bash
git clone https://github.com/Upooo/idol-platform.git /opt/idol-platform
cd /opt/idol-platform
sudo bash scripts/setup.sh
```

Script ini otomatis:
- Install Python 3.11, git, curl
- Install Docker + Docker Compose
- Bikin user `idol` (non-root, aman)
- Setup Python venv + install dependencies
- Copy `.env.example` → `.env`
- Start PostgreSQL di Docker (auto-restart)
- Install systemd service

### 3. Edit config

```bash
sudo nano /opt/idol-platform/.env
```

Yang WAJIB diisi:
```
HQ_BOT_TOKEN=token_dari_botfather
FOUNDER_TELEGRAM_ID=telegram_id_lu
```

DATABASE_URL udah default ke PostgreSQL Docker:
```
DATABASE_URL=postgresql+asyncpg://idol:idol_secret@localhost:5432/idol_db
```

Opsional (IDOL TEAM group):
```
IDOL_TEAM_GROUP_ID=-100xxxxxxxxxx
TOPIC_SYSTEM_ID=2
TOPIC_ORDERS_ID=3
TOPIC_STAFF_ID=4
```

### 4. Migration + Start

```bash
# Jalanin migration
sudo -u idol /opt/idol-platform/.venv/bin/alembic \
    -c /opt/idol-platform/alembic.ini upgrade head

# Start bot
sudo systemctl start idol

# Cek jalan
sudo systemctl status idol
```

Done! Bot + database jalan 24/7.

---

## Commands Sehari-hari

### Bot

```bash
sudo systemctl status idol       # Cek status
sudo systemctl restart idol      # Restart
sudo systemctl stop idol         # Stop
sudo journalctl -u idol -f       # Log realtime
sudo journalctl -u idol -n 50    # 50 baris terakhir
```

### Database

```bash
# Cek PostgreSQL container
cd /opt/idol-platform
docker compose ps

# Log database
docker compose logs db

# Masuk psql shell
docker compose exec db psql -U idol -d idol_db

# Restart database
docker compose restart db
```

### Update / Deploy

Setiap kali push update ke GitHub:

```bash
sudo bash /opt/idol-platform/scripts/deploy.sh
```

Satu command: cek db → git pull → deps → migrate → restart.

---

## Troubleshooting

### Bot ga mau start
```bash
sudo journalctl -u idol -n 30 --no-pager
# Biasanya: .env belum diisi, database belum ready, token salah
```

### Database error
```bash
cd /opt/idol-platform
docker compose ps          # Cek container status
docker compose logs db     # Cek error
docker compose restart db  # Restart
```

### Permission error
```bash
sudo chown -R idol:idol /opt/idol-platform
sudo chmod 600 /opt/idol-platform/.env
```

### Reset database (HATI-HATI - data ilang)
```bash
cd /opt/idol-platform
docker compose down -v     # Hapus container + data
docker compose up -d db    # Bikin ulang
# Tunggu 5 detik
sudo -u idol /opt/idol-platform/.venv/bin/alembic \
    -c /opt/idol-platform/alembic.ini upgrade head
sudo systemctl restart idol
```

---

## Security Notes

- Bot jalan sebagai user `idol` (bukan root)
- `.env` di-chmod 600 (cuma idol yang bisa baca)
- PostgreSQL cuma listen di 127.0.0.1 (ga bisa diakses dari luar)
- systemd `ProtectSystem=strict` (bot ga bisa nulis ke system files)
- Database password default `idol_secret` — **GANTI di production!**
