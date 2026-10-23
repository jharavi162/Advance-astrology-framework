#!/usr/bin/env bash
# Pull GitHub main and restart the app when it changed (run by
# horasutra-update.timer every 2 minutes; safe to run by hand).
# New code is test-imported in a scratch copy first, so a broken commit never
# replaces the running version on disk.
set -euo pipefail
APP="${APP:-/opt/horasutra}"
cd "$APP"
git fetch -q origin main
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] && exit 0

TRY=$(mktemp -d); trap 'rm -rf "$TRY"' EXIT
git archive origin/main | tar -x -C "$TRY"
if ! cmp -s requirements.txt "$TRY/requirements.txt"; then
  "$APP/.venv/bin/pip" install -q -r "$TRY/requirements.txt"
fi
if ! (cd "$TRY" && "$APP/.venv/bin/python" -c "import webapp.server"); then
  echo "update: $(git rev-parse --short origin/main) does not import — keeping $(git rev-parse --short HEAD)"
  exit 1
fi

git reset -q --hard origin/main                 # this copy is deploy-only
chown -R horasutra:horasutra "$APP" 2>/dev/null || true
systemctl restart horasutra
echo "update: now at $(git log -1 --format='%h %s')"
