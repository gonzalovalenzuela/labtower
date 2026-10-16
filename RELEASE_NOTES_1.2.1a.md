# Pi Console 1.2.1a

## Español

Seguridad sobre 1.2.1. No hay cambios visibles en la interfaz.

- **CSRF:** las peticiones que modifican datos se rechazan (403) si no vienen de la propia página. Antes, otra página del mismo host en otro puerto podía crear o borrar datos con tu sesión.
- **Escaneo automático** en GitHub: claves y secretos en todo el historial, análisis de Python (bandit), shellcheck y Actions al día.
- Cuatro falsos positivos del escáner quedaron marcados en el código. Sin cambio de funcionamiento.

**Qué notarás:** nada. curl y los scripts siguen funcionando; solo se bloquean las escrituras que un navegador marca como ajenas.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1a/pi-console_1.2.1a_all.deb
sha256sum pi-console_1.2.1a_all.deb    # b093b39f0445f976f023cc89b77aeaec6ca0a9e2081a2340019488b0b44df92f
sudo apt-get install -y ./pi-console_1.2.1a_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R. Detalle en [CHANGELOG.md](https://github.com/gonzalovalenzuela/pi-console/blob/main/CHANGELOG.md).

## English

Security update on top of 1.2.1. No visible UI changes.

- **CSRF:** requests that change data are rejected (403) unless they come from the page itself. Before, another page on the same host and a different port could create or delete data with your session.
- **Automatic scanning** on GitHub: keys and secrets across the whole history, Python analysis (bandit), shellcheck and up-to-date Actions.
- Four scanner false positives are now marked in the code. No behaviour change.

**What you will notice:** nothing. curl and scripts keep working; only writes that a browser flags as foreign are blocked.

**Install or upgrade**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.2.1a/pi-console_1.2.1a_all.deb
sha256sum pi-console_1.2.1a_all.deb    # b093b39f0445f976f023cc89b77aeaec6ca0a9e2081a2340019488b0b44df92f
sudo apt-get install -y ./pi-console_1.2.1a_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R). Details in [CHANGELOG.md](https://github.com/gonzalovalenzuela/pi-console/blob/main/CHANGELOG.md).
