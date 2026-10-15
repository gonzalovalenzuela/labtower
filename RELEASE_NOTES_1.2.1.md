# Pi Console 1.2.1

## Español

Versión estable de la serie 1.2. Reúne 1.2.0a–x ([historial](RELEASE_NOTES_1.2.0.md)).

**Qué incluye**
- **Resumen** (`/overview/`): UPS, Proxmox, red y Raspberry Pi en una pantalla, línea de tiempo y modo kiosko.
- **Seguridad:** 13 hallazgos de auditoría corregidos. Sin `admin`/`admin` (contraseña aleatoria), scrypt, sesiones con hash, límite de intentos, servicios con systemd endurecido, respaldo SFTP cifrado, `pi-console-https`.
- **Gráficos:** voltaje, consumo y temperatura de la UPS; CPU y memoria de Proxmox; temperatura de la Pi, con histórico en SQLite.
- **Operación:** `pi-console-health`, respaldos Teleporter, panel de salud en el Admin Panel.

**Cambios respecto a 1.2.0x**
- Al purgar, los datos conservados pasan a `root:root` (700) y se devuelven al reinstalar.
- La metaetiqueta `author` ya no lleva correo.
- Capturas rehechas con datos ficticios.

**Revisado antes de publicar:** sin claves ni datos personales en código, historial ni paquete; 38 pruebas de integración; instalación, actualización, desinstalación y purga probadas.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1/pi-console_1.2.1_all.deb
sha256sum pi-console_1.2.1_all.deb    # c384b7c97942efe3cf239ed0aed4b8446a5029a4a99ce02c86f1599b50e6934c
sudo apt-get install -y ./pi-console_1.2.1_all.deb
pi-console-health
```
Los datos (`/var/lib/pi-console`) se conservan; el instalador guarda además una copia en `/var/backups/pi-console`.

**Notas**
- Desde versiones anteriores a 1.2.0u hay que iniciar sesión otra vez.
- Al actualizar desde una versión anterior a 1.2.0u se ejecuta el `prerm` antiguo; las actualizaciones siguientes usan el nuevo.
- La CSP aún permite `'unsafe-inline'`. WOL, Net Monitor y Admin Panel tienen menos aislamiento systemd porque usan `ping` y `sudo`.
- Las unidades systemd se validaron con `systemd-analyze verify`; no se probaron en una Pi real.

Detalle en [CHANGELOG.md](CHANGELOG.md).

## English

Stable release of the 1.2 series. It gathers 1.2.0a–x ([history](RELEASE_NOTES_1.2.0.md)).

**What it includes**
- **Overview** (`/overview/`): UPS, Proxmox, network and Raspberry Pi on one screen, event timeline and kiosk mode.
- **Security:** all 13 audit findings fixed. No `admin`/`admin` (random password), scrypt, hashed sessions, login throttling, hardened systemd services, encrypted SFTP backup, `pi-console-https`.
- **Charts:** UPS voltage, power and temperature; Proxmox CPU and memory; Pi temperature, with SQLite history.
- **Operations:** `pi-console-health`, Teleporter backups, health panel in the Admin Panel.

**Changes since 1.2.0x**
- On purge, the kept data becomes `root:root` (700) and is handed back on reinstall.
- The `author` meta tag no longer carries an email.
- Screenshots redone with fictitious data.

**Checked before publishing:** no keys or personal data in code, history or package; 38 integration tests; install, upgrade, remove and purge tested.

**Install or upgrade**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1/pi-console_1.2.1_all.deb
sha256sum pi-console_1.2.1_all.deb    # c384b7c97942efe3cf239ed0aed4b8446a5029a4a99ce02c86f1599b50e6934c
sudo apt-get install -y ./pi-console_1.2.1_all.deb
pi-console-health
```
Data in `/var/lib/pi-console` is kept; the installer also saves a copy in `/var/backups/pi-console`.

**Notes**
- From versions older than 1.2.0u, everyone must log in again.
- Upgrading from a version older than 1.2.0u runs the old `prerm`; later upgrades use the new one.
- The CSP still allows `'unsafe-inline'`. WOL, Net Monitor and Admin Panel have less systemd isolation because they use `ping` and `sudo`.
- The systemd units were checked with `systemd-analyze verify`; not tested on a real Pi.

Details in [CHANGELOG.md](CHANGELOG.md).
