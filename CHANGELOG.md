# Changelog

## 1.1.8c — 2026-10-10

### UPS Monitor (interfaz)
- La cabecera de los dos gráficos (voltaje y consumo) ahora tiene el mismo diseño: título a la izquierda, rangos 1h/1d/1mo/All a la derecha y la leyenda entre ambos; en pantallas de hasta 700 px, título y rangos en la primera línea y la leyenda debajo, igual en los dos. Antes el gráfico de voltaje pasaba los rangos a una segunda línea y el de consumo no.

### Instalación
- Los mensajes de instalación, actualización y desinstalación (`postinst`, `preinst`, `prerm`, `postrm`) ahora están en inglés.

### Módulo de salud
- Cada servicio expone `GET /api/health` (sin login: solo niveles ok/warn/fail; con sesión, el detalle) y responde 503 si algo falla. Revisa archivos de datos legibles/escribibles, espacio en disco, y por módulo: WOL (red y lista de Net Monitor), UPS (base de datos, que el historial **realmente se esté guardando**, pollers vivos, upsd respondiendo), Net Monitor (escaneo trabado, temporizador de auto-escaneo armado) y Proxmox (pollers vivos, clusters respondiendo).
- El Admin Panel agrega la salud de todos los módulos en una tarjeta **Salud del sistema** (se refresca cada 30 s) y en `GET /admin/api/health`.
- Cada módulo de la tarjeta se expande al hacer clic y muestra todo lo que se revisa: cada chequeo con su descripción, su nivel (verde/naranja/rojo) y el detalle (espacio libre, filas pendientes, error exacto, tiempo activo). Se mantiene abierto al refrescar.
- Nuevo comando `pi-console-health` (código de salida 0 = ok, 1 = degradado, 2 = falla; `-j` muestra el JSON), útil para cron o monitoreo externo.

### Revisión de código: bloqueos, concurrencia y robustez
- **Servidores HTTP multihilo con timeout** (WOL, UPS, Net Monitor, Proxmox, Admin): antes eran de un solo hilo, así que un cliente lento o colgado bloqueaba todo el módulo. Ahora cada conexión tiene su hilo y un timeout.
- **`users.json` y `sessions.json` compartidos por 5 procesos**: lectura-modificación-escritura bajo `flock`, escritura atómica (fsync + rename, archivo temporal propio) y copia `.bak` de la última versión válida. Archivos con permisos 0600. Un `users.json` dañado ya no reactiva `admin/admin`: se usa la copia `.bak` o, sin ella, no entra nadie hasta borrar el archivo.
- **Sesiones**: usuarios eliminados o con permisos reducidos pierden el acceso de inmediato (antes seguía vigente hasta 24 h); al cambiar contraseña o eliminar un usuario se cierran sus otras sesiones.
- **Datos de cada módulo** (`devices.json`, `wake_log.json`, `servers.json`, `hosts.json`, `config.json`, `clusters.json`): escritura atómica con copia `.bak`, y las altas/bajas/ediciones concurrentes ya no se pisan entre sí. `config.json` y `clusters.json` (tokens, SNMP, Pi-hole) pasan a 0600.
- **UPS Monitor**: un `ERR DATA-STALE` de upsd ya no inserta filas en cero en el historial; la base espera hasta 30 s por un bloqueo en vez de fallar; un error inesperado no mata el hilo de consulta (se reinicia solo); `/api/test` requiere admin.
- **Net Monitor**: dos escaneos simultáneos ya no pueden arrancar; el escaneo siempre libera su estado y reprograma un único temporizador (antes un reescaneo de una IP o un cambio de intervalo podían acumular temporizadores); cambiar el intervalo ya no borraba la configuración SNMP/OUI/Pi-hole; borrar un host durante un escaneo ya no reaparece; validación de IP/intervalo.
- **WOL Console**: envío del magic packet nativo (ya no depende del paquete `wakeonlan`, que no estaba declarado) y respeta el puerto del dispositivo; `/api/ping` valida el host (no acepta opciones de línea de comandos); contador de rate-limit con bloqueo y limpieza.
- **Proxmox**: `/api/test` requiere admin; el token API no se devuelve al crear un cluster; el hilo de consulta no muere por un error de lectura de configuración.

### Correcciones
- **UPS Monitor dejaba de guardar el historial (gráficos de consumo sin datos nuevos)**: aproximadamente 4 horas después de iniciar el servicio, la limpieza periódica de la base (`db_prune`) fallaba con `database table is locked` y dejaba abierta su conexión; desde ese momento todos los guardados fallaban con `database is locked` hasta reiniciar el servicio. Ahora la limpieza cierra la transacción antes de compactar el WAL, siempre libera la conexión y un error ahí ya no afecta al resto.

