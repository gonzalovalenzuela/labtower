<p align="center"><img src="docs/logo.png" alt="LabTower" width="120"></p>

# LabTower

**Panel para homelab** (Raspberry Pi, VM o equipo x86): UPS, red, Proxmox, NAS Synology, Wake-on-LAN y administración en un solo lugar. Sin dependencias externas: Python estándar + nginx.

[English → README.en.md](README.en.md)

<img src="docs/screenshots/1920x1080/light/overview.png" alt="Resumen" width="900">

**Contenido:** [Módulos](#módulos) · [Capturas](#capturas) · [Requisitos](#requisitos) · [Instalar](#instalar) · [Actualizar](#actualizar) · [Primer ingreso](#primer-ingreso) · [Funciones por módulo](#funciones-por-módulo) · [HTTPS](#https) · [Respaldos](#respaldos) · [Salud y operación](#salud-y-operación) · [Configuración](#configuración) · [Seguridad](#seguridad) · [Estructura](#estructura) · [Licencia](#licencia)

---

## Módulos

| Módulo | Ruta | Puerto | Qué hace |
|---|---|---|---|
| **Resumen** | `/overview/` | 8085 | Estado de todo en una pantalla, línea de tiempo de eventos y modo kiosko |
| **UPS Monitor** | `/nut/` | 8081 | Lee UPS por NUT: batería, carga, autonomía, consumo, voltajes, temperatura, historial y CSV |
| **Net Monitor** | `/net/` | 8083 | Escanea la red: equipos, tipo, SO, puertos, MAC y fabricante |
| **Proxmox Monitor** | `/pve/` | 8084 | Clusters Proxmox VE: nodos, VMs, CTs y Ceph |
| **NAS Monitor** | `/nas/` | 8086 | Uno o varios NAS Synology por SNMP: discos, volúmenes, temperatura, CPU, memoria y red |
| **DNS Monitor** | `/dns/` | 8087 | Pi-hole (v5 y v6) y AdGuard Home: consultas, % bloqueado, tops, DNS de salida y pausa del bloqueo |
| **WAN Monitor** | `/wan/` | 8088 | Salida a internet: latencia, pérdida, cortes, IP pública y prueba de velocidad programada |
| **WOL Console** | `/wol/` | 8080 | Enciende equipos con Wake-on-LAN |
| **Admin Panel** | `/admin/` | 8082 | Usuarios, permisos, sesiones, respaldos y salud del sistema |

El menú se puede reordenar por usuario. La página de inicio (`/`) tiene una tarjeta por módulo.

## Capturas

<img src="docs/screenshots/1920x1080/light/ups.png" width="290"> <img src="docs/screenshots/1920x1080/light/net.png" width="290"> <img src="docs/screenshots/1920x1080/dark/proxmox.png" width="290"> <img src="docs/screenshots/1920x1080/light/nas.png" width="290">

Todas las pantallas (tema claro y oscuro, 4 tamaños) están en [`docs/screenshots/`](docs/screenshots/). Los datos son de demostración.

---

## Requisitos

- Raspberry Pi (probado en 3A+) o una VM/equipo x86, con Raspberry Pi OS, DietPi, Debian 12+ o Ubuntu.
- Python 3.9+, nginx, `sudo`, `snmp`, NUT (`nut`, `nut-client`), `openssh-client`, `gnupg`, `gpg-agent`, `openssl`, `cron`, `curl`, `iproute2`, `systemd` y otros paquetes base. `apt` los instala con el `.deb`.
- Opcional: `ieee-data` (base local de fabricantes por MAC) y los motores de prueba de velocidad (ver más abajo).

## Instalar

```bash
wget https://github.com/gonzalovalenzuela/labtower/releases/download/2.1/labtower_2.1_all.deb
sudo apt-get update
sudo apt-get install -y ./labtower_2.1_all.deb
```

Usa `apt-get install ./archivo.deb` y no `dpkg -i`, para que `apt` instale las dependencias. Luego abre `http://<ip-de-la-pi>/`.

El instalador crea el usuario del sistema `labtower`, los servicios systemd, la configuración de nginx y el usuario `admin` con una **contraseña aleatoria** que muestra al terminar. Si la perdiste: `sudo cat /var/lib/labtower/initial-admin-password`.

**Desde el código fuente** (desarrollo): copia los módulos a `/opt/labtower`, instala la configuración de `etc/nginx/` y crea los servicios con `debian/postinst` como guía.

### Pruebas de velocidad (opcional)

WAN Monitor trae un motor propio y no necesita nada más. Si quieres usar **Ookla** o **LibreSpeed**, instala su programa; después aparece como opción en *WAN Monitor → Ajustes → Motor de la prueba* (mientras falte, sale marcado «no instalado»).

**Ookla `speedtest`** (el paquete oficial se llama `speedtest`; el `speedtest-cli` de Debian es otro programa y no sirve):

```bash
sudo apt-get install -y curl
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install -y speedtest
speedtest --version
```

Si el script del repositorio no reconoce tu versión de Debian o Raspberry Pi OS, descarga el `.tgz` de Linux para tu arquitectura (`x86_64`, `aarch64`, `armhf`) desde <https://www.speedtest.net/apps/cli>, descomprímelo y copia `speedtest` a `/usr/local/bin/`. LabTower lo ejecuta con `--accept-license --accept-gdpr`.

**LibreSpeed `librespeed-cli`:**

```bash
sudo apt-get install -y librespeed-cli     # Debian 13 (trixie) o posterior
librespeed-cli --version
```

Donde el paquete no existe, usa el binario de la [versión v1.0.14](https://github.com/librespeed/speedtest-cli/releases/tag/v1.0.14). Cada archivo es un `.tar.gz` con el programa `librespeed-cli`; elige el de tu arquitectura (`uname -m`):

| `uname -m` | Archivo |
|---|---|
| `x86_64` | `librespeed-cli_1.0.14_linux_amd64.tar.gz` |
| `aarch64` (Raspberry Pi 64 bits) | `librespeed-cli_1.0.14_linux_arm64.tar.gz` |
| `armv7l` (Raspberry Pi 32 bits) | `librespeed-cli_1.0.14_linux_armv7.tar.gz` |

```bash
wget https://github.com/librespeed/speedtest-cli/releases/download/v1.0.14/librespeed-cli_1.0.14_linux_arm64.tar.gz
tar -xzf librespeed-cli_1.0.14_linux_arm64.tar.gz librespeed-cli
sudo install -m 755 librespeed-cli /usr/local/bin/librespeed-cli
librespeed-cli --version
```

## Actualizar

```bash
wget https://github.com/gonzalovalenzuela/labtower/releases/download/2.1/labtower_2.1_all.deb
sudo apt-get install -y ./labtower_2.1_all.deb
labtower-health
```

- Sirve desde cualquier 1.1.x, 1.2.x, 1.3, 1.4 y también desde **Pi Console** (el nombre anterior, ver abajo). Los datos de `/var/lib/labtower` se conservan y además se copian a `/var/backups/labtower`.
- **Desde Pi Console (1.x):** LabTower es el mismo proyecto con otro nombre. El `.deb` de la 2.0 reemplaza a `pi-console` y migra solo el usuario, los datos, los certificados HTTPS, el respaldo SFTP y los respaldos anteriores a las rutas nuevas (`/var/lib/labtower`, `/etc/labtower`…). Hay que iniciar sesión otra vez. Los comandos `pi-console-*` ahora son `labtower-*`. Después puedes ejecutar `sudo dpkg -P pi-console` para limpiar el registro del paquete viejo.
- Si instalas un número **menor** que el actual, `apt` pide `--allow-downgrades`.
- Después de actualizar, recarga la página (Ctrl+Shift+R). En el iPad, cierra y abre la página.
- Los cambios de cada versión están en [CHANGELOG.md](CHANGELOG.md).

## Primer ingreso

1. Entra con `admin` y la contraseña que mostró el instalador.
2. El sistema te obliga a elegir una contraseña nueva (mínimo 8 caracteres) antes de usar cualquier módulo.
3. Crea tus usuarios en el Admin Panel. Para cualquier usuario se puede marcar «debe cambiar contraseña» al crearlo o al restablecer su clave.

---

## Funciones por módulo

### Resumen
- **Estado global** (Todo en orden / Atención / Falla) y lista de lo que requiere atención, con enlace al módulo.
- **UPS:** estado, batería, carga, autonomía, consumo y gráficos de las últimas 24 h.
- **Proxmox:** nodos en línea, VMs y CTs corriendo, CPU y memoria (gráfico de 12 h), salud de Ceph.
- **NAS:** por cada NAS, estado, CPU y memoria (gráfico de 12 h con temperatura), discos sanos, temperatura y el volumen más lleno.
- **Red:** equipos en línea, conocidos y apagados, último escaneo, reparto por tipo y equipos nuevos de las últimas 48 h.
- **Raspberry Pi:** temperatura, CPU, memoria, disco, tiempo encendida y estado de la fuente de poder. Solo en una Raspberry Pi agrega el gráfico de 24 h de temperatura con marcas de bajo voltaje y limitación (se guarda 7 días en `metrics.db`).
- **Línea de tiempo:** cambios importantes con hora (UPS a batería, nodo caído, cambio de Ceph, equipos nuevos o que dejaron de responder). Los guardan los módulos, aunque nadie tenga la página abierta: últimos 300 eventos o 30 días.
- Cada persona ve solo los módulos a los que tiene acceso.
- **Actualización:** selector de intervalo (10 s, 30 s, 1, 2, 5 min o manual con ↻), por navegador. Con la pestaña oculta no consulta.

**Modo kiosko** (botón *Kiosko* o `/overview/?kiosk=1`): pantalla completa, letra grande, sin botones ni cursor, y la pantalla no se apaga. Un toque o el mouse muestra el botón para salir. Opciones por URL: `?zoom=0.8` (0.5 a 2) y `?autoscroll=1` (sube y baja solo si no cabe). Se recomienda un usuario de solo lectura.

**iPad como pantalla:** abre `http://IP-DEL-PI/overview/?kiosk=1` en Safari → Compartir → *Añadir a pantalla de inicio*, con *Abrir como app web* activado. Para que no se bloquee: *Acceso guiado* o *Bloqueo automático: Nunca*.

### UPS Monitor
- Empieza sin servidores. Un administrador agrega uno (nombre, host y puerto de `upsd`, por defecto 3493) y puede probar la conexión antes de guardar.
- Consulta `upsd` cada 10 s y guarda el historial en SQLite (WAL, 1 año).
- Gráficos de voltaje, consumo y temperatura (si la UPS la informa). Exporta CSV.
- Muestra los clientes conectados a cada UPS.

### Net Monitor
- **Red:** se detecta sola (la /24 de la Pi) o se fija con `SCAN_NETWORK`.
- **Escaneo:** en una instalación nueva no escanea hasta que lo pidas (botón *Hacer escaneo inicial*). El escaneo automático se activa en *Ajustes* (mínimo 60 s).
- **Detección:** ping (TTL), puertos y banner HTTP. No usa `nmap`.
- **MAC y fabricante**, en este orden: Pi-hole, ARP local, SNMP (ARP de un router o switch). El fabricante sale de la base `manuf` de Wireshark (descarga semanal) o de `ieee-data`.
- **Tipos de equipo:** computador, teléfono, tablet, router, switch, punto de acceso, almacenamiento, TV, cámara, impresora, consola de juegos, servidor, teléfono IP, UPS, altavoz inteligente y otros. SO, tipo y grupo se pueden editar a mano.
- **Basurero** para quitar un equipo de la lista (solo administradores). Si sigue conectado, el próximo escaneo lo vuelve a descubrir.
- Al pasar el mouse (o tocar en iPad) por una IP en UPS, Proxmox, WOL o Resumen aparece una tarjeta con los datos del equipo.
- Las credenciales SNMP y la clave de Pi-hole se guardan con permisos 600 y la API nunca las devuelve.

#### Switch Monitor (pestaña de Net Monitor)
- Segunda pestaña junto a *Equipos*. Para cada switch muestra el panel frontal con el estado de cada puerto (arriba, abajo, deshabilitado, errores nuevos, enlace entre switches, loop), velocidad negociada, paquetes por segundo, errores, STP, temperatura y a qué equipo está conectado cada puerto (cruza la tabla MAC del switch con los equipos que ya conoce Net Monitor).
- **Modelos:** ZX310S (interfaz web), HC-SWTGW218AS (interfaz web) y cualquier switch con SNMP v2c (TP-Link y otros); este último es el único que entrega bytes, así que solo ahí hay Mb/s.
- **Se agregan desde la interfaz** (botón *+ Agregar switch*, solo administradores), con botón *Probar* antes de guardar. Usuario, contraseña o community se guardan en `switches.json` con permisos 600 y la API nunca los devuelve.
- **Solo lectura:** no cambia nada en los switches. Las operaciones peligrosas (borrar contadores del ZX, vaciar la tabla MAC del HC, reiniciar, guardar) están bloqueadas en el código.
- **Historial de 1 año** (como UPS Monitor): temperatura y, por puerto, estado, velocidad, paquetes o Mb/s y errores; rangos 1 h, 1 d, 1 sem, 1 mes y todo. Las tasas se calculan entre muestras y toleran contadores que vuelven a cero.
- **Historial** (subpestaña): totales acumulados por puerto (bytes por SNMP; solo paquetes en ZX y HC), guardados en la base y sin perderse cuando el switch o LabTower se reinician. Suma cuánto avanza cada contador entre lecturas y parte del valor que el switch ya traía al agregarlo.
- **Alertas** en el Resumen (tarjeta Net Monitor y línea de tiempo): switch sin conexión (tras 2 lecturas fallidas), temperatura ≥ 70 °C (aviso) / ≥ 80 °C (crítico), errores nuevos en un puerto, cambios de enlace y loop. Los puertos entre switches no alertan por loop. Los umbrales se pueden cambiar con `SWITCH_TEMP_WARN` y `SWITCH_TEMP_CRIT`.
- **Topología básica** deducida de las tablas MAC. Etiqueta y «enlace a otro switch» se editan por puerto.
- Se consulta cada 60 s por defecto (30 s a 1 h, configurable); cada switch se lee de a una petición a la vez, con pausas, porque sus servidores web son frágiles.
- Diagnóstico por consola: `python3 /opt/labtower/net-monitor/switches.py --config switches.json --once`.

### Proxmox Monitor
- Consulta cada cluster cada 5 s con la página abierta y cada 60 s en reposo.
- Orden de nodos y nodos fijados por cluster (solo admin).
- Al agregar un cluster hay que confirmar la huella SHA-256 de su certificado, que queda fijada. Si el certificado cambia, no se envía el token.

### NAS Monitor
- Funciona como UPS Monitor: una tabla **Resumen de NAS** con todos los NAS (estado, modelo, CPU, RAM, temperatura, discos y volumen más lleno). Cada fila se abre y muestra su detalle debajo; por defecto se abre el primero. También se elige desde el menú lateral.
- Agrega todos los NAS que quieras (como los clusters de Proxmox o los servidores de UPS). Cada uno se consulta por **SNMP v3** (usuario, nivel `authPriv`/`authNoPriv`/`noAuthNoPriv`, clave de autenticación y de cifrado) o por v2c. El botón *Probar conexión* revisa los datos antes de guardar.
- **Detalle de cada NAS:** medidores (CPU, RAM, volumen, temperatura, discos y tiempo encendido), sistema, volúmenes con su espacio, discos con estado y temperatura, red, UPS conectado y actividad de disco.
- **Gráficos** de CPU/RAM, temperatura y red con rangos **1h / 1d / 1mo / Todo**; al pasar el cursor muestran el valor de cada momento. El historial se guarda en `metrics.db` (`NAS_KEEP_DAYS`, 7 días por defecto).
- **Avisos** (también en la línea de tiempo del Resumen): disco con falla, volumen degradado o casi lleno (90 %), temperatura alta y actualización de DSM disponible. Un *Storage Pool* lleno no avisa, porque es normal que lo esté si sus volúmenes usan todo el espacio.
- Las claves SNMP se guardan con permisos 600 y la API nunca las devuelve. Al leer, van en un archivo temporal privado, nunca en la línea de comandos. Al editar, dejar una clave en blanco conserva la guardada.
- **Activar SNMP en el Synology:** *Panel de control → Terminal y SNMP → SNMP → Habilitar SNMPv3*, define usuario y contraseñas (mínimo 8 caracteres) y usa `SHA`/`AES`. Otros NAS que usen las MIB estándar (UCD/IF-MIB) muestran CPU, memoria y red, pero no discos ni volúmenes.
- Necesita los comandos `snmpget` y `snmpbulkwalk` (paquete `snmp`, que ya instala el paquete de LabTower).

### WOL Console
- Envía paquetes mágicos (máximo 10 por minuto por IP).
- Toma equipos detectados por Net Monitor (nombre, MAC, IP y categoría) y usa la IP más reciente si cambió por DHCP.
- Net Monitor marca con la etiqueta *WOL* los equipos registrados aquí.

### Admin Panel
- Usuarios y permisos por módulo (ninguno, solo lectura, ejecutar, admin).
- **Sesiones activas:** dispositivos con sesión (usuario, navegador, IP, última actividad); se puede cerrar una o todas las demás.
- Tarjeta de **Salud del sistema** y **Respaldos** (Teleporter).

### Todos los módulos
- **Idioma:** inglés (por defecto) o español; se comparte entre módulos.
- **Hora 24H/12H** (desde 1.2.2a): botón junto al idioma. Por defecto 24 h; se guarda en el navegador.
- **Recordarme** al iniciar sesión: 1 día, 1 semana, 1 mes o siempre. Sin marcar, la sesión dura 24 h.

---

## HTTPS

Por defecto se sirve por HTTP en el puerto 80, pensado para una red local de confianza. Para cifrar:

```bash
sudo labtower-https enable --redirect                                  # certificado autofirmado
sudo labtower-https enable --redirect --cert fullchain.pem --key privkey.pem   # certificado propio (por ejemplo Let's Encrypt)
sudo labtower-https status
sudo labtower-https disable
```

`--redirect` manda el puerto 80 a HTTPS, marca la cookie como `Secure` y envía HSTS. Con el certificado autofirmado el navegador avisa una vez. En iPad/iPhone hay que instalarlo y confiar en él (Ajustes → General → Información → Ajustes de confianza de certificados). Si se usa un certificado propio, accede por el nombre del certificado y no por la IP.

---

## Respaldos

### Teleporter (manual)
```bash
sudo teleporter backup ~/labtower-$(date +%Y%m%d).tar.gz   # crear
teleporter check ~/labtower-20261009.tar.gz                # verificar, no cambia nada
sudo teleporter restore ~/labtower-20261009.tar.gz         # restaurar (-y para no preguntar)
```

- **Incluye:** usuarios, WOL, UPS (servidores e historial), Net Monitor (hosts, SNMP y switches con su historial), Proxmox, NAS Monitor (lista de NAS e historial), históricos del Resumen, y la configuración de NUT y nginx. **No incluye** sesiones, certificados HTTPS ni la llave del respaldo SFTP.
- **Restaurar NUT y nginx** solo se hace desde la consola con `--nut` y `--nginx`; el panel no lo permite.
- **Antes de restaurar** se guarda una copia del estado actual en `/var/backups/labtower/`.
- **Límites:** se rechaza un archivo que descomprima a más de 2 GiB; las subidas desde el panel tienen tope de 200 MB.
- **Desde el panel** (`/admin/` → *Backup & restore*): crear y descargar, subir, verificar y restaurar. Solo lo usa quien es admin de todos los módulos.
- **Migrar a otra Pi:** instala el `.deb`, entra con `admin`, sube el respaldo y pulsa *Restore*.
- El archivo contiene hashes de contraseñas y tokens (permisos 600): guárdalo en un lugar privado.

### Respaldo automático por SFTP
Un cron diario (03:17) hace un respaldo, lo verifica y lo sube por SFTP. Viene instalado y **desactivado** hasta que se completa `SFTP_USER`. Solo usa llave SSH.

```bash
sudo labtower-sftp-backup setup       # crea la llave SSH y muestra la pública
sudo nano /etc/labtower/backup.conf   # completar SFTP_USER (y SFTP_HOST, SFTP_DIR)
sudo labtower-sftp-backup test        # revisa conexión, carpeta y escritura
sudo labtower-sftp-backup run         # respaldo ahora
sudo labtower-sftp-backup status      # resultado de la última corrida
```

- **Cifrado:** el archivo se sube cifrado con gpg (AES-256). La contraseña se crea sola en `/etc/labtower/backup_passphrase`: **guarda una copia fuera de la Pi** (`sudo cat /etc/labtower/backup_passphrase`), sin ella no se puede abrir ningún respaldo.
- **Restaurar:** baja el `.tar.gz.gpg`, ejecuta `sudo labtower-sftp-backup decrypt archivo.tar.gz.gpg` y luego `sudo teleporter restore archivo.tar.gz`.
- **Seguro:** se sube como `.part` y se renombra; se compara el tamaño remoto; la huella del servidor queda fijada en la primera conexión.
- **Retención:** 30 copias en el storage (`KEEP_REMOTE`) y 7 en el servidor LabTower (`KEEP_LOCAL`). Solo se borran archivos `labtower-auto-<equipo>-<fecha>_<hora>.tar.gz`.
- Resultado en `/var/log/labtower/backup.status`; errores con `journalctl -t labtower-sftp-backup`. El horario se cambia en `/etc/cron.d/labtower-sftp-backup`.
- Usa un usuario SFTP propio, con acceso solo a esa carpeta.

---

## Salud y operación

```bash
labtower-health         # resumen: exit 0 = ok, 1 = degradado, 2 = falla (-j para JSON)
labtower-resources      # memoria y CPU de cada servicio (-w refresca cada 2 s)
systemctl status wol-console labtower-ups admin-panel net-monitor proxmox-monitor nas-monitor dns-monitor wan-monitor labtower-overview
journalctl -u net-monitor -f        # logs de un servicio
sudo systemctl restart net-monitor  # reiniciar uno
```

Cada módulo responde `GET /api/health` (200 = ok o degradado, 503 = falla). Sin sesión solo muestra niveles. Detecta servicio caído, archivo de datos corrupto, disco casi lleno, base de historial bloqueada, escaneo trabado, y `upsd`, Proxmox o un NAS sin respuesta. En una Raspberry Pi avisa además de bajo voltaje o limitación; ese aviso viene del firmware y solo se borra al reiniciar.

| Servicio | Módulo |
|---|---|
| `wol-console` | WOL Console |
| `labtower-ups` | UPS Monitor (antes `nut-monitor`, que chocaba con el `upsmon` de NUT) |
| `admin-panel` | Admin Panel |
| `net-monitor` | Net Monitor |
| `proxmox-monitor` | Proxmox Monitor |
| `nas-monitor` | NAS Monitor |
| `dns-monitor` | DNS Monitor |
| `wan-monitor` | WAN Monitor |
| `labtower-overview` | Resumen |

**Desinstalar:** `sudo apt remove labtower` detiene los servicios y guarda una copia de los datos en `/var/backups/labtower`. `sudo apt purge labtower` elimina además el código, los servicios, el sitio nginx y el usuario `labtower`. En ambos casos `/var/lib/labtower` y `/var/backups/labtower` **no se borran**; elimínalos a mano si quieres dejar el equipo limpio.

---

## Configuración

Los valores por defecto sirven para la mayoría. Para cambiarlos, escribe `NOMBRE=valor` en `/etc/default/labtower` y reinicia los servicios:

```bash
echo 'NUT_POLL=5' | sudo tee -a /etc/default/labtower
sudo systemctl restart wol-console labtower-ups admin-panel net-monitor proxmox-monitor nas-monitor dns-monitor wan-monitor labtower-overview
```

| Variable | Módulo | Por defecto | Para qué |
|---|---|---|---|
| `SCAN_NETWORK` | Net | /24 de la Pi | Red a escanear (ej. `192.0.2.0/24`) |
| `SCAN_INTERVAL` | Net | manual | Segundos entre escaneos automáticos (0 = manual) |
| `SCAN_PORTS` | Net | puertos comunes | Puertos que se sondean |
| `PORT_TIMEOUT` | Net | `0.5` | Segundos de espera por puerto |
| `MAX_WORKERS` | Net | `30` | Equipos que se escanean a la vez |
| `PIHOLE_HOSTS`, `PIHOLE_PASS` | Net | vacío | Pi-hole (también se configura en la página) |
| `NUT_POLL` | UPS | `10` | Segundos entre consultas a `upsd` |
| `NUT_DB_FLUSH` | UPS | `60` | Segundos entre escrituras del historial |
| `PVE_POLL_ACTIVE`, `PVE_POLL_IDLE` | Proxmox | `5`, `60` | Segundos entre consultas con la página abierta / en reposo |
| `PVE_KEEP_DAYS` | Proxmox | `7` | Días de historial de CPU y memoria |
| `NAS_POLL_ACTIVE`, `NAS_POLL_IDLE` | NAS | `15`, `60` | Segundos entre consultas con la página abierta / en reposo |
| `NAS_KEEP_DAYS` | NAS | `7` | Días de historial de cada NAS |
| `LABTOWER_PI_KEEP_DAYS` | Resumen | `7` | Días de historial de la Pi |
| `WOL_BROADCAST` | WOL | automático | Direcciones de broadcast separadas por coma |
| `LABTOWER_SECURE_COOKIE` | todos | apagado | `1` marca la cookie como `Secure` (solo detrás de HTTPS) |

---

## Seguridad

Pensado para una **red local de confianza**. No expongas el puerto 80 a internet.

- **Acceso:** los servicios Python escuchan solo en `127.0.0.1`; solo nginx es visible en la red. Para cifrar, ver [HTTPS](#https).
- **Contraseñas:** mínimo 8 caracteres, guardadas con scrypt. La cuenta inicial usa una contraseña aleatoria que hay que cambiar.
- **Intentos de login:** 5 fallos desde una IP en 10 minutos bloquean esa IP por 5 minutos; cada cuenta tiene además su propio límite. El contador es compartido por todos los módulos. nginx limita peticiones y conexiones por IP.
- **Sesiones:** cookie `HttpOnly` y `SameSite=Strict`; en disco solo se guarda el hash SHA-256 del token. Se pueden ver y cerrar en el Admin Panel.
- **CSRF:** toda petición que modifica datos se rechaza (403) si no viene de la propia página.
- **CSP estricta:** sin scripts ni manejadores en línea (`script-src 'self'`). Navegadores: Chrome 75+, Firefox 105+, Safari 15.4+.
- **Permisos por módulo:** un administrador solo da o quita permisos en los módulos donde él mismo tiene ese nivel, y no puede borrar ni cambiar la clave de un usuario con más permisos.
- **Privilegios mínimos:** el código de `/opt/labtower` es de root y de solo lectura para los servicios; sus datos viven en `/var/lib/labtower/`. Los servicios systemd van endurecidos. Los scripts que corren como root (instalador, Teleporter, respaldo SFTP) no siguen enlaces simbólicos dentro de carpetas de los servicios.
- **Entradas validadas:** hosts y nombres de NUT, Proxmox, NAS y Pi-hole; el certificado de Pi-hole se fija en la primera conexión; la huella de cada cluster Proxmox queda fijada. Un cluster antiguo sin huella muestra un aviso permanente (usa *Fijar certificado*).
- **Respaldo desde el panel:** corre como root mediante una regla `sudo` limitada a `teleporter.sh gui-backup` y `gui-restore`. Restaurar la configuración de NUT puede introducir comandos que `upsd` ejecuta como root: restaura solo respaldos de confianza.

---

## Estructura

```
labtower/
├── auth/              # autenticación compartida, Admin Panel y respaldos del panel
├── wol-console/       # cada módulo: server.py + static/
├── nut-monitor/       # (UPS Monitor)
├── net-monitor/
├── proxmox-monitor/
├── nas-monitor/       # NAS Monitor (Synology por SNMP)
├── dns-monitor/       # DNS Monitor (Pi-hole / AdGuard Home)
├── wan-monitor/       # WAN Monitor (internet)
├── overview/          # Resumen
├── home/              # página de inicio e iconos
├── etc/               # nginx, backup.conf, cron
├── scripts/           # teleporter.sh, labtower-sftp-backup, -https, -health, -resources, apt-repo.py
├── debian/            # empaquetado .deb
├── assets/icons/      # icono fuente y script que regenera los PNG
├── assets/brand/      # kit de marca: un icono por módulo y la paleta
├── tests/             # pruebas automáticas (unittest)
├── docs/              # APT.md y capturas
├── CHANGELOG.md, RELEASE_NOTES_2.0.md, VERSION, LICENSE
└── README.md, README.en.md
```

En la Pi:

| Ruta | Contenido |
|---|---|
| `/opt/labtower/` | Código (lo reemplaza cada actualización) |
| `/var/lib/labtower/` | Datos: `users.json`, `<módulo>/`, `metrics.db`, `events.json` |
| `/etc/labtower/` | `backup.conf`, llave y contraseña del respaldo, `tls/` |
| `/var/backups/labtower/` | Copias antes de actualizar, desinstalar o restaurar |
| `/var/log/labtower/` | Estado del respaldo SFTP y registro de restauración |
| `/usr/local/bin/` | `teleporter`, `labtower-sftp-backup`, `labtower-https`, `labtower-health`, `labtower-resources` |

Cada módulo es un servidor HTTP Python independiente. Todos usan `auth/auth.py` para usuarios y sesiones.

Pruebas (solo biblioteca estándar, sin tocar `/var/lib`): `python3 -m unittest discover -s tests -t . -v`

Los comentarios del código están en español e inglés (los de inglés llevan el prefijo `EN:`). Existe un generador de repositorio APT en `scripts/apt-repo.py` (aún sin publicar, ver [docs/APT.md](docs/APT.md)).

---

## Licencia

[PolyForm Noncommercial 1.0.0](LICENSE), desde la versión 1.3.

- **Gratis** para uso personal, hobby, estudio, educación y organizaciones sin fines de lucro.
- **El uso comercial (por ejemplo, dentro de una empresa) y los derivados comerciales requieren permiso escrito del autor.** Para pedirlo, abre un issue en GitHub.
- Las versiones anteriores a la 1.3 se publicaron con licencia MIT; esas copias conservan esa licencia.

Creado con ayuda de IA.
