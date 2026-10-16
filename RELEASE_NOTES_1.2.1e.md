# Pi Console 1.2.1e

## Español

Auditoría exhaustiva. Sin cambios visibles en la interfaz.

- **XSS desde el servidor NUT (alto):** los valores del UPS y su estado se mostraban sin escapar; como el protocolo NUT no tiene autenticación, un equipo de la LAN podía ejecutar código en el navegador del administrador. Corregido (probado con un upsd falso).
- **Net Monitor:** el nombre de SO y de grupo ya no permite romper atributos HTML.
- **Cambio de contraseña:** corregida una redirección abierta (`next=/%09/sitio`).
- Datos de Proxmox escapados; WOL rechaza caracteres de control en nombre y notas.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1e_all.deb
sha256sum pi-console_1.2.1e_all.deb    # c9534fa7e63efdf610a7f084358a463f0c26933fa61c011e902215e37b2b0ea2
sudo apt-get install -y ./pi-console_1.2.1e_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R.

## English

Exhaustive audit. No visible UI changes.

- **XSS from the NUT server (high):** UPS values and status were rendered unescaped; since the NUT protocol has no authentication, a LAN host could run code in the administrator's browser. Fixed (tested with a fake upsd).
- **Net Monitor:** OS and group names can no longer break out of HTML attributes.
- **Password change:** fixed an open redirect (`next=/%09/site`).
- Proxmox data escaped; WOL rejects control characters in name and notes.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1e_all.deb
sha256sum pi-console_1.2.1e_all.deb    # c9534fa7e63efdf610a7f084358a463f0c26933fa61c011e902215e37b2b0ea2
sudo apt-get install -y ./pi-console_1.2.1e_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R).
