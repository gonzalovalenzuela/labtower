# Changelog

## 1.2.0c — 2026-10-13

### Instalación nueva
- **Cambio de contraseña obligatorio en el primer ingreso.** La cuenta inicial `admin`/`admin` (y cualquier cuenta marcada «debe cambiar contraseña» desde el Admin Panel) pasa por una pantalla de cambio de contraseña antes de entrar a cualquier módulo; al guardarla vuelve al módulo desde el que ingresó y ya puede navegar a los demás. Se exige la contraseña actual, una nueva de al menos 6 caracteres y distinta de la actual.
- **Se aplica en el servidor, no solo en la página**: mientras la contraseña esté pendiente, la sesión no sirve en ningún módulo (todas las llamadas dan 401) salvo para cambiarla (`/admin/change-password`). Funciona con cualquier usuario, también sin permisos de administrador. Al cambiarla se cierran las demás sesiones de esa cuenta.
- **Net Monitor no escanea nada por defecto** en una instalación nueva: arranca en modo manual (intervalo 0) y, cuando no hay equipos, la página muestra la red detectada y el botón **«Hacer escaneo inicial»**. Se puede activar el escaneo automático en Ajustes. Las instalaciones existentes conservan su intervalo.
- En modo manual (intervalo 0) Net Monitor tampoco escanea al arrancar el servicio; antes lo hacía siempre una vez.
- **El escaneo va poblando la lista**: cada equipo encontrado se guarda enseguida (como máximo cada 2 s) y la página se refresca cada 3 s durante el escaneo, sin esperar a que termine toda la red. Mientras escanea con la lista vacía muestra «Escaneando…».

### UPS Monitor
- **Primera UPS recién agregada**: la tabla muestra «Conectando con el servidor NUT…» (en vez de «No UPS found») y la página refresca cada 1,5 s hasta que llegan los datos, sin recargar a mano. Las dos primeras lecturas de cada UPS se guardan de inmediato, así los gráficos tienen puntos a los pocos segundos en vez de esperar hasta 60 s.
- El subtítulo «NUT · APC · Eaton» pasa a «NUT UPS».

## 1.2.0b — 2026-10-13

### Instalación nueva
- **UPS Monitor ya no crea un servidor «Local» por defecto**: una instalación nueva empieza sin servidores (no hace falta tener una UPS); se agrega uno desde la página. Las instalaciones existentes conservan los suyos.
- **`snmp` pasa a ser dependencia** del paquete (antes solo sugerida), para que la fuente SNMP de Net Monitor funcione sin pasos extra.
- **Net Monitor**: la red a escanear por defecto es la /24 de la IP de la máquina (antes fijaba `192.168.0.0/24`); se puede cambiar con `SCAN_NETWORK`. Los servidores Pi-hole ya no vienen precargados.
- Los ejemplos (placeholders) de IP en WOL, UPS, Net Monitor y Proxmox usan direcciones de documentación (`192.0.2.x`) en lugar de IP de una red real.
- Orden de navegación por defecto en todas las páginas: UPS Monitor, Net Monitor, Proxmox, WOL Console, Admin Panel (quien ya reordenó el menú conserva su orden).

## 1.2.0a — 2026-10-13

### Correcciones
- **Instalación nueva: la página de inicio daba `500 Internal Server Error`.** nginx servía `/` desde `/opt/pi-console-home/`, pero el paquete instala la portada en `/opt/pi-console/home/`; la carpeta antigua solo existía en equipos con instalación manual previa. Ahora nginx usa `/opt/pi-console/home` (también en actualizaciones: la portada se actualiza con el paquete).
- Documentación: la instalación indica `apt-get install ./pi-console_X.deb` (resuelve dependencias) en lugar de `dpkg -i`.

## 1.2.0 — 2026-10-12

Primer release de la serie 1.2. Reúne todos los cambios de 1.1.8b a 1.1.9j (listados abajo) y agrega el código comentado.

### Código comentado en español e inglés
- Todo el código fuente lleva comentarios en **español** y, a continuación, en **inglés** (marcados con `EN:`): los 5 servicios Python, el módulo de autenticación, `teleporter.sh`, los scripts de salud y recursos, los scripts del paquete (`postinst`, `preinst`, `prerm`, `postrm`), la configuración de nginx y las 7 páginas HTML. Cada archivo empieza con un mapa de su estructura y el flujo de datos; cada función explica qué hace y, cuando importa, por qué.
- Solo se agregaron comentarios; la lógica no cambió. Se verificó que el código sin comentarios quedara idéntico (Python por AST; shell, nginx y HTML por comparación de líneas, más `bash -n` y `node --check`).
- Los mensajes de log y de error de los servicios que quedaban en español ahora están en inglés («Admin permission required», «Duplicate MAC», «Scan finished…», etc.).

