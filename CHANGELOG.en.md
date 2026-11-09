# Changelog (English)

English version of the release notes, from 2.0 on. The full history, including development builds, is in [CHANGELOG.md](CHANGELOG.md) (Spanish).

## 2.1.9 — 2026-11-09

### New module: Uptime Monitor
- **New:** Uptime Monitor (`/uptime/`, service `labtower-uptime`). Checks services over HTTP(S), TCP and DNS at an interval (60 s by default, from 20 s to 1 h). HTTP(S): expected response code and optional keyword. DNS: A or AAAA record, with the server's resolver or a given one, and an optional expected IP.
- **New:** a service is marked down after 3 failures in a row (configurable from 1 to 6); until then it shows "Pending".
- **New:** a bar with the last 50 checks, 24 h, 7 and 30-day availability, and a response-time chart with ranges and comparison with the previous period.
- **New:** HTTPS certificate expiry, warning 14 days ahead. "Do not verify the certificate" accepts self-signed ones and still checks the expiry.
- **New:** monitors are reordered by dragging (↑ ↓ buttons on touch screens).
- **New:** per-user "Uptime Monitor" permission. On upgrade, whoever administers WOL becomes administrator and the rest get read-only. It is included in backups and can be turned off with `labtower-modules`.
- **New:** Overview: Uptime card and events for down, recovered and certificate expiring or expired.

### Overview and all modules
- **Improvement:** each module's "Attention" notice shows the detail of what is failing. Proxmox with a failed read no longer shows as OK, and the NAS, DNS, VPN, Uptime and unresponsive-module notices include the error.
- **Fix:** on refresh, the page jumped to another position in Safari (iPhone, iPad and Mac). The view now stays put in every module.
- **Fix:** layout at every resolution, down to 320 px: charts, tables, figure cards and long texts fit their card's width instead of overlapping or spilling out.
- **Fix:** a HEAD or malformed request left an error in the journal and dropped the connection. Every service now answers 501.

### Installed app (iPhone, iPad, Android)
- **New:** when the server does not answer, it shows "No connection to LabTower" and retries on its own. HTTPS only; it stores no data.
- **New:** pulling down from the top reloads the page.
- **Improvement:** the status bar follows the theme chosen in LabTower and the launch screen is light or dark according to the device theme.

### Proxmox Monitor
- **New:** ✎ button to edit a cluster (name, host, port, user and token) without restarting. An empty secret keeps the stored one; if the host or port changes, the certificate must be confirmed.
- **New:** if the cluster certificate changed, the page explains it and offers "Pin certificate again", also when there is no data. Until it is confirmed, the token is not sent.
- **Fix:** if a read fails, the page shows the error and the time of the data on screen, instead of old data without notice.
- **Fix:** node charts are laid out in 4, 2 or 1 column depending on the width, with aligned headers.

### NAS Monitor
- **New:** expiry of each NAS's TLS certificates, on the ports you choose. Warning at 14 days and critical at 3, adjustable. Daily check and a "Check now" button.
- **New:** Overview: alerts and events for NAS certificates expiring, expired and renewed.

### UPS Monitor
- **New:** runtime chart per UPS, in minutes, with the battery and load in the tooltip. Only shown if the UPS reports its runtime.
- **Improvement:** NUT servers with an error are shown above the table.

### WAN Monitor
- **New:** in "Quality and availability", "LAN outages" and "WAN outages" columns next to the total.
- **Security:** the router certificate fingerprint is pinned. If it changes, the connection is dropped before the user and password are sent; saving the router settings learns it again.

### Net Monitor and Switch Monitor
- **New:** a warning when a switch port stays below its usual speed (for example 1G to 100M from a cable or a stuck port), in Net Monitor and in the Overview.
- **New:** a switch can be paused without deleting it, useful when another LabTower install already watches it: these switches allow a single session.
- **Fix:** "SessionExpired" right after logging in to a switch, caused by an old cookie sent along with the new one.
- **Fix:** the Pi-hole dot stayed grey even when connected. It now shows the real state: green connected, orange failing, grey not configured.
- **Fix:** after a failure, Pi-hole did not reconnect until the next scan. It now retries on its own.
- **Improvement:** the last scan's error is shown.

### Code
- **Improvement:** code cleanup. Errors that used to be lost are now logged, and file and command reads catch only the expected errors.

## 2.1.8 — 2026-11-05

