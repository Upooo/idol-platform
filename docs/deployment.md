# Deployment Guide — IDOL Platform

## Arsitektur Deploy

```
VPS lu
├── PostgreSQL (Docker container, auto-restart)
├── IDOL Bot (systemd service, auto-restart)
└── .env (config, chmod 600)
```

## Prerequisites

- VPS Ubuntu 20.04+ atau Debian 11+
- **Python 3.10+** (di-install otomatis via deadsnakes PPA kalau belum ada)
- Akses root/sudo
- Docker (di-install otomatis sama setup script)

> **Note:** Ubuntu 20.04 bawaan cuma Python 3.8. Setup script otomatis
> install Python 3.10 via [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
> kalau Python lu kurang dari 3.10. Ga perlu manual.

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
- Cek Python version, install 3.10 via deadsnakes kalau kurang
- Install Docker + Docker Compose
- Bikin user `idol` (non-root)
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

### 4. Migration + Start

```bash
sudo -u idol /opt/idol-platform/.venv/bin/alembic \
    -c /opt/idol-platform/alembic.ini upgrade head

sudo systemctl start idol
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
cd /opt/idol-platform
docker compose ps                              # Cek status
docker compose exec db psql -U idol -d idol_db  # Masuk DB
docker compose logs db                          # Log database
docker compose restart db                       # Restart DB
```

### Update / Deploy

```bash
sudo bash /opt/idol-platform/scripts/deploy.sh
```

---

## Troubleshooting

### Bot ga mau start
```bash
sudo journalctl -u idol -n 30 --no-pager
```

### Database error
```bash
cd /opt/idol-platform
docker compose ps
docker compose logs db
docker compose restart db
```

### Python version error
```bash
# Cek Python di venv
/opt/idol-platform/.venv/bin/python --version
# Harus >= 3.10
```

### Permission error
```bash
sudo chown -R idol:idol /opt/idol-platform
sudo chmod 600 /opt/idol-platform/.env
```

### Reset database (HATI-HATI - data ilang)
```bash
cd /opt/idol-platform
docker compose down -v
docker compose up -d db
sleep 5
sudo -u idol /opt/idol-platform/.venv/bin/alembic \
    -c /opt/idol-platform/alembic.ini upgrade head
sudo systemctl restart idol
```

---

## Security Notes

- Bot jalan sebagai user `idol` (bukan root)
- `.env` di-chmod 600
- PostgreSQL cuma listen di 127.0.0.1
- systemd `ProtectSystem=strict`
- Database password default `idol_secret` — **GANTI di production!**
