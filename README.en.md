# Pi Console

**Homelab dashboard** for Raspberry Pi: UPS, network, Proxmox, Wake-on-LAN and administration in one panel, with no external dependencies (standard-library Python + nginx).

[Versión en español → README.md](README.md)

<img src="docs/screenshots/1920x1080/light/overview.png" alt="Overview" width="900">

## Modules

Default menu order (each user can reorder it):

| Module | Port | Path | Description |
|---|---|---|---|
| **Overview** | 8085 | `/overview/` | One screen with the key points of UPS, Proxmox and network, the Pi's status and an event timeline; kiosk mode |
| **UPS Monitor** | 8081 | `/nut/` | UPS monitor via NUT — battery, load, runtime, power, voltages, temperature (if the UPS reports it), clients, history charts, CSV export |
| **Net Monitor** | 8083 | `/net/` | Network scanner — hosts, device type, OS, ports, MAC/vendor (ARP, Pi-hole, SNMP) |
| **Proxmox Monitor** | 8084 | `/pve/` | Proxmox VE cluster dashboard — nodes, VMs, CTs and Ceph |
| **WOL Console** | 8080 | `/wol/` | Wake-on-LAN — power on machines remotely |
| **Admin Panel** | 8082 | `/admin/` | Users and permissions, backups (Teleporter) and system health |

More screenshots (light/dark, 4 resolutions) are in [`docs/screenshots/`](docs/screenshots/).

## Overview page

`/overview/` shows, on one screen: a global status (all good / attention / failure) with a list of what needs attention; each UPS (state, battery, load, runtime, watts, 24 h load chart and, if the UPS reports it, a temperature chart); each Proxmox cluster (nodes online, running VMs/CTs, CPU/memory, Ceph health, 12 h CPU and memory chart); Net Monitor (hosts online/known/offline, last scan, device types, new devices in the last 48 h); the Raspberry Pi itself (temperature, CPU, memory, disk, uptime, power supply; on a real Raspberry Pi only, also a 24 h temperature history with red marks for under-voltage and amber for throttling, kept in the `/var/lib/pi-console/metrics.db` database for 7 days, `PICONSOLE_PI_KEEP_DAYS` changes it); and an **event timeline** (UPS on battery or mains back, Proxmox node down/up, Ceph health changes, new or vanished hosts). Events are recorded by the modules themselves, so they are kept even when nobody has the page open (last 300 events / 30 days in `/var/lib/pi-console/events.json`). Everyone sees only the cards and events of the modules they can access; the page refreshes every 10 s.