- **Change:** all services are now named `labtower-<module>`: labtower-wol, labtower-auth, labtower-net, labtower-pve, labtower-nas, labtower-dns, labtower-wan and labtower-vpn (labtower-ups and labtower-overview are unchanged). On upgrade the installer removes the old names; your data is not touched. Example: `journalctl -u labtower-wan`.
- **Improvement:** new per-user permission, "View serial numbers" (yes/no), for UPS, NAS, disks and Proxmox nodes. Without it the server does not send that data to the browser. New users get it set to "no"; on upgrade, WOL and UPS administrators keep it.
- **Improvement:** Proxmox Monitor: clicking a node's name opens its full detail, with charts by range. If the node has the PVE mods add-on, it shows temperatures and fans grouped as in Proxmox: CPU thermal state per core (with max and critical), NVMe temperatures by model, other temperatures and fan speeds in RPM, plus "Sensor Mod Version" and "Information". Requires PVE mods installed on each node (see README).
- **Fix:** Proxmox Monitor: services that are off on purpose (`syslog`, `systemd-timesyncd`…) no longer show as "dead". A summary is shown and only the ones that should be running or failed are marked red.
- **Improvement:** WAN Monitor: speed test chart with ranges (1 h, 1 day, 1 week, 1 month, all). The test period is set in minutes or hours (minimum 5 minutes); under 30 minutes a warning says it can saturate the link quickly. Values you had saved in hours are converted automatically.
- **Fix:** WAN Monitor no longer queries DNS every time it reads its configuration. Before, it sent the network's DNS one query to api.ipify.org and two to speed.cloudflare.com every few seconds (tens of thousands a day). Now the name is resolved when saving and once before connecting.
- **Improvement:** Net Monitor: the switch temperature chart has ranges (1 h, 1 day, 1 week, 1 month, all).
- **Improvement:** DNS Monitor: "Queries per hour" with ranges (1 day, 1 week, 1 month, all) and a new per-client activity chart (Pi-hole).
- **Fix:** the IP card no longer offers Net Monitor for this same machine (127.0.0.1, ::1, localhost), for example on UPS Monitor clients.
- **Improvement:** the LabTower version appears in the footer of every page, including kiosk, home and password change.
- **Improvement:** Overview: the 2FA code field on the login sits under the password and disappears after signing in; the module buttons row was removed (the "Only with problems" filter stays); in the classic menu the title carries the LabTower icon, the module strip fits on one line with short names (UPS, Net, WOL, Admin) and the top bar lines up with the cards; in kiosk mode, VPN Monitor's "N connected" stays on one line.
- **Improvement:** on mobile, the bottom bar of every section has a "Sign out" button.
- **Change:** WOL Console: removed "Export JSON" from the Actions menu and the "v2" under the name.
- **Fix:** installer: upgrading no longer hands all data back to the "labtower" user (it printed "data of a previous installation handed back to labtower" on every upgrade). That only happens after a purge.
- **Fix:** auth, labtower-resetpw and Net Monitor load on Python 3.9, the package's minimum version ("X | None" annotations). A new test checks the packaged code against the 3.9 grammar.
- **Fix:** the SFTP backup status was left empty every hour on servers with the log in RAM (DietPi empties /var/log). The status, the verification result and the restore log are now kept in /var/lib/labtower/state and migrate automatically on upgrade. If the status file is empty, `labtower-sftp-backup status` and the panel treat it as "not run yet" instead of "unreadable".
- **Improvement:** the saved session cookie for switches is now created with mode 600.
- **Improvement:** README: install on a VM or a Raspberry Pi, and the PVE mods requirement for Proxmox node detail.

## 2.1.7 — 2026-11-04

