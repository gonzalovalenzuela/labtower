# Pi Console 1.2.1g

## Español

- **iPad / app web:** manifest e iconos; con *Añadir a pantalla de inicio* se abre a pantalla completa, sin barra de Safari ni botón X. Sin zoom al tocar campos ni rebote al desplazar. Si ya tenías un acceso directo, bórralo y créalo otra vez.
- **Net Monitor:** nueva categoría **Game Console** con detección automática (Nintendo, PlayStation, Xbox, Steam Deck, Quest) y 4 más para reducir los *Other*: Servidor, Teléfono IP, UPS y Altavoz inteligente. Overview las muestra también.
- Cambia `pi-console-site.conf`: si lo editaste, dpkg preguntará; conserva el nuevo.

**Instalar o actualizar**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1g_all.deb
sha256sum pi-console_1.2.1g_all.deb    # e5f0507e4de59043c1eefd0b04db16a8df3caf7e2b5fa2663a9d833ab1f358be
sudo apt-get install -y ./pi-console_1.2.1g_all.deb
```
Los datos se conservan. Recarga el navegador con Ctrl+Shift+R.

## English

- **iPad / web app:** manifest and icons; with *Add to Home Screen* it opens full screen, with no Safari bar or X button. No zoom on field focus, no rubber-band scrolling. If you already had a shortcut, delete it and add it again.
- **Net Monitor:** new **Game Console** category with automatic detection (Nintendo, PlayStation, Xbox, Steam Deck, Quest) plus 4 more to cut down *Other*: Server, IP Phone, UPS and Smart Speaker. Overview shows them too.
- `pi-console-site.conf` changed: if you edited it, dpkg will ask; keep the new one.

**Install or upgrade**
```bash
wget https://raw.githubusercontent.com/gonzalovalenzuela/pi-console/deb-builds/pi-console_1.2.1g_all.deb
sha256sum pi-console_1.2.1g_all.deb    # e5f0507e4de59043c1eefd0b04db16a8df3caf7e2b5fa2663a9d833ab1f358be
sudo apt-get install -y ./pi-console_1.2.1g_all.deb
```
Data is kept. Hard-reload the browser (Ctrl+Shift+R).
