# Deploying HoraSutra on your own server

One Ubuntu 24.04 server (2 GB RAM is comfortable) and a domain.

1. Create the server (DigitalOcean Bangalore, AWS Lightsail Mumbai, Hetzner …)
   and open its web console or SSH in as root.
2. Run:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/jharavi162/Advance-astrology-framework/main/deploy/setup.sh -o setup.sh
   bash setup.sh yourdomain.in
   ```

   It asks for `ANTHROPIC_API_KEY` and `PDF_UNLOCK_CODE` once and stores them
   in `/etc/horasutra/env` (root + app only; never in git).
3. At the domain registrar, add two **A records** — `@` and `www` — pointing to
   the server's IP. HTTPS turns on by itself within a few minutes.

What runs:

| Unit | What it does |
|---|---|
| `horasutra.service` | the app on 127.0.0.1:8000 (restarts on crash/boot) |
| Caddy | HTTPS on 443 → the app; access log in `/var/log/caddy/` |
| `horasutra-update.timer` | every 2 min: pulls GitHub `main`; restarts only if the new code imports |
| `horasutra-backup.timer` | daily tarball of `/var/lib/horasutra` (saved readings, PDFs), 14 kept |

Everyday commands:

```bash
journalctl -u horasutra -f          # live app log (incl. the [card] usage lines)
systemctl status horasutra          # is it running
nano /etc/horasutra/env && systemctl restart horasutra   # change a secret/limit
bash /opt/horasutra/deploy/update.sh                    # update now
ls /var/backups/horasutra           # backups
```

Saved readings and PDFs live in `/var/lib/horasutra/cards` and survive
deploys and reboots (unlike Render's free plan).
