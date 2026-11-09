### Nuevo módulo: Uptime Monitor
- **Nuevo:** Uptime Monitor (`/uptime/`, servicio `labtower-uptime`). Revisa servicios por HTTP(S), TCP y DNS cada cierto intervalo (60 s por defecto, de 20 s a 1 h). HTTP(S): código de respuesta esperado y palabra clave opcional. DNS: registro A o AAAA, con resolvedor propio o uno dado, e IP esperada opcional.
- **Nuevo:** un servicio se marca caído después de 3 fallos seguidos (configurable de 1 a 6); mientras tanto queda «Pendiente».
- **Nuevo:** barra con las últimas 50 revisiones, disponibilidad de 24 h, 7 y 30 días, y gráfico del tiempo de respuesta con rangos y comparación con el periodo anterior.
- **Nuevo:** vencimiento de certificados HTTPS, con aviso 14 días antes. «No verificar el certificado» acepta autofirmados y sigue revisando el vencimiento.
- **Nuevo:** los monitores se reordenan arrastrando (botones ↑ ↓ en pantallas táctiles).
- **Nuevo:** permiso «Uptime Monitor» por usuario. Al actualizar, quien administra WOL queda como administrador y el resto con solo lectura. Entra en los respaldos y se puede apagar con `labtower-modules`.
- **Nuevo:** Resumen: tarjeta de Uptime y eventos de caído, recuperado y certificado por vencer o vencido.

### Resumen y todos los módulos
- **Mejora:** el aviso «Atención» de cada módulo muestra el detalle de lo que falla. Proxmox con una lectura fallida ya no aparece como OK, y los avisos de NAS, DNS, VPN, Uptime y módulos sin respuesta incluyen el error.
- **Arreglo:** al refrescarse, la página saltaba a otra posición en Safari (iPhone, iPad y Mac). Ahora la vista se mantiene en todos los módulos.
- **Arreglo:** presentación en todas las resoluciones, hasta 320 px: gráficos, tablas, tarjetas de cifras y textos largos se ajustan al ancho de su tarjeta en vez de montarse o salirse.
- **Arreglo:** una petición HEAD o mal formada dejaba un error en el journal y cortaba la conexión. Ahora todos los servicios responden 501.

### App instalada (iPhone, iPad, Android)
- **Nuevo:** si el servidor no responde, muestra «Sin conexión con LabTower» y reintenta solo. Solo con HTTPS; no guarda datos.
- **Nuevo:** deslizar hacia abajo desde arriba recarga la página.
- **Mejora:** la barra de estado sigue el tema elegido en LabTower y la pantalla de arranque es clara u oscura según el tema del equipo.

### Proxmox Monitor
- **Nuevo:** botón ✎ para editar un cluster (nombre, host, puerto, usuario y token) sin reiniciar. El secreto vacío conserva el guardado; si cambian host o puerto hay que confirmar el certificado.
- **Nuevo:** si el certificado del cluster cambió, la página lo explica y ofrece «Volver a fijar certificado», también cuando no hay datos. Mientras no se confirme, no se envía el token.
- **Arreglo:** si una lectura falla, la página muestra el error y la hora de los datos que se ven, en vez de datos viejos sin aviso.
- **Arreglo:** los gráficos del nodo se ordenan en 4, 2 o 1 columna según el ancho, con los encabezados alineados.

### NAS Monitor
- **Nuevo:** vencimiento de los certificados TLS de cada NAS, en los puertos que elijas. Aviso a los 14 días y crítico a los 3, ajustables. Revisión diaria y botón «Revisar ahora».
- **Nuevo:** Resumen: alertas y eventos de certificados de NAS por vencer, vencidos y renovados.

### UPS Monitor
- **Nuevo:** gráfico de autonomía por UPS, en minutos, con la batería y la carga en el detalle. Solo aparece si la UPS informa la autonomía.
- **Mejora:** los servidores NUT con error se muestran sobre la tabla.

### WAN Monitor
- **Nuevo:** en «Calidad y disponibilidad», columnas «Cortes LAN» y «Cortes WAN» junto al total.
- **Seguridad:** fija la huella del certificado del router. Si cambia, la conexión se corta antes de enviar el usuario y la contraseña; guardar los ajustes del router la vuelve a aprender.

### Net Monitor y Switch Monitor
- **Nuevo:** aviso cuando un puerto de un switch queda bajo su velocidad habitual (por ejemplo, de 1G a 100M por un cable o un puerto trabado), en Net Monitor y en el Resumen.
- **Nuevo:** un switch se puede pausar sin borrarlo, útil cuando otra instalación de LabTower ya lo vigila: estos switches admiten una sola sesión.
- **Arreglo:** «SessionExpired» después de iniciar sesión en un switch, por una cookie vieja que se enviaba junto a la nueva.
- **Arreglo:** el punto de Pi-hole quedaba gris aunque estuviera conectado. Ahora muestra el estado real: verde conectado, naranjo con falla, gris sin configurar.
- **Arreglo:** tras una falla, Pi-hole no se volvía a conectar hasta el siguiente escaneo. Ahora se reintenta solo.
- **Mejora:** se muestra el error del último escaneo.

### Código
- **Mejora:** limpieza del código. Errores que antes se perdían ahora quedan en el log, y las lecturas de archivos y comandos capturan solo los errores esperables.

---

## English

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
