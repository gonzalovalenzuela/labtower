# Pi Console 1.2.1t

## Español
- **Seguridad:** revisión completa del código. Corregido: archivo de estado del respaldo SFTP escrito como root en carpeta del servicio (ahora `/var/log/pi-console/`), tope de 2 GiB descomprimidos en Teleporter, subidas simultáneas, límite de frecuencia en «Despertar todos». Sin hallazgos críticos.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1t_all.deb
sha256sum pi-console_1.2.1t_all.deb    # 5b6d7256f0f5a77a3db2d947770ff6e556a74b7e05ec42898d8efd333386c114
sudo apt-get install -y ./pi-console_1.2.1t_all.deb
```

## English
- **Security:** full code review. Fixed: SFTP backup status file written as root inside a service-owned folder (now `/var/log/pi-console/`), 2 GiB uncompressed cap in Teleporter, simultaneous uploads, rate limit on "Wake all". No critical findings.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1t_all.deb
sha256sum pi-console_1.2.1t_all.deb    # 5b6d7256f0f5a77a3db2d947770ff6e556a74b7e05ec42898d8efd333386c114
sudo apt-get install -y ./pi-console_1.2.1t_all.deb
```
