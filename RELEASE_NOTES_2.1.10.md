### Pausar equipos
- **Nuevo:** botón ⏸ / ▶ para pausar sin borrar un NAS, un servidor UPS (NUT), un cluster de Proxmox, un servidor DNS, una VPN, un monitor de Uptime, un switch o un punto de acceso. Solo administradores.
- **Nuevo:** un equipo pausado no se consulta ni avisa y no cuenta en las cifras ni en el Resumen. Aparece como «Pausado». Si todos los equipos de un módulo están en pausa, el Resumen dice «Todos en pausa (N)».
- **Nuevo:** al reanudar se lee de inmediato. En Proxmox eso incluye SMART, respaldos y red de invitados.
- **Nuevo:** pausar no cambia la configuración, las claves ni el certificado fijado. Editar un equipo pausado lo deja pausado.
- **Nuevo:** en DNS el botón dice «Pausar monitoreo» y el bloqueo de anuncios del servidor sigue igual. En Uptime se conserva el historial.
- **Nuevo:** en UPS Monitor, pausar un servidor NUT con un UPS en batería cierra el corte en ese momento.
- **Nuevo:** los switches tienen el botón en su tarjeta, además de la casilla en «Editar».

### Todos los módulos
- **Arreglo:** el aviso «Atención» seguía visible después de resolverse el problema, hasta un minuto o más en Safari. Ahora se actualiza cuando la página muestra datos nuevos y al volver a la pestaña.

### App instalada (iPhone, iPad, Android)
- **Arreglo:** al deslizar hacia abajo para recargar, el ícono a veces quedaba girando y la página no se recargaba. Ahora se recarga cuando termina el rebote y, si no lo logra, reintenta a los 4 s. A los 10 s el ícono se esconde para poder deslizar de nuevo. Además, solo gira la flecha.

### Net Monitor
- **Cambio:** la MAC de cada equipo sale primero de la tabla ARP del servidor. Pi-hole y SNMP quedan de respaldo. Al actualizar, el primer escaneo no avisa «MAC cambió» por este cambio.
- **Arreglo:** «MAC cambió» ya no avisa por una MAC que esa IP ya tuvo (equipos con dos tarjetas en la misma red).
- **Nuevo:** al tocar la etiqueta «MAC cambió» se ven la MAC anterior y la actual (también en iPhone). Un administrador puede marcarlo como revisado para quitar el aviso.
- **Arreglo:** la tabla de hosts ya no pestañea con cada refresco.

### AP Monitor (nueva pestaña de Net Monitor)
- **Nuevo:** muestra los puntos de acceso Wi-Fi: estado, uptime, modelo, firmware, radios (canal, ancho, potencia, uso del canal), SSID y clientes conectados con su señal. Los clientes se cruzan con los equipos conocidos.
- **Nuevo:** OpenWrt por ubus, directo o el de LuCI (OpenWrt 19.07 y posteriores).
- **Nuevo:** MitraStar Smart WiFi de Movistar: por sesión web (modelo, firmware, SSID y canales; el equipo no informa clientes) o solo ping. Cierra la sesión después de cada lectura. Si falla, el error distingue clave incorrecta de sesión ocupada por otro navegador.
- **Nuevo:** HPE Aruba Instant On: por el portal en la nube (API no oficial, cuenta sin 2FA) o solo ping. Una cuenta trae todos los AP del sitio, con sus clientes conectados.
- **Nuevo:** aviso cuando un AP se cae y cuando vuelve. El número de serie solo con el permiso «Ver números de serie».
- **Nuevo:** `aps.json` (permisos 600) entra en el Teleporter y en la copia previa a actualizar o desinstalar.