### Interfaz
- En pantallas de hasta 960 px la barra lateral estaba oculta y no había forma de cambiar de módulo. Ahora hay un botón de menú (☰) en la barra superior que abre la navegación como panel lateral, con fondo atenuado; se cierra al tocar el fondo, un enlace o con Esc. Aplica a WOL Console, UPS Monitor, Net Monitor, Proxmox y Admin Panel.
- La barra superior pasa a varias filas en móvil para que todos sus controles (idioma, tema, usuario, escaneo) sean alcanzables.
- Todas las páginas (WOL, UPS, Net Monitor, Proxmox y Admin, incluida la pantalla de login) muestran *Pi Console vX.Y.Z* en el pie. La versión sale del archivo `/opt/pi-console/VERSION` que instala el paquete, vía `GET /api/version` de cada servicio (también aparece en `/api/health`).
- Diseño: en pantallas de laptop (≈1366 px o menos) Net Monitor y WOL Console se salían de la pantalla por la derecha porque la barra superior no cabía; ahora la barra se acomoda en varias filas y no hay desbordamiento horizontal entre 320 y 1366 px. En móvil, el Admin Panel ya no se ensancha más que la pantalla (las tablas se desplazan dentro de su tarjeta).
- Net Monitor: textos que quedaban en español con la interfaz en inglés («Todos», «seg», «cada 1h», «hace 8m», tooltips, detalle del host, progreso del escaneo) ahora siguen el idioma elegido.
- Móvil: en el Admin Panel las tablas se desplazan dentro de su tarjeta sin mover el título ni el botón *New user*, y la barra superior alinea sus márgenes con el contenido. En UPS Monitor la tabla de resumen cabe en pantallas de 360 px aunque el modelo/serie sea largo, y el panel de detalle del UPS queda siempre visible aunque la tabla se desplace.
- Móvil: en el Admin Panel la lista de usuarios y la de backups pasan a tarjetas (una por usuario/backup), sin columnas cortadas ni desplazamiento lateral.
- Tablets (≈800–1280 px, p. ej. iPad horizontal): en WOL Console el panel *Add device* pasa debajo de la tabla y el botón *Wake* ya no queda cortado; en Net Monitor el vendor/MAC se muestra solo en la fila expandida, los nombres largos se parten y la tabla cabe sin desplazarse aunque haya muchos puertos abiertos.

### WOL Console
- Lee los hosts de Net Monitor (`net-monitor/hosts.json`, solo lectura): en *Add device* aparece **From Net Monitor** (solo admin con acceso a Net Monitor) para elegir un host detectado; rellena nombre, MAC, IP y categoría (computer→PC, storage→NAS, el resto→OTHER). Los ya agregados aparecen deshabilitados.
- Si Net Monitor conoce otra IP para la misma MAC (DHCP), la tabla muestra la IP de Net Monitor (la guardada queda tachada) y *Wake* la usa para comprobar si el equipo ya está encendido.
- Nuevo endpoint `GET /api/netmonitor/hosts` (requiere permiso `net` de lectura). Variables opcionales: `NET_HOSTS_FILE` (WOL) y `WOL_DEVICES_FILE` (Net Monitor).

### UPS Monitor
- Los servidores NUT ahora se pueden **editar** (nombre, host y puerto) desde el botón de lápiz de la barra lateral, además de eliminarlos. Al cambiar host o puerto se reconecta de inmediato y se descartan los datos del destino anterior; el historial se conserva. Nuevo endpoint `PUT /api/servers/<id>` (solo admin).
- La cabecera de los dos gráficos (voltaje y consumo) ahora tiene el mismo diseño: título a la izquierda, rangos 1h/1d/1mo/All a la derecha y la leyenda entre ambos; en pantallas de hasta 700 px, título y rangos en la primera línea y la leyenda debajo, igual en los dos. Antes el gráfico de voltaje pasaba los rangos a una segunda línea y el de consumo no.
- Se pueden eliminar todos los servidores, incluido el *Local*. Sin servidores el panel muestra "No UPS found" y el resto de los módulos no se ve afectado; la lista vacía se conserva tras reiniciar y se puede volver a agregar un servidor cuando se quiera. Antes solo el servidor Local no se podía eliminar.

### Net Monitor
- Nuevos tipos de dispositivo **printer** (impresora) y **tablet**. Impresoras: fabricantes (Brother, Canon, Epson, Lexmark, Xerox, Ricoh, Kyocera…), nombres de host (NPI…, LaserJet, MFC…), puertos 9100/515/631 y banners. Tablets: iPad, Galaxy Tab, Kindle, MiPad, etc.; un iPhone/Android sigue siendo *phone*. Disponibles en filtros y en la edición manual.
- Los hosts que están registrados en WOL Console (misma MAC) muestran la etiqueta **WOL**.
- La tabla de hosts ya no se desborda en pantallas angostas: hasta 700 px se ocultan las columnas Vendor/MAC, puertos, latencia y último visto, y hasta 480 px también OS. Todo eso sigue disponible al expandir la fila (toca el nombre del host).

