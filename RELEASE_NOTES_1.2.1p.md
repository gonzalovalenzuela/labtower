# Pi Console 1.2.1p

## Español
- **HTTPS autofirmado compatible con iPad/iPhone:** el certificado ahora incluye `serverAuth`, que iOS exige. `pi-console-https enable` regenera el certificado antiguo una vez; vuelve a instalarlo y confiar en él en cada dispositivo.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1p_all.deb
sha256sum pi-console_1.2.1p_all.deb    # a40b9d4bd888a5e65746604665b633a1d535d1f352d8e40585247ee68721f343
sudo apt-get install -y ./pi-console_1.2.1p_all.deb
sudo pi-console-https enable --redirect --name TU-NOMBRE-O-IP
```

## English
- **Self-signed HTTPS that iPad/iPhone accept:** the certificate now carries `serverAuth`, which iOS requires. `pi-console-https enable` regenerates the old certificate once; reinstall and trust it on each device.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1p_all.deb
sha256sum pi-console_1.2.1p_all.deb    # a40b9d4bd888a5e65746604665b633a1d535d1f352d8e40585247ee68721f343
sudo apt-get install -y ./pi-console_1.2.1p_all.deb
sudo pi-console-https enable --redirect --name YOUR-NAME-OR-IP
```
