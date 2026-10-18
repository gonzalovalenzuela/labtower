# Pi Console 1.2.1i

## Español
- **Tarjeta con los datos de Net Monitor** al pasar el ratón por una IP en UPS Monitor, Proxmox, WOL Console y Overview: estado, tipo, SO, fabricante, MAC, latencia, puertos y última vez visto. *Ver detalle completo* abre Net Monitor con ese equipo expandido (`/net/?ip=…`). Clic directo en la IP en WOL, Proxmox (barra superior) y Overview; en iPad, un toque abre la tarjeta.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1i_all.deb
sha256sum pi-console_1.2.1i_all.deb    # 2a8334f675435a3c1fcab42c01d7d6d4904ef7e141d2bb8b33c699eabfe0b93f
sudo apt-get install -y ./pi-console_1.2.1i_all.deb
```
Recarga con Ctrl+Shift+R.

## English
- **Net Monitor card on hover** over an IP in UPS Monitor, Proxmox, WOL Console and Overview: status, type, OS, vendor, MAC, latency, ports and last seen. *Full details* opens Net Monitor with that device expanded (`/net/?ip=…`). Direct click on the IP in WOL, Proxmox (top bar) and Overview; on iPad a tap opens the card.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1i_all.deb
sha256sum pi-console_1.2.1i_all.deb    # 2a8334f675435a3c1fcab42c01d7d6d4904ef7e141d2bb8b33c699eabfe0b93f
sudo apt-get install -y ./pi-console_1.2.1i_all.deb
```
Hard-reload the browser (Ctrl+Shift+R).