### Módulo de salud
- Cada servicio expone `GET /api/health` (sin login: solo niveles ok/warn/fail; con sesión, el detalle) y responde 503 si algo falla. Revisa archivos de datos legibles/escribibles, espacio en disco, y por módulo: WOL (red y lista de Net Monitor), UPS (base de datos, que el historial **realmente se esté guardando**, pollers vivos, upsd respondiendo), Net Monitor (escaneo trabado, temporizador de auto-escaneo armado) y Proxmox (pollers vivos, clusters respondiendo).
- El Admin Panel agrega la salud de todos los módulos en una tarjeta **Salud del sistema** (se refresca cada 30 s) y en `GET /admin/api/health`.
- Cada módulo de la tarjeta se expande al hacer clic y muestra todo lo que se revisa: cada chequeo con su descripción, su nivel (verde/naranja/rojo) y el detalle (espacio libre, filas pendientes, error exacto, tiempo activo). Se mantiene abierto al refrescar.
- Nuevo comando `pi-console-health` (código de salida 0 = ok, 1 = degradado, 2 = falla; `-j` muestra el JSON), útil para cron o monitoreo externo.
- **Fuente de la Raspberry Pi:** el Admin Panel y `pi-console-health` muestran el chequeo `power` con aviso cuando la Pi registra subtensión o limitación (por fuente o cable insuficiente), sea ahora o desde el arranque. Solo aparece en una Raspberry Pi: en una VM u otro equipo no se muestra. Los eventos «desde el arranque» solo se borran al reiniciar. El instalador agrega al usuario del servicio al grupo `video` en una Pi para poder leer `vcgencmd get_throttled`.

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
- Los servicios aceptan ráfagas de conexiones simultáneas (cola de escucha de 5 a 128): antes, 30 peticiones a la vez podían terminar con la conexión reiniciada.

### Documentación
- Capturas de pantalla de todos los módulos (claro/oscuro, 4 resoluciones) en `docs/screenshots/` y galería en el README.

### Idioma
- Quedaban textos en español con la interfaz en inglés en WOL Console (filtro «Todos», tooltips, avisos y el «hace 8m»), UPS Monitor (tooltips y campo de servidor) y Proxmox Monitor («Conectando…», «Sin nodos»): ahora siguen el idioma elegido. Las fechas usan el formato del idioma.
- Mensajes de error del backend traducidos al inglés («User already exists», «Device not found», «Not found», «That host:port already exists», «Magic packet sent to …»).

### Herramientas
- Nuevo comando `pi-console-resources`: memoria (RSS) y CPU de cada servicio, de nginx y RAM libre del sistema (`-w` para verlo en vivo). Sirve para decidir si hace falta mover Pi Console fuera de la Pi.

### Seguridad
- Contraseñas: ahora se guardan con **scrypt** y una sal aleatoria por usuario (antes SHA-256 con una sal fija). Los usuarios existentes se migran solos en su próximo inicio de sesión; los respaldos antiguos siguen funcionando.
- Inicio de sesión: tras 5 intentos fallidos desde la misma IP se bloquea el acceso durante 5 minutos (respuesta 429). Cada fallo añade una pequeña espera, y un usuario inexistente tarda lo mismo que uno real. Los contadores son por servicio y se reinician al reiniciarlo.
- nginx: cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y una política `Content-Security-Policy` básica.
- **users.json ausente (SEC-01):** si el archivo de usuarios desaparece en una instalación ya usada, ya no se vuelve a crear el usuario `admin` / `admin`: se usa la copia `.bak` o, si no existe, nadie puede entrar hasta restaurarla. El usuario inicial solo se crea en una instalación nueva (marcador `.users-initialized` en `/var/lib/pi-console`).
- **WOL Console** escucha solo en `127.0.0.1`, como los demás módulos; se accede por nginx (puerto 80).
- **Permisos explícitos (PVE-01):** `net` y `pve` ya no se derivan del permiso WOL en cada petición. Al arrancar los servicios se migran una sola vez a valores explícitos (admin si era admin de WOL, solo lectura en otro caso) y un permiso ausente significa sin acceso. El Admin Panel muestra y edita ahora las columnas **Net Monitor** y **Proxmox**; los usuarios nuevos reciben *Sin acceso* a ambos por defecto.
- **Proxmox, certificado (PVE-02):** al agregar un cluster se muestra la huella SHA-256 del certificado y hay que confirmarla (botón *Probar* dos veces) antes de enviar el token; la conexión queda fijada a esa huella y falla si el certificado cambia. Los clusters existentes siguen funcionando, pero muestran el aviso «Certificado sin verificar» con un botón para fijarlo.
- **Restore de NUT y nginx solo por consola (SEC-03):** el panel ya no ofrece restaurar `/etc/nut` ni el sitio nginx (corrían como root vía sudo); `teleporter restore --nut` / `--nginx` sigue disponible en la consola. `teleporter.sh gui-restore` rechaza esas opciones.
- **Bloqueo entre procesos (CON-01):** si no se puede obtener el bloqueo de archivo, la operación falla con error en lugar de continuar sin él.

### Instalación
- Los mensajes de instalación, actualización y desinstalación (`postinst`, `preinst`, `prerm`, `postrm`) ahora están en inglés.

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