### Switch Monitor
- **Nuevo:** en un puerto con velocidad baja, «Revisado: solo este aviso» quita el aviso hasta que el puerto vuelva a su velocidad habitual. Sirve para equipos apagados que quedan a 10 Mb/s esperando WOL.
- **Nuevo:** «Silenciar todos los avisos del puerto» y la casilla «Sin avisos en este puerto (pruebas)» quitan los avisos de velocidad, enlace, rebotes, errores y loop hasta desmarcarla. Esos puertos no cuentan en «Puertos con errores nuevos».
- **Arreglo:** si el switch rechaza la sesión, la siguiente lectura empieza con una conexión nueva. Antes podía quedar «Sin conexión» hasta reiniciar el servicio.
- **Nuevo:** cuando un switch rechaza la sesión, el log del servicio anota qué petición falló, cuánto después de entrar y si otro inicio de sesión de LabTower le quitó la sesión. No registra contraseñas ni cookies.
- **Arreglo:** las tablas ya no pestañean con cada refresco.

### UPS Monitor
- **Arreglo:** la tabla de UPS ya no pestañea con cada refresco.

### WAN Monitor
- **Nuevo:** la tarjeta Conexión muestra cuánto lleva encendido el router, en Huawei, OpenWrt y DD-WRT. En OpenWrt el usuario necesita acceso a `system info`.
- **Arreglo:** si el router enviaba un tiempo inválido, se perdía toda su lectura. Ahora ese dato queda vacío y el resto del chequeo sigue.
- **Arreglo:** si el router responde algo que no es HTTP, se informa como falta de conexión con el router y el chequeo no se rompe.

### Proxmox Monitor
- **Arreglo:** el aviso al eliminar un cluster sigue el idioma elegido y avisa si falla.

### DNS Monitor
- **Arreglo:** un servidor sin lectura muestra «—» en la tabla en vez de «undefined%».

### VPN Monitor
- **Arreglo:** el detalle de un servidor que nunca respondió ahora muestra Editar y Eliminar.

### WoL Console
- **Arreglo:** la tabla de equipos ya no pestañea con el refresco cada 5 segundos.
- **Arreglo:** «Sesión activa» cuenta desde el inicio de sesión. Antes volvía a cero al cambiar de módulo.
- **Cambio:** «Wakes enviados» pasa a «Wakes de hoy»: los de hoy de todos los usuarios, desde el registro del servidor. «Último wake» también. Ya no vuelven a cero al cambiar de módulo.

### Instalación
- **Arreglo:** `/var/backups/labtower` crecía sin límite: cada instalación o actualización guardaba una copia de cada archivo de datos y nada borraba las viejas. Ahora se conservan las 5 más nuevas de cada archivo y, de `history.db`, también la más grande. La primera instalación de esta versión limpia las que ya había.
- **Arreglo:** al actualizar se hacían dos copias de todo. Ahora la segunda, la de `prerm`, se hace solo al desinstalar.

### Teleporter
- **Cambio:** se conservan las 5 copias previas a restaurar (`pre-restore-*.tar.gz`) más nuevas.

## English

### Pausing devices
- **New:** ⏸ / ▶ button to pause, without deleting, a NAS, a UPS (NUT) server, a Proxmox cluster, a DNS server, a VPN, an Uptime monitor, a switch or an access point. Administrators only.
- **New:** a paused device is not polled or alerted on and does not count in the figures or the Overview. It shows as "Paused". If every device of a module is paused, the Overview says "All paused (N)".
- **New:** resuming reads it at once. In Proxmox that includes SMART, backups and guest networking.
- **New:** pausing does not change the configuration, the keys or the pinned certificate. Editing a paused device keeps it paused.
- **New:** in DNS the button says "Pause monitoring" and the server's ad blocking is not affected. In Uptime the history is kept.
- **New:** in UPS Monitor, pausing a NUT server with a UPS on battery ends the outage at that moment.
- **New:** switches have the button on their card, besides the checkbox in "Edit".

### All modules
- **Fix:** the "Attention" notice stayed visible after the problem was solved, for a minute or more in Safari. It now updates when the page shows new data and when you return to the tab.