**Kiosk mode:** the *Kiosk* button (or `/overview/?kiosk=1`) goes full screen with large text, no buttons or cursor, and keeps the screen awake. Meant for a fixed monitor or tablet; moving the mouse or touching the screen shows an exit button. Text size adapts to the screen (7" tablet, laptop, monitor); adjust it with `?zoom=0.8` (0.5 to 2). If the content doesn't fit, the *Auto-scroll* button (it shows up next to *Exit kiosk* when the screen is touched) makes it scroll slowly up and down by itself; it starts off and pauses for 30 s when the screen is touched. With `?autoscroll=1` it starts on. Example: `/overview/?kiosk=1&zoom=0.9`. The session renews itself while the page is open, so a read-only user is advisable. While Overview is open, Proxmox Monitor polls its clusters every 5 s (as it does with its own page open).

## Requirements

Raspberry Pi OS, DietPi or Debian 12+ (also works on an x86 VM), Python 3.9+, nginx, NUT (`nut`, `nut-client`), `snmp`, `sudo`. `apt` installs all of them.

## Install

```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1d/pi-console_1.2.1d_all.deb
sudo apt-get update
sudo apt-get install -y ./pi-console_1.2.1d_all.deb
```

Then open `http://<pi-ip>/`. The installer prints the initial user `admin` with a **random password** (it is also in `/var/lib/pi-console/initial-admin-password` until changed); you **must set a new password** on first login. UPS Monitor starts with no servers, and Net Monitor scans nothing until you press "Run initial scan".

## Update

Install the new `.deb` the same way. Data in `/var/lib/pi-console` is kept (a copy also goes to `/var/backups/pi-console`). Installing a *lower* version number than the one you have needs `--allow-downgrades`.

## Operations

```bash
pi-console-health            # health summary (exit 0 ok, 1 degraded, 2 failed)
pi-console-resources         # memory and CPU per service
journalctl -u net-monitor -f # logs (services: wol-console, pi-console-ups, admin-panel, net-monitor, proxmox-monitor, pi-console-overview)
sudo teleporter backup ~/backup.tar.gz   # backup / check / restore
```

Settings are environment variables in `/etc/default/pi-console` (`NUT_POLL`, `SCAN_NETWORK`, `SCAN_INTERVAL`, `PICONSOLE_SECURE_COOKIE`…; see the Spanish README for the full table). `apt remove` keeps your data; `apt purge` removes code, services and the system user but leaves `/var/lib/pi-console` and `/var/backups/pi-console`.

## Automatic SFTP backup

Teleporter backups also include the **Overview chart histories**: UPS temperature (in its `history.db`) and Proxmox CPU/memory plus Pi temperature/under-voltage (in `metrics.db`). Backups from version 1.2.0o (which kept that data as JSON) restore too and the data is imported automatically. Older backups without those files stay valid: the current ones are kept.

A daily cron job (03:17) makes a Teleporter backup, **verifies it before uploading**, and sends it over SFTP to a storage server (`storage.example.lan` by default). It ships **disabled** until a user is set. It uses an SSH key only (never a password), so it can run unattended.

```bash
sudo pi-console-sftp-backup setup     # creates the SSH key and shows the public key to authorize on the storage
sudo nano /etc/pi-console/backup.conf   # set SFTP_USER (and SFTP_DIR, SFTP_HOST if needed)
sudo pi-console-sftp-backup test      # checks connection, folder and write access
sudo pi-console-sftp-backup run       # make a backup now (cron does it by itself afterwards)
sudo pi-console-sftp-backup status    # result of the last run
journalctl -t pi-console-sftp-backup  # history / errors
```

It uploads as `.part` and renames when complete, then compares the remote size with the local one. It keeps 30 copies on the storage and 7 on the Pi, and only deletes files named `pi-console-auto-<host>-<date>_<time>.tar.gz`. The storage's host key is pinned on first use and a change makes the backup fail. The archive holds password hashes and tokens: use a dedicated SFTP user on a trusted storage. Restore with `teleporter restore` or the admin panel.

## Security

Designed for a **trusted LAN**, served over **plain HTTP on port 80**: do not expose it to the internet. HTTPS is one command away: `sudo pi-console-https enable` (self-signed certificate) or `--cert/--key` with your own, plus `--redirect` to redirect port 80, send HSTS and mark the cookie `Secure`. Python services listen on `127.0.0.1` only. Passwords (min. 8 characters) use scrypt; 5 failed logins from one IP within 10 minutes lock that IP for 5 minutes, with a per-account limit as well; the counters are shared by every module, and changing a password needs the current one. Session tokens are stored only as SHA-256 hashes and are never returned in the login JSON or included in backups; sessions last 24 h. nginx rate-limits requests and connections per IP and hides its version. The code in `/opt/pi-console` is root-owned and read-only for the services, their data lives in `/var/lib/pi-console/<module>/`, the systemd units are hardened, and the scripts that run as root never follow symlinks inside the services' folders. Hosts and names are validated and the Pi-hole certificate is pinned on first use. Known limit: the nginx CSP still allows `'unsafe-inline'` because the pages carry inline scripts and styles. The SFTP backup is encrypted with gpg (AES-256); keep a copy of `/etc/pi-console/backup_passphrase` off the Pi. Per-module permissions (none / read-only / execute / admin): an admin can only grant permissions on modules where they hold that level, and only admins of every module can use Teleporter from the panel. Proxmox clusters pin the certificate SHA-256 fingerprint.

Every request that changes data is rejected (403) when the browser says it is not same-origin (`Sec-Fetch-Site`, or `Origin` against `Host` in older browsers); `SameSite=Strict` alone did not stop another page on the same host and a different port.

## License

MIT — see [LICENSE](LICENSE). Created with the help of AI.
