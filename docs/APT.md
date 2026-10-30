# Repositorio APT de LabTower / LabTower APT repository

> **Estado: preparado, sin publicar.** / **Status: ready, not published yet.** Hoy se instala con el `.deb` (ver README). / Today, install with the `.deb` (see README).

Permite instalar y actualizar LabTower con `apt` en el servidor, sin descargar el `.deb` a mano.
Se publica en GitHub Pages (rama `gh-pages`) y está firmado con una clave GPG tuya.
/ Install and upgrade LabTower with `apt` on the server. Hosted on GitHub Pages (`gh-pages` branch) and signed with your own GPG key.

## Uso en el servidor / On the server

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/labtower.asc https://gonzalovalenzuela.github.io/labtower/labtower.asc
echo "deb [signed-by=/etc/apt/keyrings/labtower.asc] https://gonzalovalenzuela.github.io/labtower stable main" | sudo tee /etc/apt/sources.list.d/labtower.list
sudo apt update && sudo apt install labtower
```

Las actualizaciones llegan con `sudo apt update && sudo apt upgrade`. Si ya tienes LabTower instalado con `dpkg -i`, `apt` lo reconoce y lo actualiza igual; los datos no se tocan.

## Configuración inicial (una sola vez, en el Mac) / One-time setup (on the Mac)

1. **Crear la clave** (`brew install gnupg` si falta). Pide una frase de contraseña; guárdala.
   ```bash
   gpg --quick-generate-key "LabTower APT <tu-correo>" ed25519 sign 5y
   gpg --list-secret-keys --keyid-format long      # anota la huella (fingerprint) de 40 caracteres
   gpg --armor --export-secret-keys <HUELLA> > ~/labtower-apt-private.asc   # copia de seguridad: NO va al repo
   ```
2. **Crear la rama `gh-pages`** en un clon aparte (queda sin historial del código):
   ```bash
   cd <carpeta-de-trabajo>
   git clone git@github.com:gonzalovalenzuela/labtower.git labtower-pages
   cd labtower-pages && git checkout --orphan gh-pages && git rm -rf . && git commit --allow-empty -m "gh-pages" && cd ..
   ```
3. En GitHub: *Settings → Pages → Build and deployment → Deploy from a branch → `gh-pages` / `(root)`*.

## Publicar una versión / Publishing a release

```bash
cd <carpeta-del-repo>
python3 scripts/apt-repo.py --repo ../labtower-pages --key <HUELLA> add /ruta/a/labtower_1.2.0_all.deb
cd ../labtower-pages && git add -A && git commit -m "labtower 1.2.0" && git push -u origin gh-pages
```

- Sin dependencias (solo Python 3 y `gpg`). En macOS no hay `dpkg-deb`: los datos del paquete se leen de `debian/control` del repo, y la versión debe coincidir con el nombre del `.deb` (si no, el script se detiene).
- Las versiones anteriores se conservan en `pool/`; para retirar una, bórrala de `pool/main/p/labtower/` y ejecuta `... --key <HUELLA> rebuild`.
- El script genera `dists/stable/{InRelease,Release,Release.gpg}`, los `Packages` para amd64/arm64/armhf (el paquete es `all`), `labtower.asc` (clave pública) y una página `index.html` con las instrucciones.
- Probado con `apt` real: `update`, `policy` y `download` verifican la firma y los hashes; un `.deb` alterado es rechazado.
