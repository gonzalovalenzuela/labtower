# Pi Console 1.2.2

## Español
Reúne todos los cambios desde 1.2.1 (builds 1.2.1a a 1.2.1t).

**Seguridad**
- CSRF: las peticiones que modifican datos se rechazan si no vienen de la propia página.
- CSP estricta: sin scripts ni manejadores en línea (`script-src 'self'`). Navegadores: Chrome 75+, Firefox 105+, Safari 15.4+.
- XSS corregido en los 5 paneles. Incluye el que venía del servidor NUT (un equipo de la red podía ejecutar código en el navegador del administrador).
- WOL: el límite por IP ya no se evade con `X-Forwarded-For`. "Despertar todos" también tiene límite.
- Net Monitor: el escaneo de una IP solo acepta equipos de la red escaneada.
- Redirección abierta en el cambio de contraseña corregida.
- La contraseña inicial del admin ya no se escribe en el journal. Los hashes antiguos se migran a scrypt.
- Respaldo SFTP: el archivo de estado ahora está en `/var/log/pi-console/backup.status` (carpeta de root).
- Teleporter: se rechazan respaldos que descomprimen a más de 2 GiB. Dos subidas simultáneas ya no se pisan.
- Revisión final del código con bandit y shellcheck. Sin hallazgos críticos ni altos.

**Nuevo**
- Login: "Recordarme" (1 día, 1 semana, 1 mes o siempre). Sin marcar, 24 h.
- Admin: tarjeta "Sesiones activas" para ver y cerrar sesiones.
- Overview: selector de intervalo de actualización (10 s a 5 min, o manual).
- Net Monitor: botón de basurero para eliminar equipos. Categorías nuevas: Game Console, Servidor, Teléfono IP, UPS y Altavoz inteligente.
- Tarjeta de Net Monitor al pasar el mouse (o tocar en iPad) por una IP en UPS, Proxmox, WOL y Overview.
- Nuevo icono de la app y soporte para pantalla de inicio en iPad/iPhone (pantalla completa, icono incrustado).
- HTTPS autofirmado compatible con iOS. `pi-console-https enable` regenera el certificado antiguo una vez; hay que instalarlo de nuevo en cada dispositivo.

**Correcciones**
- Admin: el login con Enter abría dos sesiones.
- UPS Monitor: anillos y etiquetas de los gráficos ya no se cortan.
- Las duraciones de más de 24 h se ven en días (`1d 16h`).

**Al actualizar:** `pi-console-site.conf` cambió. Si lo editaste, dpkg preguntará; conserva el nuevo. Si ya tenías la app en la pantalla de inicio, quítala y agrégala otra vez.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.2/pi-console_1.2.2_all.deb
sha256sum pi-console_1.2.2_all.deb    # 052118769a143c9bd0017f3f4a48bd0508f92d2151bc45b399565c8febf1991a
sudo apt-get install -y ./pi-console_1.2.2_all.deb
```

## English
Includes every change since 1.2.1 (builds 1.2.1a to 1.2.1t).

**Security**
- CSRF: requests that change data are rejected unless they come from the app's own page.
- Strict CSP: no inline scripts or handlers (`script-src 'self'`). Browsers: Chrome 75+, Firefox 105+, Safari 15.4+.
- XSS fixed in all 5 panels, including one coming from the NUT server (a device on the network could run code in the admin's browser).
- WOL: the per-IP limit can no longer be bypassed with `X-Forwarded-For`. "Wake all" is rate limited too.
- Net Monitor: scanning a single IP only accepts hosts in the scanned network.
- Open redirect in the password change page fixed.
- The initial admin password is no longer written to the journal. Old hashes are migrated to scrypt.
- SFTP backup: the status file moved to `/var/log/pi-console/backup.status` (root-owned folder).
- Teleporter: backups that expand to more than 2 GiB are rejected. Simultaneous uploads no longer overwrite each other.
- Final code review with bandit and shellcheck. No critical or high findings.

**New**
- Login: "Remember me" (1 day, 1 week, 1 month or forever). Unchecked, 24 h.
- Admin: "Active sessions" card to view and close sessions.
- Overview: refresh interval selector (10 s to 5 min, or manual).
- Net Monitor: trash button to remove hosts. New categories: Game Console, Server, IP Phone, UPS and Smart Speaker.
- Net Monitor card on hover (or tap on iPad) over an IP in UPS, Proxmox, WOL and Overview.
- New app icon and iPad/iPhone home screen support (full screen, embedded icon).
- Self-signed HTTPS compatible with iOS. `pi-console-https enable` regenerates the old certificate once; install it again on each device.

**Fixes**
- Admin: login with Enter opened two sessions.
- UPS Monitor: rings and chart labels are no longer cut off.
- Durations over 24 h show in days (`1d 16h`).

**When upgrading:** `pi-console-site.conf` changed. If you edited it, dpkg will ask; keep the new one. If the app was already on your home screen, remove it and add it again.

**Install or upgrade**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.2/pi-console_1.2.2_all.deb
sha256sum pi-console_1.2.2_all.deb    # 052118769a143c9bd0017f3f4a48bd0508f92d2151bc45b399565c8febf1991a
sudo apt-get install -y ./pi-console_1.2.2_all.deb
```