### Installed app (iPhone, iPad, Android)
- **Fix:** when pulling down to reload, the icon sometimes kept spinning and the page did not reload. It now reloads when the bounce ends and, if that fails, retries after 4 s. After 10 s the icon hides so you can pull again. Also, only the arrow spins now.

### Net Monitor
- **Change:** each device's MAC now comes first from the server's ARP table. Pi-hole and SNMP stay as fallbacks. After upgrading, the first scan does not warn "MAC changed" because of this.
- **Fix:** "MAC changed" no longer warns about a MAC that IP already had (devices with two network cards on the same network).
- **New:** tapping the "MAC changed" label shows the previous and the current MAC (also on iPhone). An administrator can mark it as reviewed to clear the warning.
- **Fix:** the hosts table no longer flickers on every refresh.

### AP Monitor (new Net Monitor tab)
- **New:** shows Wi-Fi access points: status, uptime, model, firmware, radios (channel, width, power, channel use), SSIDs and connected clients with their signal. Clients are matched to known devices.
- **New:** OpenWrt over ubus, direct or through LuCI (OpenWrt 19.07 and later).
- **New:** Movistar's MitraStar Smart WiFi: through a web session (model, firmware, SSIDs and channels; the unit does not report clients) or ping only. It logs out after each read. If it fails, the error tells a wrong password apart from a session held by another browser.
- **New:** HPE Aruba Instant On: through the cloud portal (unofficial API, account without 2FA) or ping only. One account brings every AP of the site, with its connected clients.
- **New:** alert when an AP goes down and when it comes back. The serial number only with the "See serial numbers" permission.
- **New:** `aps.json` (permissions 600) is included in the Teleporter and in the copy made before upgrading or uninstalling.

### Switch Monitor
- **New:** on a port below its usual speed, "Reviewed: this alert only" clears the alert until the port is back at its usual speed. Useful for powered-off devices that drop to 10 Mb/s waiting for WOL.
- **New:** "Silence every alert of this port" and the "No alerts on this port (testing)" checkbox remove the speed, link, flapping, error and loop alerts until unticked. Those ports do not count in "Ports with new errors".
- **Fix:** if the switch rejects the session, the next read starts with a new connection. Before, it could stay "Unreachable" until the service was restarted.
- **New:** when a switch rejects the session, the service log records which request failed, how long after logging in, and whether another LabTower login took the session. No passwords or cookies are logged.
- **Fix:** the tables no longer flicker on every refresh.

### UPS Monitor
- **Fix:** the UPS table no longer flickers on every refresh.

### WAN Monitor
- **New:** the Connection card shows how long the router has been on, for Huawei, OpenWrt and DD-WRT. On OpenWrt the user needs access to `system info`.
- **Fix:** if the router sent an invalid time, its whole reading was lost. Now that value is left empty and the rest of the check goes on.
- **Fix:** if the router answers something that is not HTTP, it is reported as no connection to the router and the check does not break.

### Proxmox Monitor
- **Fix:** the notice when deleting a cluster follows the chosen language and warns if it fails.

### DNS Monitor
- **Fix:** a server without a reading shows "—" in the table instead of "undefined%".

### VPN Monitor
- **Fix:** the detail of a server that never answered now shows Edit and Delete.

### WoL Console
- **Fix:** the device table no longer flickers with the 5-second refresh.
- **Fix:** "Active session" counts from login. Before, it reset to zero when switching modules.
- **Change:** "Wakes sent" becomes "Wakes today": today's wakes from every user, from the server log. "Last wake" too. They no longer reset to zero when switching modules.

### Installation
- **Fix:** `/var/backups/labtower` grew without limit: every install or upgrade saved a copy of each data file and nothing removed the old ones. Now the 5 newest of each file are kept and, for `history.db`, also the largest. The first install of this version cleans up the existing ones.
- **Fix:** upgrading made two copies of everything. Now the second one, from `prerm`, is made only when uninstalling.

### Teleporter
- **Change:** the 5 newest pre-restore copies (`pre-restore-*.tar.gz`) are kept.