### Net Monitor (móvil)
- La tabla de hosts ya no se desborda en pantallas angostas: hasta 700 px se ocultan las columnas Vendor/MAC, puertos, latencia y último visto, y hasta 480 px también OS. Todo eso sigue disponible al expandir la fila (toca el nombre del host).

### UPS Monitor
- Se pueden eliminar todos los servidores, incluido el *Local*. Sin servidores el panel muestra "No UPS found" y el resto de los módulos no se ve afectado; la lista vacía se conserva tras reiniciar y se puede volver a agregar un servidor cuando se quiera. Antes solo el servidor Local no se podía eliminar.

## 1.1.8b — 2026-10-10

### Interfaz móvil
- En pantallas de hasta 960 px la barra lateral estaba oculta y no había forma de cambiar de módulo. Ahora hay un botón de menú (☰) en la barra superior que abre la navegación como panel lateral, con fondo atenuado; se cierra al tocar el fondo, un enlace o con Esc. Aplica a WOL Console, UPS Monitor, Net Monitor, Proxmox y Admin Panel.
- La barra superior pasa a varias filas en móvil para que todos sus controles (idioma, tema, usuario, escaneo) sean alcanzables.

### Net Monitor
- Nuevos tipos de dispositivo **printer** (impresora) y **tablet**. Impresoras: fabricantes (Brother, Canon, Epson, Lexmark, Xerox, Ricoh, Kyocera…), nombres de host (NPI…, LaserJet, MFC…), puertos 9100/515/631 y banners. Tablets: iPad, Galaxy Tab, Kindle, MiPad, etc.; un iPhone/Android sigue siendo *phone*. Disponibles en filtros y en la edición manual.
- Los hosts que están registrados en WOL Console (misma MAC) muestran la etiqueta **WOL**.

### WOL Console
- Lee los hosts de Net Monitor (`net-monitor/hosts.json`, solo lectura): en *Add device* aparece **From Net Monitor** (solo admin con acceso a Net Monitor) para elegir un host detectado; rellena nombre, MAC, IP y categoría (computer→PC, storage→NAS, el resto→OTHER). Los ya agregados aparecen deshabilitados.
- Si Net Monitor conoce otra IP para la misma MAC (DHCP), la tabla muestra la IP de Net Monitor (la guardada queda tachada) y *Wake* la usa para comprobar si el equipo ya está encendido.
- Nuevo endpoint `GET /api/netmonitor/hosts` (requiere permiso `net` de lectura). Variables opcionales: `NET_HOSTS_FILE` (WOL) y `WOL_DEVICES_FILE` (Net Monitor).

### UPS Monitor
- Los servidores NUT ahora se pueden **editar** (nombre, host y puerto) desde el botón de lápiz de la barra lateral, además de eliminarlos. Al cambiar host o puerto se reconecta de inmediato y se descartan los datos del destino anterior; el historial se conserva. Nuevo endpoint `PUT /api/servers/<id>` (solo admin).

## 1.1.8 — 2026-10-10

Reúne los cambios de 1.1.7 y sus revisiones (1.1.7a–1.1.7f).

### Net Monitor
- Tipos de dispositivo: computer, phone, tablet, printer, router, switch, ap, storage, tv, camera, appliance, other. Columna *Type*, filtros por tipo y edición manual (`auto` vuelve a la detección).
- Detección por puntajes (vendor, banner, hostname, puertos, gateway, TTL, MAC aleatoria). Los NAS ya no se detectan como Windows; Android/iOS se clasifican como phone.
- El tipo/OS editado ya no se pierde al terminar un escaneo.
- Se muestra la MAC cuando no se detecta el vendor. Fuentes de MAC: Pi-hole, ARP local, SNMP.
- Fuente SNMP configurable (host, puerto, v1/2c/3, community, usuario v3, auth/privacy, timeout, botón *Test*). Lee `ipNetToMediaPhysAddress` con respaldo a `ipNetToPhysicalPhysAddress`. Las credenciales no se devuelven por la API y `config.json` queda con permisos 600.
- Base de vendors (OUI): `manuf` de Wireshark con descarga semanal, respaldo a `ieee-data`, actualización manual y estado en el panel.
- Los nombres de host de Pi-hole perdían caracteres finales al quitar `.local`.

