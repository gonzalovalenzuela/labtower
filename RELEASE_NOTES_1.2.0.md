# Pi Console 1.2.0

## Español

Primer release de la serie 1.2. Reúne todo lo hecho desde 1.1.8 y deja el código listo para leerlo y mantenerlo.

**Novedades principales**
- **Código comentado en español e inglés** en todos los archivos (servicios Python, autenticación, teleporter, scripts, instalador, nginx y páginas HTML), con un mapa de estructura al inicio de cada archivo. Solo comentarios: la lógica no cambió.
- **Seguridad:** contraseñas con scrypt, límite de intentos de login, cabeceras de seguridad en nginx, `users.json` ausente ya no reabre `admin/admin`, certificado de Proxmox fijado por huella SHA-256, permisos explícitos por módulo (WOL, UPS, Net, Proxmox), restaurar NUT/nginx solo por consola, WOL escucha solo en loopback.
- **Salud del sistema:** `GET /api/health` en cada servicio, tarjeta *Salud del sistema* en el Admin Panel y comando `pi-console-health`. En una Raspberry Pi avisa de subtensión (`power`); en una VM u otro equipo no se muestra.
- **Robustez:** servidores HTTP multihilo, escritura atómica con copia `.bak`, bloqueo entre procesos, sesiones que se cierran al quitar o reducir permisos, corrección del historial de UPS que dejaba de guardarse.
- **Interfaz:** menú móvil, pie con la versión, mejoras para móvil/tablet/laptop, columnas Net Monitor y Proxmox en el Admin Panel, impresoras y tablets en Net Monitor, edición de servidores NUT.
- Mensajes de error y de log del backend en inglés.

**Actualizar desde cualquier 1.1.x**
```bash
wget "https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.0d_all.deb?n=$RANDOM" -O pi-console_1.2.0d_all.deb
sudo apt-get install -y ./pi-console_1.2.0d_all.deb
pi-console-health
```
Los datos (`/var/lib/pi-console`) se conservan; el instalador además guarda una copia en `/var/backups/pi-console`.

Detalle completo en [CHANGELOG.md](CHANGELOG.md).

## English

First release of the 1.2 series. It gathers everything done since 1.1.8 and leaves the code easy to read and maintain.

**Highlights**
- **Code commented in Spanish and English** in every file (Python services, authentication, teleporter, scripts, installer, nginx and HTML pages), with a structure map at the top of each file. Comments only: the logic did not change.
- **Security:** scrypt passwords, login throttling, nginx security headers, a missing `users.json` no longer reopens `admin/admin`, Proxmox certificate pinned by SHA-256 fingerprint, explicit per-module permissions (WOL, UPS, Net, Proxmox), NUT/nginx restore from the command line only, WOL listens on loopback only.
- **System health:** `GET /api/health` on every service, a *System health* card in the Admin Panel and the `pi-console-health` command. On a Raspberry Pi it warns about under-voltage (`power`); it is not shown on VMs or other machines.
- **Robustness:** multi-threaded HTTP servers, atomic writes with `.bak` copy, cross-process locking, sessions closed when permissions are removed or reduced, fix for the UPS history that stopped being saved.
- **UI:** mobile menu, version footer, phone/tablet/laptop improvements, Net Monitor and Proxmox columns in the Admin Panel, printers and tablets in Net Monitor, editable NUT servers.
- Backend error and log messages in English.

**Upgrade from any 1.1.x**
```bash
wget "https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.0d_all.deb?n=$RANDOM" -O pi-console_1.2.0d_all.deb
sudo apt-get install -y ./pi-console_1.2.0d_all.deb
pi-console-health
```
Data in `/var/lib/pi-console` is kept; the installer also saves a copy in `/var/backups/pi-console`.

Full details in [CHANGELOG.md](CHANGELOG.md).