- **New:** unified navigation. A top bar with logo (Home), current group and a module picker showing each module's status (shape and text, not just color), or the classic side menu; a wizard lets you choose the first time and "Menu type" changes it later. On mobile there is a bottom bar. A notice with links appears under the module bar when any module has warnings or failures. The menu shows only the modules you have permission for and that the admin has not turned off.
- **New:** the admin can disable the modules they do not use (Admin Panel → Modules, or `sudo labtower-modules disable|enable <module>`). They disappear from menus, home and Overview, do not count in health and stay off after reboots, upgrades and restores; their data is kept.
- **New:** Overview: a row of status chips per module (● ok, ▲ warning, ■ failure, with the number of warnings); a click goes to the card and Ctrl/⌘+click opens the module. "Only with problems" hides healthy cards and is remembered.
- **New:** Proxmox Monitor: cluster capacity and health (days until full, N-1 test, HA, replication, failed tasks, Ceph, per-node data, guest state changes and locks). The README lists the privileges the API token needs.
- **New:** UPS Monitor: detailed status (flags), alarms and beeper, power quality and shutdown margin.
- **New:** NAS Monitor: days until each volume is full, maximum and 24 h average temperature per disk, link down and errors for each network port, and events in Overview (update available, fans, hot disk, link down, network errors, reboot).
- **New:** WAN Monitor: quality per destination, latency percentiles, speed against the plan, availability and MTBF, sustained-quality events, public IP history (with year, no retention limit; it recovers earlier changes from the events) and automatic traceroute when each outage starts. The date since which the IP is known is edited in Settings (dd-mm-yyyy), and the Connection card and the side panel show the days since the last change. The `traceroute` package becomes recommended.
- **New:** Net Monitor: MAC change on an IP, unreviewed devices, connectivity history per host, watched hosts with latency, new ports and an unstable-host flag.
- **New:** DNS Monitor: upstream DNS health (probe every 60 s, with alert and Overview event) and a resolution test that compares your DNS with an outside resolver and detects blocked names.
- **New:** WOL Console: live status of each machine (ping from the server) and power-on confirmation: it reports "woke up (N s)" or that it did not respond within 3 minutes.
- **Improvement:** VPN Monitor keeps the last reading of each server and shows it right after a restart ("Previous reading, updating…"); readings slower than 5 s are logged (`slow read`). Overview shows only the number of connected VPN clients.
- **Improvement:** a common bar in all modules and in Overview (language, theme, clock, user, sign out, 24H and "Menu type"), full width; with the top bar they move up to the global bar and the module bar is hidden if nothing of its own is left. The action buttons (Scan network, Settings, Wake All) share one look.
- **Improvement:** Net Monitor: auto-scan, offline host cleanup, SNMP and Pi-hole move to a "Settings" window, as in WAN Monitor.
- **Improvement:** one text scale in all modules: table header 11 px / 600, cell 13 px, card title 12 px.
- **Improvement:** Proxmox: "Days until full" tells "Gathering history (X of 2 days needed)" apart from "Not growing".
- **Improvement:** the top bar icon is the original LabTower one again; Admin Panel, Net, Proxmox, NAS, DNS, WAN and VPN now have an icon in the browser tab.
- **Security:** when another account's password is reset, changing it at the next sign-in is mandatory, and new users have it set; changing permission levels asks for the current password.
- **Security:** WAN https URLs cannot point to this machine or to link-local addresses; NUT rejects 0.0.0.0 and link-local; the upstream DNS probe only uses port 53 or high ports; the authentication service limits the events and logs each module can write, and the WAN module reads only its own events.
- **Fix:** Net Monitor: Pi-hole stopped connecting until "Save" was pressed when it renewed or regenerated its own certificate. If the pinned certificate expired, or the new one has the same subject and issuer, the new one is pinned (it is logged and shown in events); with a different identity it is still rejected. If it fails with no known names it retries after a minute, and the panel shows the device query error.
- **Fix:** Net Monitor: saving the Pi-hole settings with a blank password erased the saved one and Pi-hole was left disconnected without warning. Now an empty password keeps the saved one (the field says so) and, if none is saved, it asks you to type it.
- **Fix:** Net Monitor: the ZX switch stayed "unreachable" after every restart or upgrade. The switch's web session is saved (mode 600) and reused, and after several rejections in a row it waits longer between attempts.
- **Fix:** Net Monitor: saving OUI or SNMP could erase recently pinned Pi-hole fingerprints; a host's group was lost on every rescan.
- **Fix:** DNS Monitor: the text of the resolution test was cleared every 5 s when the page redrew and the test did not run.
- **Fix:** in "top bar" mode the WAN Monitor "Settings" button was lost; the "Attention" notice sat above the module bar and "Scan network" / "Settings" in the middle.
- **Fix:** a POST with no body no longer returns 400 in Net, NUT, Proxmox, NAS, VPN, WOL, Overview and Panel; the HTML escaping in Net, WOL and Panel also covers the single quote.

## 2.1.6 — 2026-11-02

**VPN Monitor (new module)**
- **New feature:** VPN Monitor (`/vpn/`): shows who is connected to Tailscale, OpenVPN and WireGuard, since when, with which address and how much traffic, with recent sessions and the trend chart.
- **New feature:** Tailscale is read through its API with a read-only key. OpenVPN (status file, versions 1, 2 and 3) and WireGuard (`wg show all dump`) are read over SSH on the VPN server, which can be another VM, a CT or a NAS. LabTower generates its own SSH key, runs only two fixed commands, and restricting the key in `authorized_keys` with `command="…"` is recommended.
- **New feature:** "Run with sudo" option for servers where the status file or `wg show` are root-only (for example Synology). It uses `sudo -n` and only with the two fixed commands.
- **New feature:** WireGuard peers are named with aliases by public key.
- **New feature:** connect and disconnect notices in the Overview timeline and a VPN card in Overview.
- **New feature:** its own "vpn" permission (Admin Panel → users), a service with its own user and backup of `vpn.json` and `state.json`. The SSH key is not backed up: after a restore it has to be created again and installed on the VPN server.

