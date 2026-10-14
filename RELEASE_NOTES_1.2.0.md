# Pi Console 1.2.0j

## Español

Primer release de la serie 1.2. Reúne todo lo hecho desde 1.1.8 y deja el código listo para leerlo y mantenerlo.

**Novedades principales**
- **Código comentado en español e inglés** en todos los archivos (servicios Python, autenticación, teleporter, scripts, instalador, nginx y páginas HTML), con un mapa de estructura al inicio de cada archivo. Solo comentarios: la lógica no cambió.
- **Seguridad:** contraseñas con scrypt, límite de intentos de login, cabeceras de seguridad en nginx, `users.json` ausente ya no reabre `admin/admin`, certificado de Proxmox fijado por huella SHA-256, permisos explícitos por módulo (WOL, UPS, Net, Proxmox), restaurar NUT/nginx solo por consola, WOL escucha solo en loopback.
- **Salud del sistema:** `GET /api/health` en cada servicio, tarjeta *Salud del sistema* en el Admin Panel y comando `pi-console-health`. En una Raspberry Pi avisa de subtensión (`power`); en una VM u otro equipo no se muestra.
- **Robustez:** servidores HTTP multihilo, escritura atómica con copia `.bak`, bloqueo entre procesos, sesiones que se cierran al quitar o reducir permisos, corrección del historial de UPS que dejaba de guardarse.
- **Interfaz:** menú móvil, pie con la versión, mejoras para móvil/tablet/laptop, columnas Net Monitor y Proxmox en el Admin Panel, impresoras y tablets en Net Monitor, edición de servidores NUT.
- Mensajes de error y de log del backend en inglés.
- **Instalación nueva más limpia:** el primer ingreso con `admin`/`admin` obliga a cambiar la contraseña antes de usar cualquier módulo; UPS Monitor empieza sin servidores (no exige tener una UPS); Net Monitor no escanea nada hasta que lo pides («Hacer escaneo inicial», con la lista llenándose en vivo) y autodetecta tu red; `snmp` es dependencia; los ejemplos usan IP neutras; menú por defecto: UPS, Net, Proxmox, WOL, Admin.
- **Permisos entre módulos:** un admin solo da o quita permisos en los módulos donde él mismo tiene ese nivel, y los respaldos (Teleporter) los maneja solo quien administra todos los módulos. Proxmox avisa de forma permanente de los clusters sin certificado fijado. Cookie `Secure` opcional (`PICONSOLE_SECURE_COOKIE=1`) y sección [*Seguridad*](README.md#seguridad) en el README.
- **1.2.0j:** el desplazamiento automático del kiosko viene apagado y se activa con el botón «Auto-desplazar» (aparece al tocar la pantalla, solo si el contenido no cabe). Un toque sobre la barra oculta ya no pulsa botones por accidente.
- **1.2.0i:** el kiosko cabe sin scroll en una tablet de 7" (1024×600): 4 tarjetas en una fila, márgenes y tamaños compactos, sin gráficos de 24 h y con la línea de tiempo resumida.
- **1.2.0h:** el modo kiosko se adapta a pantallas chicas (tablet de 7"): letra y columnas según el tamaño, `?zoom=` para ajustar, desplazamiento automático si el contenido no cabe (`?autoscroll=0` lo desactiva) y el botón de salir aparece también al tocar la pantalla.
- **1.2.0g:** el Resumen se ve bien en iPad antiguos (iOS 12 / Safari < 14.1): espaciado de respaldo donde el navegador no soporta `gap` en flexbox y tamaño de letra del modo kiosko sin `:has()`. En navegadores modernos no cambia nada.
- **1.2.0f:** en modo kiosko el botón «Salir de kiosko» ya no tapa la hora de actualización.
- **1.2.0d:** el Resumen muestra el nombre y la dirección del servidor UPS sin conexión en vez de su identificador interno.
- **1.2.0c (Resumen):** nueva página `/overview/` con lo principal de UPS, Proxmox y red en una pantalla, widget de la Pi (temperatura, CPU, memoria, disco), línea de tiempo de eventos y modo kiosko para un monitor fijo. Servicio nuevo `pi-console-overview` (puerto 8085).
- **1.2.0b (documentación):** README reordenado y completo (actualizar, variables de entorno, operación, capturas de los 5 módulos), versión en inglés (`README.en.md`) y `LICENSE` MIT. La clave CSRF de WOL ahora es aleatoria y persistente (sin valor por defecto conocido). La página de inicio sigue el orden del menú e incluye el Admin Panel.

**Actualizar desde cualquier 1.1.x**
```bash
wget "https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.0j_all.deb?n=$RANDOM" -O pi-console_1.2.0j_all.deb
sudo apt-get install -y ./pi-console_1.2.0j_all.deb
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
- **Cleaner fresh install:** the first login with `admin`/`admin` forces a password change before any module can be used; UPS Monitor starts with no servers (no UPS required); Net Monitor scans nothing until you ask ("Run initial scan", with the list filling in live) and autodetects your network; `snmp` is a dependency; examples use neutral IPs; default menu: UPS, Net, Proxmox, WOL, Admin.
- **Cross-module permissions:** an admin can only grant or remove permissions on the modules where they hold that level themselves, and backups (Teleporter) are handled only by someone who administers every module. Proxmox permanently warns about clusters without a pinned certificate. Optional `Secure` cookie (`PICONSOLE_SECURE_COOKIE=1`) and a [*Security*](README.md#seguridad) section in the README.
- **1.2.0j:** kiosk auto-scroll now starts off and is turned on with the "Auto-scroll" button (it shows up when the screen is touched, only if the content doesn't fit). Touching the hidden bar no longer presses buttons by accident.
- **1.2.0i:** kiosk fits without scrolling on a 7" tablet (1024×600): 4 cards in one row, compact spacing and sizes, no 24 h charts and a shortened timeline.
- **1.2.0h:** kiosk mode adapts to small screens (7" tablet): text size and columns by screen size, `?zoom=` to adjust, automatic scrolling when the content doesn't fit (`?autoscroll=0` disables it), and the exit button also appears on touch.
- **1.2.0g:** Overview renders correctly on old iPads (iOS 12 / Safari < 14.1): fallback spacing where flexbox `gap` is unsupported and kiosk font size without `:has()`. No change on modern browsers.
- **1.2.0f:** in kiosk mode the "Exit kiosk" button no longer covers the update time.
- **1.2.0d:** Overview shows the name and address of an unreachable UPS server instead of its internal identifier.
- **1.2.0c (Overview):** new `/overview/` page with the key points of UPS, Proxmox and network on one screen, a Pi widget (temperature, CPU, memory, disk), an event timeline and a kiosk mode for a fixed monitor. New service `pi-console-overview` (port 8085).
- **1.2.0b (documentation):** reorganised, complete README (updating, environment variables, operations, screenshots of all 5 modules), an English version (`README.en.md`) and an MIT `LICENSE`. The WOL CSRF key is now random and persistent (no known default). The home page follows the menu order and includes the Admin Panel.

**Upgrade from any 1.1.x**
```bash
wget "https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.0j_all.deb?n=$RANDOM" -O pi-console_1.2.0j_all.deb
sudo apt-get install -y ./pi-console_1.2.0j_all.deb
pi-console-health
```
Data in `/var/lib/pi-console` is kept; the installer also saves a copy in `/var/backups/pi-console`.

Full details in [CHANGELOG.md](CHANGELOG.md).
