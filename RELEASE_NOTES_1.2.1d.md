# Pi Console 1.2.1d

## Español

Endurecimiento tras la auditoría. Sin cambios visibles en la interfaz.

- **XSS almacenado corregido:** un nombre de servidor UPS o clúster con comillas podía ejecutar código en el navegador de otro administrador. Corregido en los 5 paneles.
- La contraseña inicial del admin ya no se escribe en el journal.
- Usuarios con hash antiguo: se migra a scrypt y se exige nueva contraseña.
- Errores capturados solo por tipo (sin `except:` genérico).
- El instalador recomienda activar HTTPS.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1d_all.deb
sha256sum pi-console_1.2.1d_all.deb    # 1a17d70df0ddfd560768710fe166f3ff728c3e220c329e9c3796d5c6105cee77
sudo apt-get install -y ./pi-console_1.2.1d_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R.

## English

Hardening after the audit. No visible UI changes.

- **Stored XSS fixed:** a UPS server or cluster name with quotes could run code in another administrator's browser. Fixed in the 5 panels.
- The initial admin password is no longer written to the journal.
- Users with the old hash: migrated to scrypt and asked for a new password.
- Errors caught by type only (no bare `except:`).
- The installer recommends enabling HTTPS.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1d_all.deb
sha256sum pi-console_1.2.1d_all.deb    # 1a17d70df0ddfd560768710fe166f3ff728c3e220c329e9c3796d5c6105cee77
sudo apt-get install -y ./pi-console_1.2.1d_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R).