**Administration**
- **New feature:** `sudo labtower-resetpw [user]` command to recover access from the console: it generates a random password (which must be changed at the next sign-in), closes that user's sessions, removes their lockout for failed attempts and records it in the audit log. Options: `--ask` (you type the password), `--disable-2fa` (you lost your phone) and `--list`.
- **Fix:** Upload backup: the file picker accepted only `.gz`, but backups downloaded from the panel are encrypted (`.gpg`). It now accepts `.gpg` too.

**Home page**
- **Improvement:** each card shows its module's status next to the arrow: green "active", yellow "with warnings", red "with failures" and gray "no response". Before there were only two indicators (WOL and NUT) and "active" only meant the service answered. On narrow screens only the dot is shown.

**WAN Monitor**
- **New feature:** "Contracted download" and "Contracted upload" settings (Mb/s). The speed card shows the percentage delivered in the last test and its 7-day average (green from 90 %, orange from 70 %, red below that).

**NAS Monitor**
- **Improvement:** volume space thresholds are set per NAS (Edit NAS → "Volume warning" and "Volume critical", 90 % and 95 % by default).
- **Fix:** alerts used 90 and 95 %, but the colors on the NAS page and in Overview used fixed 80 and 90 %, so a volume at 84 % showed orange or red without an alert. Now everything uses the same values.

**Proxmox Monitor**
- **New feature:** "Expand all / Collapse all" button in Cluster diagnostics, to open or close reboots, backups and SMART at once.

**Overview**
- **Removed:** the "Suggested monitors" card (it produced too many false positives).

**Install in a Proxmox CT**
- **Fix:** restoring a backup from the Admin Panel failed with "The 'no new privileges' flag is set". The `admin-panel` service (the only one that uses `sudo`) is now installed without the systemd options that set that flag. On a VM nothing changes.

## 2.1.5 — 2026-11-02

**Overview**
- **New feature:** global search in the top bar (also with the `/` key). It searches Net Monitor hosts, UPS, Proxmox VMs and containers, NAS, DNS servers and Wake-on-LAN machines. It only shows what each user has permission to see.
- **New feature:** "Alert rules" card: administrators define thresholds on server, UPS, NAS, Proxmox, DNS and internet metrics (for example "server temperature > 65 °C" or "UPS battery < 50 %"), as warning or critical. Rules that are met appear in the attention panel and in the overall status. They are evaluated while Overview is open.
- **New feature:** "Suggested monitors" card: if Net Monitor sees a host with ports typical of a service LabTower can monitor (Proxmox, UPS server, Pi-hole or AdGuard Home, Synology) and it is not configured yet, it suggests it with a link to the module. Only administrators of that module see it and each suggestion can be dismissed.
- **New feature:** Pi-hole / AdGuard blocking can be paused and resumed from the DNS card (5 min, 30 min, 1 hour or until resumed). It requires the "execute" level in DNS Monitor.
- **Improvement:** in kiosk mode the controls to pause Pi-hole blocking are not shown.

**Charts (UPS, NAS, DNS, WAN and switches)**
- **Improvement:** all detail charts look and work the same: same colors, axes, date labels and value window on mouse hover.
- **New feature:** 1-week range in UPS, NAS, DNS and WAN.
- **New feature:** "vs previous" button, which draws the period just before as a dotted line for comparison.
- **New feature:** important events (power outages, IP changes, drops) appear as marks on the chart of the matching module.

**Net Monitor**
- **New feature:** Proxmox VMs and containers are recognized in the hosts table: "VM 100" / "CT 200" badge next to the name, detail with the matching VM/CT and search by "proxmox", "vm", "ct" or number. They are matched by MAC, then by IP and, if neither exists, by identical name.
- **New feature:** "Remove offline after N days" option to automatically delete hosts that stopped responding (0 = never). Only administrators see and change it.
- **New feature:** Switch Monitor: switches are listed in the side bar and you can pick one to see it alone.
- **New feature:** Switch Monitor: each port's speed has a color (10G, 2.5G, 1G, 100M, 10M) in the panel, the table and a legend.
- **New feature:** the Pi-hole panel shows how many devices, DHCP leases and local DNS records it read, and warns if any could not be read.
- **Improvement:** the "Discovered hosts", "Online" and "Offline" cards can be tapped and filter the table like the buttons; tapping the active one again shows all.
- **Improvement:** Pi-hole names include "Local DNS" records and DHCP leases, with priority over reverse DNS. They are refreshed every 5 minutes (before 30) and at the start of each scan; if Pi-hole does not respond, the ones already there are kept.
- **Improvement:** names are also requested directly from Pi-hole's DNS (port 53), without password or API, so they appear even if the application password cannot read the configuration.
- **Fix:** powered-off or unresponsive hosts (for example the AMT interface of a server that is off) did not get a name from Pi-hole or DNS; now they do.
- **Fix:** the purge of offline hosts deletes nothing if no host responded during the scan (for example, if the server lost the network).
- **Security:** names coming from Pi-hole or DNS are cleaned of control characters and limited to 80 characters. The direct DNS query applies the same anti-SSRF rule as the Pi-hole API.

