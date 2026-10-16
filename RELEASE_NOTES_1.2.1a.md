# Pi Console 1.2.1a

## Español

Corrección de seguridad sobre 1.2.1.

- **CSRF:** las peticiones que modifican datos se rechazan (403) si no son del mismo origen. `SameSite=Strict` no frenaba a otra página del mismo host en otro puerto.
- **Escaneo automático** en GitHub: secretos en todo el historial, bandit, shellcheck y Actions al día.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1a/pi-console_1.2.1a_all.deb
sha256sum pi-console_1.2.1a_all.deb    # b093b39f0445f976f023cc89b77aeaec6ca0a9e2081a2340019488b0b44df92f
sudo apt-get install -y ./pi-console_1.2.1a_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R. Detalle en [CHANGELOG.md](https://github.com/gonzalovalenzuela/pi-console/blob/main/CHANGELOG.md).

## English

Security fix on top of 1.2.1.

- **CSRF:** requests that change data are rejected (403) unless same-origin. `SameSite=Strict` did not stop another page on the same host and a different port.
- **Automatic scanning** on GitHub: secrets across the whole history, bandit, shellcheck and up-to-date Actions.

**Install or upgrade**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1a/pi-console_1.2.1a_all.deb
sha256sum pi-console_1.2.1a_all.deb    # b093b39f0445f976f023cc89b77aeaec6ca0a9e2081a2340019488b0b44df92f
sudo apt-get install -y ./pi-console_1.2.1a_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R). Details in [CHANGELOG.md](https://github.com/gonzalovalenzuela/pi-console/blob/main/CHANGELOG.md).
