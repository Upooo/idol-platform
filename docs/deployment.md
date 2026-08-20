# Deployment Guide — IDOL Platform

## Prerequisites

- VPS dengan Ubuntu 22.04+ (atau Debian 12+)
- Python 3.11+
- PostgreSQL 16+
- Akses root/sudo

## Quick Setup (Pertama Kali)

### 1. SSH ke VPS lu

```bash
ssh root@IP_VPS_LU
```

### 2. Clone repo & jalanin setup script

```bash
git clone https://github.com/Upooo/idol-platform.git /opt/idol-platform
cd /opt/idol-platform
sudo bash scripts/setup.sh
```

Script ini otomatis:
- Install Python 3.11, PostgreSQL, git
- Bikin user `idol` (non-root, lebih aman)
- Clone repo ke `/opt/idol-platform`
- Setup Python venv + install dependencies
- Copy `.env.example` → `.env`
- Bikin database PostgreSQL (`idol_db`)
- Install systemd service (`idol.service`)

### 3. Edit config

```bash
sudo nano /opt/idol-platform/.env
```

Yang WAJIB diisi:
```
HQ_BOT_TOKEN=token_dari_botfather
FOUNDER_TELEGRAM_ID=telegram_id_lu
DATABASE_URL=postgresql+asyncpg://idol:idol_secret@localhost:5432/idol_db
```

Opsional (IDOL TEAM group):
```
IDOL_TEAM_GROUP_ID=-100xxxxxxxxxx
TOPIC_SYSTEM_ID=2
TOPIC_ORDERS_ID=3
TOPIC_STAFF_ID=4
```

### 4. Jalanin migration

```bash
sudo -u idol /opt/idol-platform/.venv/bin/alembic \
    -c /opt/idol-platform/alembic.ini upgrade head
```

### 5. Start bot

```bash
sudo systemctl start idol
```

Done! Bot jalan 24/7.

---

## Commands yang Perlu lu Tau

### Status & Logs

```bash
# Cek status bot (running/stopped/error)
sudo systemctl status idol

# Lihat log realtime (CTRL+C buat keluar)
sudo journalctl -u idol -f

# Lihat 50 baris log terakhir
sudo journalctl -u idol -n 50

# Lihat log hari ini aja
sudo journalctl -u idol --since today
```

### Start / Stop / Restart

```bash
sudo systemctl start idol      # Nyalain
sudo systemctl stop idol       # Matiin
sudo systemctl restart idol    # Restart
```

### Update / Deploy

Setiap kali lu push update ke GitHub:

```bash
sudo bash /opt/idol-platform/scripts/deploy.sh
```

Script ini otomatis: `git pull` → install deps → migrate → restart service.

---

## Kenapa Systemd, Bukan Tmux?

| | tmux | systemd |
|---|---|---|
| VPS reboot | ❌ Bot mati, harus manual start | ✅ Auto start |
| Bot crash | ❌ Mati total | ✅ Auto restart dalam 5 detik |
| Lihat log | Harus attach tmux | `journalctl -u idol -f` dari mana aja |
| Lupa SSH | Bisa lupa bot mati | Ga mungkin lupa, auto jalan |
| Multiple bot | Banyak tmux session | 1 service per bot, rapi |

---

## Struktur di VPS

```
/opt/idol-platform/          ← app directory
├── .env                     ← config (chmod 600, aman)
├── .venv/                   ← Python virtual environment
├── src/                     ← source code
├── alembic/                 ← database migrations
├── deploy/
│   └── idol.service         ← systemd service file
├── scripts/
│   ├── setup.sh             ← first-time setup
│   └── deploy.sh            ← update & restart
└── ...
```

---

## Troubleshooting

### Bot ga mau start
```bash
# Cek error detail
sudo journalctl -u idol -n 30 --no-pager

# Biasanya:
# - .env belum diisi → edit .env
# - Database belum ada → jalanin migration
# - Token salah → cek BOT_TOKEN
```

### Database error
```bash
# Cek PostgreSQL jalan
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test koneksi
sudo -u idol psql -U idol -d idol_db -c "SELECT 1;"
```

### Permission error
```bash
# Fix ownership
sudo chown -R idol:idol /opt/idol-platform

# Fix .env permission
sudo chmod 600 /opt/idol-platform/.env
```

### Update systemd service file
```bash
# Kalau edit deploy/idol.service
sudo cp /opt/idol-platform/deploy/idol.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart idol
```

---

## Security Notes

- Bot jalan sebagai user `idol` (bukan root) — lebih aman
- `.env` di-chmod 600 — cuma user idol yang bisa baca
- systemd `ProtectSystem=strict` — bot ga bisa nulis ke system files
- `NoNewPrivileges=true` — ga bisa escalate permission
- Database password default `idol_secret` — **GANTI di production!**