**Proxmox Monitor**
- **New feature:** clicking the name of a VM or container goes to its detail in Net Monitor (as in UPS Monitor), with a data card on mouse hover.
- **New feature:** it reads the MAC and IPs of each VM/CT (fixed ones for the container, guest agent for VMs, container interface), every 5 minutes, in `/api/guests`.
- **New feature:** "Hide stopped" button to hide powered-off VMs and containers (remembered in the browser).
- **Improvement:** the days after which a backup is flagged as old are set per cluster (administrators only). The default is 7 days (before 36 hours).
- **Improvement:** VM and container names are no longer cut off; the metrics move to a second line under the name.
- **Fix:** fixed an error that prevented the page from loading.

**UPS Monitor**
- **Improvement:** devices connected to the UPS show the name Net Monitor knows; if it has none, the IP.
- **Improvement:** if the battery is under 1 year old, the age is shown in months.
- **Performance improvement:** the battery aging state is computed in the background (before it slowed the page for more than a second) and battery tests and the replacement date are cached for a few seconds so the disk and database are not read on every query.

**WAN Monitor**
- **Improvement:** the public IP change notice shows the previous IP, lasts 24 hours and stays in the Overview timeline. The public IP also appears in the side bar.

**Admin Panel**
- **New feature:** the users table has a "Last login" column.
- **Fix:** "Last login" is no longer empty for someone with an open session.
- **Improvement:** the new-version notice shows the commands to upgrade (`wget` and `sudo apt install`) with a button to copy them.

**Installer**
- **Improvement:** at the end it no longer recommends enabling HTTPS if it is already enabled; it shows that it is enabled.

**Internal**
- **Improvement:** backup, HTTPS and install scripts without `shellcheck` warnings (including a guard so an empty variable can never delete `/etc`) and unused code removed. Behavior does not change.
- **Improvement:** GitHub security scans (bandit and gitleaks) are green.

## 2.1.4 — 2026-10-30

**Security**
- **Two-factor authentication (2FA).** In Admin Panel → "Security" it is enabled by scanning a QR code with any app (Google Authenticator, Aegis, 1Password…); the typed key remains as an alternative. 10 single-use recovery codes are given. With 2FA on, every sign-in form asks for the code; each code works once and failed attempts count toward the lockout. An admin can reset another user's 2FA. The QR is generated inside LabTower, with no libraries or internet.
- **Audit log** in Admin Panel: who created or deleted users, changed permissions or passwords, enabled or reset 2FA, closed sessions, created/downloaded/restored/deleted backups, changed the WAN Monitor settings or a battery date, and lockouts for failed attempts. It keeps the last 5,000 entries and never passwords or codes.
- **New-version notice** in Admin Panel: it checks the versions published on GitHub (stable only) at most every 12 hours and warns with a link to the notes. It only reads; it does not download or install. Disable it with `LABTOWER_UPDATE_CHECK=0` in `/etc/default/labtower`.

**WAN Monitor**
- **Router check.** It asks the router whether its WAN link is up, to tell whether an outage is in the local network or on the line. Types: Huawei (WiFi AX3, Mesh and others), OpenWrt, DD-WRT and classic TP-Link. Outages are marked "Local network (LAN)", "Line / provider (WAN)" or "Internet". "Test router" button with the exact reason if it fails. It only reads; the password is stored on the server and never shown. Newer TP-Link models with encrypted login cannot be queried.
- **Comparison with the router:** in "Connection" it shows how long the WAN has been up according to the router and how many outages LabTower recorded in that period ("2 here · 0 WAN").

