# Pi Console

**Homelab dashboard** for Raspberry Pi: UPS, network, Proxmox, Wake-on-LAN and administration in one panel, with no external dependencies (standard-library Python + nginx).

[Versión en español → README.md](README.md)

<img src="docs/screenshots/1920x1080/light/overview.png" alt="Overview" width="900">

## Modules

Default menu order (each user can reorder it):

| Module | Port | Path | Description |
|---|---|---|---|
| **Overview** | 8085 | `/overview/` | One screen with the key points of UPS, Proxmox and network, the Pi's status and an event timeline; kiosk mode |
| **UPS Monitor** | 8081 | `/nut/` | UPS monitor via NUT — battery, load, runtime, power, voltages, clients, history charts, CSV export |
| **Net Monitor** | 8083 | `/net/` | Network scanner — hosts, device type, OS, ports, MAC/vendor (ARP, Pi-hole, SNMP) |
| **Proxmox Monitor** | 8084 | `/pve/` | Proxmox VE cluster dashboard — nodes, VMs, CTs and Ceph |
| **WOL Console** | 8080 | `/wol/` | Wake-on-LAN — power on machines remotely |
| **Admin Panel** | 8082 | `/admin/` | Users and permissions, backups (Teleporter) and system health |

More screenshots (light/dark, 4 resolutions) are in [`docs/screenshots/`](docs/screenshots/).

## Overview page

`/overview/` shows, on one screen: a global status (all good / attention / failure) with a list of what needs attention; each UPS (state, battery, load, runtime, watts, 24 h chart); each Proxmox cluster (nodes online, running VMs/CTs, CPU/memory, Ceph health); Net Monitor (hosts online/known/offline, last scan, device types, new devices in the last 48 h); the Raspberry Pi itself (temperature, CPU, memory, disk, uptime, power supply); and an **event timeline** (UPS on battery or mains back, Proxmox node down/up, Ceph health changes, new or vanished hosts). Events are recorded by the modules themselves, so they are kept even when nobody has the page open (last 300 events / 30 days in `/var/lib/pi-console/events.json`). Everyone sees only the cards and events of the modules they can access; the page refreshes every 10 s.

**Kiosk mode:** the *Kiosk* button (or `/overview/?kiosk=1`) goes full screen with large text, no buttons or cursor, and keeps the screen awake. Meant for a fixed monitor or tablet; moving the mouse or touching the screen shows an exit button. Text size adapts to the screen (7" tablet, laptop, monitor); adjust it with `?zoom=0.8` (0.5 to 2). If the content doesn't fit, the *Auto-scroll* button (it shows up next to *Exit kiosk* when the screen is touched) makes it scroll slowly up and down by itself; it starts off and pauses for 30 s when the screen is touched. With `?autoscroll=1` it starts on. Example: `/overview/?kiosk=1&zoom=0.9`. The session renews itself while the page is open, so a read-only user is advisable. While Overview is open, Proxmox Monitor polls its clusters every 5 s (as it does with its own page open).

## Requirements

Raspberry Pi OS, DietPi or Debian 12+ (also works on an x86 VM), Python 3.9+, nginx, NUT (`nut`, `nut-client`), `snmp`, `sudo`. `apt` installs all of them.

## Install

```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.0j/pi-console_1.2.0j_all.deb
sudo apt-get update
sudo apt-get install -y ./pi-console_1.2.0j_all.deb
```

Then open `http://<pi-ip>/`. The initial user is `admin` / `admin`; you **must set a new password** on first login. UPS Monitor starts with no servers, and Net Monitor scans nothing until you press "Run initial scan".

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

## Security

Designed for a **trusted LAN**, served over **plain HTTP on port 80**: do not expose it to the internet; put an HTTPS proxy in front if you need to (and set `PICONSOLE_SECURE_COOKIE=1`). Python services listen on `127.0.0.1` only. Passwords use scrypt; 5 failed logins from one IP within 10 minutes lock that IP for 5 minutes; sessions last 24 h. Per-module permissions (none / read-only / execute / admin): an admin can only grant permissions on modules where they hold that level, and only admins of every module can use Teleporter from the panel. Proxmox clusters pin the certificate SHA-256 fingerprint.

## License

MIT — see [LICENSE](LICENSE). Created with the help of AI.