### Proxmox Monitor
- Refresco más rápido: una sola llamada a `/cluster/resources` (con respaldo por nodo), conexión HTTPS persistente, sondeo de 5 s con la vista activa y 60 s en reposo, datos lentos cada 60 s, historial cada 30 s.
- Orden estable de nodos, orden manual (arrastrar o flechas) y pin por nodo, guardados por cluster.
- `/api/clusters` ya no expone `token_value` a usuarios viewer.

### UPS Monitor
- Layout compacto que cabe en una pantalla (probado en 1366x768, 1440x900 y 1920x1080). *Activity* pasa al fondo; los gráficos se ajustan al alto libre.
- Gráficos vacíos en la última hora: el cliente volvía a filtrar con el reloj del navegador y descartaba todo si difería del reloj de la Pi. Ahora el recorte usa el punto más reciente del historial.
- El servicio systemd se llama ahora `pi-console-ups` (antes `nut-monitor`). El nombre antiguo tapaba el servicio `upsmon` de `nut-client`: `systemctl restart nut-monitor` y `nut.target` arrancaban el dashboard en lugar de `upsmon`. Al actualizar, el `postinst` elimina la unidad antigua y, si hay `MONITOR` en `/etc/nut/upsmon.conf`, habilita y arranca el `nut-monitor` real. Logs: `journalctl -u pi-console-ups`.

### Inicio de sesión
- Login directo en un módulo (WOL, UPS, Net, Proxmox) fallaba con `ME.username[0]`: `/api/login` no devolvía el usuario. Ahora lo devuelve y la interfaz tolera que falte.

### Interfaz
- Campos de entrada con fondo más oscuro y borde más marcado en tema claro y oscuro.

### Teleporter (respaldo y restauración)
- `/usr/local/bin/teleporter.sh` (enlace `teleporter`): `teleporter backup`, `teleporter check <archivo>`, `sudo teleporter restore <archivo> [-y] [--nut] [--nginx]`. `pi-console-backup` y `pi-console-restore` son atajos.
- Respalda usuarios y sesiones, dispositivos WOL, servidores UPS e `history.db` (snapshot SQLite consistente), hosts/config de Net Monitor, clusters Proxmox, y opcionalmente configuración de NUT y sitio nginx.
- `check` valida gzip, rutas seguras, SHA-256, JSON, integridad SQLite y que `users.json` no esté vacío; no modifica nada.
- `restore` verifica antes de tocar, crea un snapshot en `/var/backups/pi-console/`, detiene servicios, reemplaza archivos de forma atómica (0600), valida `nginx -t` (revierte si falla), usa bloqueo contra ejecuciones simultáneas y siempre reinicia los servicios. Acepta respaldos del teleporter 1.x.
- Configuración de NUT y sitio nginx se restauran solo con `--nut` / `--nginx` (desactivado por defecto; NUT se configura manualmente).
- Variables de entorno de pruebas se ignoran bajo `sudo`.

### Admin Panel
- Tarjeta *Backup & restore* en `/admin/`: crear (descarga automática), subir, verificar, restaurar, descargar y eliminar respaldos. Permite migrar a una instalación nueva: instalar el `.deb`, subir el respaldo y pulsar *Restore*; luego iniciar sesión con los usuarios del respaldo.
- La restauración corre como root mediante `/etc/sudoers.d/pi-console-teleporter` (solo `teleporter.sh gui-backup` y `gui-restore`), en la unidad `pi-console-restore`, con registro en `/var/lib/pi-console/teleporter/restore.log`.
- Respaldos en `/var/lib/pi-console/teleporter/` (se conservan 5; subidas se borran tras 24 h). Límite de subida: 200 MB.
- Endpoints (solo admin): `GET /api/teleporter`, `POST /api/teleporter/{backup,upload,check,restore}`, `GET /api/teleporter/download/<archivo>`, `DELETE /api/teleporter/<archivo>`.
- nginx `/admin/`: cuerpos de hasta 200 MB, sin buffer de subida, timeouts de 300 s.

### Paquete
- Nueva dependencia: `sudo`. Nuevos `Suggests`: `ieee-data`, `snmp`.
- `postinst` crea el directorio del teleporter y la regla sudo (validada con `visudo -c`); `postrm` la elimina.
- Los datos de usuario (`clusters.json`, `hosts.json`, `config.json`) se conservan al actualizar.

### Conocido
- En pantallas de ~390 px el UPS Monitor desborda horizontalmente.
- El banner del `postinst` siempre muestra el usuario inicial `admin / admin`, también al actualizar.
