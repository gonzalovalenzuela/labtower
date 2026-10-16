# Pi Console 1.2.1c

## Español

Revisión de seguridad del código. Sin cambios visibles en la interfaz.

- **WOL:** el límite de encendidos por IP se podía evadir falseando `X-Forwarded-For`. Corregido.
- **Net Monitor:** el escaneo de una IP solo acepta equipos de la red escaneada (antes aceptaba cualquier IP, incluida Internet y la propia Pi).
- Validación de host y usuario más estricta; `esc()` de UPS y Proxmox escapa comillas.
- Sin hallazgos en respaldos/restauración, sudoers, SNMP, certificados de Proxmox, cookies, nginx y systemd.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1c_all.deb
sha256sum pi-console_1.2.1c_all.deb    # dc0da6eed13191f33e44c08492734c5ee89cc0faffc26324f0b0fb5aa616b647
sudo apt-get install -y ./pi-console_1.2.1c_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R.

## English

Security review of the code. No visible UI changes.

- **WOL:** the per-IP wake-up limit could be evaded by forging `X-Forwarded-For`. Fixed.
- **Net Monitor:** single-IP scan only accepts hosts of the scanned network (it used to accept any IP, including the Internet and the Pi itself).
- Stricter host and username validation; `esc()` in UPS and Proxmox escapes quotes.
- No findings in backup/restore, sudoers, SNMP, Proxmox certificates, cookies, nginx and systemd.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1c_all.deb
sha256sum pi-console_1.2.1c_all.deb    # dc0da6eed13191f33e44c08492734c5ee89cc0faffc26324f0b0fb5aa616b647
sudo apt-get install -y ./pi-console_1.2.1c_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R).
