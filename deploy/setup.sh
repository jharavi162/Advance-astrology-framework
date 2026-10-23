#!/usr/bin/env bash
# One-time setup of HoraSutra on a fresh Ubuntu 24.04 server (run as root):
#
#   curl -fsSL https://raw.githubusercontent.com/jharavi162/Advance-astrology-framework/main/deploy/setup.sh -o setup.sh
#   bash setup.sh horasutra.in
#
# Installs Python + Caddy (automatic HTTPS), clones the repo to /opt/horasutra,
# asks for the secrets once (kept in /etc/horasutra/env, never in git), and
# starts three systemd units: the app, a 2-minute auto-update from GitHub
# main, and a daily backup of the saved readings. Safe to run again.
set -euo pipefail

DOMAIN="${1:-}"
REPO="${REPO:-https://github.com/jharavi162/Advance-astrology-framework.git}"
APP=/opt/horasutra
DATA=/var/lib/horasutra
ENVF=/etc/horasutra/env

[ "$(id -u)" = 0 ] || { echo "Run as root (sudo bash setup.sh <domain>)"; exit 1; }
[ -n "$DOMAIN" ] || { echo "Usage: bash setup.sh <domain>   e.g. bash setup.sh horasutra.in"; exit 1; }

echo "== Packages"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git caddy ufw

echo "== App user and folders"
id horasutra >/dev/null 2>&1 || useradd --system --home "$APP" --shell /usr/sbin/nologin horasutra
mkdir -p "$DATA/cards" /etc/horasutra /var/backups/horasutra
if [ ! -d "$APP/.git" ]; then git clone --depth 50 "$REPO" "$APP"; fi
git -C "$APP" config --global --add safe.directory "$APP" || true
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q --upgrade pip
"$APP/.venv/bin/pip" install -q -r "$APP/requirements.txt"
chown -R horasutra:horasutra "$APP" "$DATA"

echo "== Secrets (stored only in $ENVF, readable by root and the app)"
if [ ! -f "$ENVF" ]; then
  read -rsp "ANTHROPIC_API_KEY: " AK; echo
  read -rsp "PDF_UNLOCK_CODE (secret code for PDFs): " PC; echo
  umask 077
  cat > "$ENVF" <<ENV
ANTHROPIC_API_KEY=$AK
PDF_UNLOCK_CODE=$PC
CARD_DAILY_LIMIT=10
ASK_DAILY_LIMIT=3
CARD_CACHE_DIR=$DATA/cards
HOST=127.0.0.1
PORT=8000
ENV
  chgrp horasutra "$ENVF"; chmod 640 "$ENVF"
else
  echo "   $ENVF exists — kept as is (edit with: nano $ENVF)"
fi

echo "== systemd units"
install -m 644 "$APP/deploy/horasutra.service" /etc/systemd/system/
install -m 644 "$APP/deploy/horasutra-update.service" "$APP/deploy/horasutra-update.timer" /etc/systemd/system/
install -m 644 "$APP/deploy/horasutra-backup.service" "$APP/deploy/horasutra-backup.timer" /etc/systemd/system/
mkdir -p /var/log/journal                 # keep logs across reboots
systemctl restart systemd-journald
systemctl daemon-reload
systemctl enable --now horasutra.service horasutra-update.timer horasutra-backup.timer

echo "== HTTPS reverse proxy (Caddy) for $DOMAIN"
sed "s/__DOMAIN__/$DOMAIN/g" "$APP/deploy/Caddyfile" > /etc/caddy/Caddyfile
systemctl reload caddy || systemctl restart caddy

echo "== Firewall: SSH, HTTP, HTTPS only"
ufw allow OpenSSH; ufw allow 80/tcp; ufw allow 443/tcp; ufw --force enable

sleep 3
curl -fsS http://127.0.0.1:8000/api/health && echo "   app is up"
echo
echo "Done. Point the domain's A record to this server's IP; HTTPS starts by itself."
echo "Logs:    journalctl -u horasutra -f"
echo "Status:  systemctl status horasutra"
