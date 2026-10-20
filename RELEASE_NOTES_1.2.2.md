# Pi Console 1.2.2

## Español
- **Seguridad:** revisión completa del código. Corregido: archivo de estado del respaldo SFTP escrito como root en carpeta del servicio (ahora `/var/log/pi-console/`), tope de 2 GiB descomprimidos en Teleporter, subidas simultáneas, límite de frecuencia en «Despertar todos». Sin hallazgos críticos.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.2_all.deb
sha256sum pi-console_1.2.2_all.deb    # 4ad59661320cf5540ac4a250454af820eb92fbbdecea23b92efded7568d416db
sudo apt-get install -y ./pi-console_1.2.2_all.deb
```

## English
- **Security:** full code review. Fixed: SFTP backup status file written as root inside a service-owned folder (now `/var/log/pi-console/`), 2 GiB uncompressed cap in Teleporter, simultaneous uploads, rate limit on "Wake all". No critical findings.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.2_all.deb
sha256sum pi-console_1.2.2_all.deb    # 4ad59661320cf5540ac4a250454af820eb92fbbdecea23b92efded7568d416db
sudo apt-get install -y ./pi-console_1.2.2_all.deb
```
