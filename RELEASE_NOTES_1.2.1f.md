# Pi Console 1.2.1f

## Español

CSP estricta. Sin cambios visibles en la interfaz.

- Las páginas ya no llevan scripts, manejadores `on…=` ni `<style>` en línea; nginx usa `script-src 'self'` (sin `'unsafe-inline'`). Aunque se colara HTML inyectado, el navegador no ejecutaría su script.
- Los atributos `style="…"` siguen permitidos (`style-src-attr`).
- Probado en Chromium con la CSP real: 0 errores de JS y 0 violaciones; comportamiento idéntico al anterior.
- Navegadores: Chrome 75+, Firefox 105+, Safari 15.4+.
- `pi-console-site.conf` cambia: si lo editaste, dpkg preguntará; conserva el nuevo.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1f_all.deb
sha256sum pi-console_1.2.1f_all.deb    # bf49570f520d7a8ea596ee16319725ce990ed1f849e07083e3af58da93f12395
sudo apt-get install -y ./pi-console_1.2.1f_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R.

## English

Strict CSP. No visible UI changes.

- Pages no longer carry inline scripts, `on…=` handlers or `<style>` blocks; nginx uses `script-src 'self'` (no `'unsafe-inline'`). Even if injected HTML slipped in, the browser would not run its script.
- `style="…"` attributes are still allowed (`style-src-attr`).
- Tested in Chromium with the real CSP: 0 JS errors, 0 violations; behaviour identical to before.
- Browsers: Chrome 75+, Firefox 105+, Safari 15.4+.
- `pi-console-site.conf` changed: if you edited it, dpkg will ask; keep the new one.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1f_all.deb
sha256sum pi-console_1.2.1f_all.deb    # bf49570f520d7a8ea596ee16319725ce990ed1f849e07083e3af58da93f12395
sudo apt-get install -y ./pi-console_1.2.1f_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R).