**UPS Monitor**
- **Battery health:** runtime now, at full battery and with 50 % more load; battery age and capacity trend (warns if it drops 20 % or more in 120 days).
- **Battery replacement date:** ✎ button next to the age to enter it by hand (it takes priority over the UPS's own).
- **Battery age:** `battery.date` and `battery.mfr.date` are read and the most recent credible one is used; an age over 10 years is ignored (some UPS leave the factory date).
- **Self-test log:** the last 8; a failed test warns in Overview. "Last result" shows the date and time LabTower saw it, and if the UPS goes back to "No test initiated" (APC Back-UPS) the last real result is shown. Results are translated to Spanish.

**Proxmox Monitor**
- **Cluster diagnostics:** node reboots with a timeline (it marks simultaneous ones), corosync quorum, Ceph (OSDs and warnings) and disk SMART, including "Unsafe Shutdowns" on NVMe.
- **Backups (vzdump):** last backup of each VM/CT, age, size and verification; it flags "No backup" or "Very old" and lists failed tasks. Test VMs or templates can be **ignored**, several at once. The token needs `Datastore.Audit` and `Sys.Audit` (role `PVEAuditor`).

**NAS Monitor**
- It now also reads **TrueNAS** (25.04 or newer) and **OpenMediaVault** (7 or newer), read-only.

**Net Monitor / Switch Monitor**
- CRC errors per port (cable or network card), a warning for flapping links and a "Warn per port" checkbox.

**Backup**
- `labtower-sftp-backup verify` and a daily cron: checks on the storage that the latest copy exists, is not empty and is recent.

**Changes**
- Texts and documentation no longer say "the Pi": they say "the server". "Raspberry Pi" stays only for the power supply, temperature and the list of compatible machines.
- The home page is now in English and Spanish, and the side bar says "Resumen" in Spanish.

**Fixes**
- WOL Console: "Net Monitor hosts file not readable" warning (the shared files were left in mode 600 instead of 640).
- Proxmox: after ignoring or un-ignoring a VM, the page could show the previous state for up to 10 minutes.
- Untranslated or mixed-language texts in Net Monitor, Proxmox Monitor, WOL Console, NAS Monitor, WAN Monitor, Admin Panel and Overview; UPS Monitor dates use day/month/year in Spanish.
- NAS Monitor: the connection error no longer says "this Pi".

## 2.1.3 — 2026-10-29

Fixes from the code security review.

**Security**
- **Sign-in:** a successful sign-in no longer resets the IP's attempt counter (before, someone with their own account could sign in between attempts and guess other passwords without limit). nginx now applies the login attempt limit (10/min per IP) to **all** modules, not just the panel.
- **Sessions:** each session has an absolute lifetime cap from its creation (14 days for the normal one, 30 for "one week", 90 for "one month", 400 for "always"), even if it keeps being used.
- **Password on critical actions:** creating a user, resetting another's password and restoring or downloading a backup ask again for the account's password (with the same attempt limit as login).
- **Panel backups:** the download is now **encrypted** (gpg, AES-256, the same format as the SFTP backup) with a passphrase of 12 or more characters that you choose; a `.gpg` can be uploaded by giving the passphrase. Downloading unencrypted must be explicitly checked and is logged. Creating a backup no longer downloads it by itself, and the download route without a password is removed.
- **Teleporter:** the file of a backup (which may come from outside) is no longer opened by root: `tar` and the validators (JSON, SQLite) run as the unprivileged user, in a folder no other process of that user can reach. `users.json` is also validated by its structure (names, hashes and levels) before restoring, and any unknown level is treated as "none" when read.
- **Interface:** `data-on-*` attributes can only call functions registered by each module (a closed list) and not any global function; values used as class names (permission level, VM type, label, port flag) are filtered.
- **DNS servers with "Verify TLS certificate" turned off:** any certificate is no longer accepted; the fingerprint is pinned on first connection and a change is rejected (saving the server again clears it).
- **Connection targets:** Proxmox, NAS, DNS, Pi-hole and switches reject the machine itself (loopback) and link-local addresses, also if a name resolves to them, so LabTower cannot be used as a bridge to its internal services.
- **Inputs:** the APIs reject with 400 (before 500) a JSON body that is not an object, excessively nested JSON or fields of the wrong type.
- **nginx:** the 200 MB limit and unbuffered upload apply only to the backup upload route (the rest of the panel keeps 1 MB). The CSP no longer allows Google fonts (they were not used).
- **Isolation between modules (redesign):** each service runs with its own system user (`labtower-<module>`), with its private data folder (700) and its own `metrics.db`; systemd only lets it write that folder. Users, sessions, counters and events move to `/var/lib/labtower/auth/`, which only the authentication service (the Admin Panel, `labtower-auth`) reads. The other modules query it through a Unix socket (`/run/labtower/auth.sock`): checking a session, signing in or out and recording events, identifying the caller with the kernel (`SO_PEERCRED`). There is no operation that creates sessions without a password or reads users, so a compromised module can no longer forge sessions, take the hashes or touch another module's data. The service limits simultaneous connections (64) and the duration of each (5 s); the client has a bounded session cache and a 1 s circuit breaker if the service does not respond (it fails closed). `wol-console/devices.json` and `net-monitor/hosts.json` (which read each other) move to group mode 640, are read as untrusted input (not following links, regular files only, max 4 MiB) and there is no longer a shared folder.
- **Upgrade to 2.1.3:** the installer creates the users, deletes any symbolic links inside `/var/lib/labtower` (root does not follow them), distributes the files (`auth/`, each module), splits the shared `metrics.db` into one per module (with an unprivileged user; the original stays in `/var/backups/labtower/metrics.db.pre-isolation.*`) and rewrites the systemd units. It is idempotent. The `labtower` user remains only as a data-less user with which Teleporter opens untrusted backups. Earlier backups (with a single `metrics.db`) are restored by splitting it per module.
- **Teleporter:** each restored file ends up owned by its module's user (modes 700/710 for folders, 600/640 for files); the snapshot of SQLite databases is taken by the file's owner, not root; the `sudo` rule is now for `labtower-auth`.
- **Documentation:** the README explains that device credentials are stored readable (permissions 600; use read-only accounts), the allowed targets and the isolation between modules.

**Fixes**
- Inputs of the wrong type: `POST /api/hosts/delete`, `/api/hosts/update` and `/api/scan` (Net Monitor), `/api/clusters` (Proxmox) and `/api/ping` (WOL) dropped the connection without answering if the `ip` or `name` field arrived as a list, object or number; they now answer 400 like the rest.
- Dead code cleanup: unused imports and variables in several modules, `${OLD:?}` in the installer's `rm -rf`.
- Switch Monitor: "Updated … ago" shows whole seconds (before it showed, for example, "23.33152723312378 s").
- Switch Monitor: the port table header says "MBIT/S rx / tx" (before, because of capitals, it read "MB/S" although the values are megabits).
- Switch Monitor: the summary cards wrap to another row when they do not fit (before the "Max. temperature (switch)" label spilled out of the card and values broke), and the "Connected to" column of the port table has a larger minimum width so rows are not very tall on narrow screens.

## 2.1.2 — 2026-10-28

**New**
- **Switch Monitor**: a new tab in Net Monitor to monitor managed switches: ZX310S, HC-SWTGW218AS and any SNMP v2c switch, such as TP-Link. It shows the front panel with each port's state (up, down, disabled, new errors, uplink between switches, loop), speed, packets/s, errors, STP, temperature, which known host each port is connected to and a 1-year history with charts. Switches are added, tested and edited from the interface (administrators only); credentials stay in `switches.json` (permissions 600) and the API does not return them. It is read-only: the destructive operations of the devices are blocked.
- Switch Monitor, configurable **front panel layout** (one row or two alternating rows; with SNMP and 16 or more ports the alternating one is chosen, as on TP-Link) and ports sorted by physical number.
- Switch Monitor, **real bytes over SNMP** (TP-Link): Mb/s, total per port and traffic charts.
- Switch Monitor, **estimated bytes on ZX and HC**: since they only report packets, packets × average size is computed (800 B by default, configurable per switch; 0 disables it). They are always marked with "≈" and are not exact. If the HC firmware has byte columns, the real ones are used.
- Switch Monitor, **History** sub-tab: accumulated totals per port that are not lost on switch or LabTower restarts (the advance of each counter between readings is added up).
- Switch Monitor, **MAC table** sub-tab: search by MAC, IP, name, switch or port, cross-referenced with the hosts Net Monitor knows. On the HC there is an option to read the whole MAC table (off by default).
- Switch Monitor, **topology map** with draggable nodes (the position is remembered in the browser).
- Overview: the Net Monitor card lists the switches (ports up and temperature) and warnings include switch offline, high or critical temperature, new errors and loop. The timeline records drops, temperature, errors, link changes and loops (in Spanish and English).
- Backup (Teleporter, copy before upgrading and uninstalling): includes `switches.json` and `switches.db`.
- Theme: next to the ◐ icon there is now a button showing the chosen mode (DARK / LIGHT / AUTO, or OSCURO / CLARO / AUTO in Spanish), like those for "24H" and "ES". Either one can be pressed to change. It replaces the small "A" on the icon.
- Overview, "LabTower Server" card: shows the status of the last SFTP backup (OK, late if more than 36 h pass, or failed) with how long ago it ran. If it failed or is late it also appears in the warnings. It is not shown if the backup is not configured.

**Changes**
- NAS Monitor, "Disk activity": it only lists disks with real activity (≥ 5 % or ≥ 256 KB/s); idle ones are summarized in one line ("All disks idle (8)") instead of eight rows with 0 %.

**Fixes**
- Switch Monitor, HC: sign-in tolerates the device answering HTTP 400 to the POST; if the device closes the connection without answering it retries once, and when reading the MAC table what was read is kept instead of failing. HTTP errors from switches say which request failed.
- Switch Monitor, SNMP: virtual interfaces are skipped and port numbering comes from the name (`…1/0/N`).
- Overview: LabTower identifies itself as server/VM and only says "Pi" when the machine is a Raspberry Pi.
- SFTP backup: `openssh-client`, `gnupg`, `gpg-agent`, `openssl` and `cron` become mandatory dependencies of the package (before `gnupg` was only recommended and `gpg-agent` was missing, so encryption failed on minimal installs with "No agent running").
- Package: after reviewing the commands used by the modules and scripts, `iproute2` (`ip`), `systemd` (`systemctl`, `journalctl`), `curl` (`labtower-health`), `ca-certificates` (HTTPS downloads), `passwd` (`useradd`, `usermod`, `userdel`), `hostname` and `awk` are also declared.
- `labtower-sftp-backup status` no longer crashes with an empty or damaged status file: it explains it and says how to regenerate it.
- The status file is synced to disk before being renamed, so a sudden power cut does not leave it empty.

## 2.1.1 — 2026-10-27

New look: dark theme by default, rounder cards with a subtle glow, small uppercase titles, dense tables, a side menu with an accent and a translucent top bar. All modules, the Admin panel and the home page use it. Google fonts are no longer loaded: the system font is used.
Theme button with "Auto": in Overview and on the home page it cycles between dark, light and Auto, which follows the system mode.
Overview, tiled kiosk: cards are arranged by columns, so a short one no longer leaves a white gap and more data fits on the iPad.
Overview, WAN latency chart: last 24 h, with gaps where there was no response and red bands where the link was down.
Overview, DNS chart: the % blocked over the last hours, fitted to the real range.
WAN Monitor, speed test engine: new option in Settings. Besides the built-in one (Cloudflare), Ookla Speedtest CLI or LibreSpeed CLI can be used if installed.
Name: the "Raspberry Pi" card is now called "LabTower Server".
DNS Monitor: the color changes from pink to emerald green.

Fixes

NAS Monitor: disk activity showed 0 % on every disk. It now shows the 1-minute average and the real read and write per second.
Admin: restoring backups failed with "file not found". The temporary copy is now kept in /var/backups/labtower.
WAN Monitor: if the server rejects the speed test, the error says why. If only the upload fails, the download is kept.
DNS Monitor: if the Pi-hole API is not found, the message suggests what to try.
Overview: "Logged-in users" now shows who signed in over SSH or console on machines without utmp or logind.
Phone: WAN Monitor shows its top cards in 2 columns, and the NAS and DNS summary tables are no longer cut off on the right.

## 2.1 — 2026-10-27

Two new modules.

- **New feature:** DNS Monitor (`/dns/`, port 8087): one or more Pi-hole (v6 and v5, detected automatically) or AdGuard Home. It shows queries, % blocked, clients, domains on lists, response time, top queried and blocked, most active clients, upstream DNS, queries per hour and history. It lets you pause and resume blocking ("execute" permission). The password or token is stored with 0600 permissions and never goes back to the browser.
- **New feature:** WAN Monitor (`/wan/`, port 8088): latency, jitter and loss (ping or TCP to several destinations), DNS resolution time, gateway, outages (it tells "no internet" from "no local network"), public IP with change notice, availability over 24 h, 7 and 30 days, and a scheduled or on-demand speed test (download, upload and ping, against a Cloudflare-compatible server). Measurements are paused while the test runs.
- **New feature:** per-user `dns` and `wan` permissions in the Admin panel; both modules in the menu, home page, Overview (cards and timeline), system health, backups and teleporter.
- **Improvement:** the package depends on `iputils-ping`. New icons for both modules.

## 2.0.1 — 2026-10-27

New icons: an isometric stack and one icon per module. No functional changes.

## 2.0 — 2026-10-27

**Pi Console is now called LabTower.** It is the same project: it is no longer Raspberry Pi only and many other projects shared the old name. There is a new logo on the home page, the app icons and the screenshots.

**What changes**
- The package is `labtower` and replaces `pi-console`. Paths become `/opt/labtower`, `/var/lib/labtower`, `/etc/labtower`, `/var/log/labtower` and `/var/backups/labtower`.
- The system user is `labtower`. The services `pi-console-ups` and `pi-console-overview` are now `labtower-ups` and `labtower-overview`; the others keep their names.
- Commands are `labtower-https`, `labtower-health`, `labtower-resources` and `labtower-sftp-backup`. `teleporter` is unchanged.
- The `PICONSOLE_*` variables become `LABTOWER_*` (the ones in `/etc/default` are renamed automatically).
- Backups made with 1.x (`pi-console-*.tar.gz`) can still be restored and downloaded from Teleporter.

**When upgrading:** it happens by itself. The installer removes `pi-console` and moves the user, data, HTTPS certificates, SFTP backup, logs and earlier backups to the new names. Passwords and data do not change; you have to log in again. If you had your own scripts calling `pi-console-https` or other commands, rename them. Optional: `sudo dpkg -P pi-console` cleans the old package record.
