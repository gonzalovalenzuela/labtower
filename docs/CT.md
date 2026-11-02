# LabTower en un contenedor (CT) de Proxmox / LabTower in a Proxmox container (CT)

## Español

LabTower corre como paquete `.deb` sobre Debian 12 con systemd. En Proxmox lo más simple es un **CT sin privilegios** (LXC) con Debian 12: es liviano y no necesita cambios en LabTower. No hay imagen de Docker.

### Opción 1: con el script (recomendada)

En un nodo de Proxmox, como `root`:

```
wget https://raw.githubusercontent.com/gonzalovalenzuela/labtower/main/scripts/labtower-ct
chmod +x labtower-ct
./labtower-ct --ip 192.0.2.50/24 --gw 192.0.2.1
```

El script baja la plantilla de Debian 12, crea el CT (2 núcleos, 1 GB de RAM, 8 GB de disco, arranque automático), instala LabTower dentro y al final muestra la URL, el usuario `admin` y la contraseña inicial (hay que cambiarla en el primer ingreso).

Opciones (todas opcionales):

| Opción | Por defecto | Para qué |
|---|---|---|
| `--id N` | el siguiente libre | número del CT |
| `--hostname NOMBRE` | `labtower` | nombre del CT |
| `--storage ST` | `local-lvm` | storage del disco del CT |
| `--template-storage ST` | `local` | storage donde se guarda la plantilla |
| `--bridge BR` | `vmbr0` | bridge de red (el de tu LAN) |
| `--vlan N` | ninguna | etiqueta de VLAN |
| `--ip dhcp` o `CIDR` | `dhcp` | IP del CT, por ejemplo `192.0.2.50/24` |
| `--gw IP` / `--dns IP` | del DHCP | puerta de enlace y DNS si usas IP fija |
| `--memory MB` / `--cores N` / `--disk GB` | 1024 / 2 / 8 | recursos |
| `--version X.Y.Z` | última publicada | instala esa compilación de la rama `deb-builds` |
| `--url URL` | | instala un `.deb` desde una dirección https |
| `--dry-run` | | solo muestra los comandos, sin ejecutar nada |

Prueba primero con `--dry-run` para ver lo que hará.

### Opción 2: desde la interfaz de Proxmox

1. *Create CT*: plantilla **debian-12-standard**, *Unprivileged container* activado, 1 GB de RAM, 2 núcleos, 8 GB de disco. En *Network* usa el bridge de tu LAN (IP fija o DHCP).
2. En *Options → Features* activa **Nesting**. En *Options* activa *Start at boot*.
3. Inicia el CT, abre su consola y descarga el `.deb` de la última versión (el enlace está en la página de *Releases* de GitHub):

```
apt update && apt install -y wget
wget https://github.com/gonzalovalenzuela/labtower/releases/download/X.Y.Z/labtower_X.Y.Z_all.deb
apt install ./labtower_X.Y.Z_all.deb
```

4. Abre `http://IP-DEL-CT/`. El usuario es `admin`; la contraseña inicial sale al final de la instalación.

### Después de instalar
- **HTTPS:** `pct exec ID -- /usr/local/bin/labtower-https enable --redirect` (con la ruta completa, porque `pct exec` no incluye `/usr/local/bin` en el PATH).
- **Actualizar:** dentro del CT, `apt install ./labtower_NUEVA_all.deb` con el `.deb` nuevo.
- **Respaldo:** usa los respaldos de Proxmox (vzdump) del CT además del Teleporter de LabTower.
- **Ping:** en un CT sin privilegios los servicios no pueden hacer ping (Net Monitor y WAN Monitor) hasta que el grupo `labtower` entre en `net.ipv4.ping_group_range`. El script lo configura solo (`/etc/sysctl.d/99-labtower-ping.conf` dentro del CT); si creas el CT desde la interfaz, ejecuta en el nodo: `pct exec ID -- sh -c 'echo "net.ipv4.ping_group_range = 0 65534" > /etc/sysctl.d/99-labtower-ping.conf && sysctl -q -p /etc/sysctl.d/99-labtower-ping.conf'`.
- **Net Monitor:** el CT debe estar en el mismo bridge que tu LAN para ver las MAC de los equipos. Si el ping falla, revisa el firewall del CT y del bridge.
- **UPS Monitor:** LabTower se conecta a tu servidor NUT por la red; no necesita acceso USB al CT.

### Pruebas de velocidad (opcional)
WAN Monitor trae su motor propio y funciona sin instalar nada. Para usar **Ookla** o **LibreSpeed**, instala el programa **dentro del CT** (`pct enter ID`), no en el nodo de Proxmox: el script de Ookla no reconoce la versión de Debian del nodo.

Ookla (`speedtest`), dentro del CT:
```
apt-get install -y curl
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash
apt-get install -y speedtest
speedtest --version
```
Si el script no reconoce el sistema, instala el binario:
```
apt-get install -y wget
wget https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz
tar -xzf ookla-speedtest-1.2.0-linux-x86_64.tgz speedtest
install -m 755 speedtest /usr/local/bin/speedtest
```
LibreSpeed (`librespeed-cli`), dentro del CT (en Debian 12 no hay paquete; usa `arm64` en vez de `amd64` si `uname -m` dice `aarch64`):
```
wget https://github.com/librespeed/speedtest-cli/releases/download/v1.0.14/librespeed-cli_1.0.14_linux_amd64.tar.gz
tar -xzf librespeed-cli_1.0.14_linux_amd64.tar.gz librespeed-cli
install -m 755 librespeed-cli /usr/local/bin/librespeed-cli
```
Después elige el motor en **WAN Monitor → Ajustes → Motor de la prueba** (si sigue como «no instalado», `systemctl restart wan-monitor` dentro del CT). La primera vez, Ookla pide aceptar la licencia: `speedtest --accept-license --accept-gdpr`.

## English

LabTower runs as a `.deb` package on Debian 12 with systemd. On Proxmox the simplest way is an **unprivileged CT** (LXC) with Debian 12: it is light and needs no changes in LabTower. There is no Docker image.

### Option 1: with the script (recommended)

On a Proxmox node, as `root`:

```
wget https://raw.githubusercontent.com/gonzalovalenzuela/labtower/main/scripts/labtower-ct
chmod +x labtower-ct
./labtower-ct --ip 192.0.2.50/24 --gw 192.0.2.1
```

The script downloads the Debian 12 template, creates the CT (2 cores, 1 GB RAM, 8 GB disk, start at boot), installs LabTower inside and finally prints the URL, the `admin` user and the initial password (change it at the first login). Run `./labtower-ct --help` for the options (`--id`, `--hostname`, `--storage`, `--bridge`, `--vlan`, `--ip`, `--gw`, `--dns`, `--memory`, `--cores`, `--disk`, `--version`, `--url`) and use `--dry-run` first to see what it will do.

### Option 2: from the Proxmox interface

Create an unprivileged **debian-12-standard** CT (1 GB RAM, 2 cores, 8 GB disk) on your LAN bridge, enable **Nesting** and *Start at boot*, start it and install the `.deb` from the latest release with `apt install ./labtower_X.Y.Z_all.deb`. Then open `http://CT-IP/`.

### After installing
Enable HTTPS with `pct exec ID -- /usr/local/bin/labtower-https enable --redirect`; update by installing the new `.deb` inside the CT; back the CT up with Proxmox (vzdump) as well as LabTower's Teleporter. Keep the CT on the same bridge as your LAN so Net Monitor can see MAC addresses. In an unprivileged CT, allow ping for the services (the script does it): `echo 'net.ipv4.ping_group_range = 0 65534' > /etc/sysctl.d/99-labtower-ping.conf && sysctl -q -p /etc/sysctl.d/99-labtower-ping.conf` inside the CT.

### Speed tests (optional)
WAN Monitor has its own engine and works with nothing installed. To use **Ookla** or **LibreSpeed**, install the program **inside the CT** (`pct enter ID`), not on the Proxmox node: Ookla's script does not recognise the node's Debian version. The commands are the same as in the Spanish section above (Ookla: packagecloud script, or the `x86_64` binary from `speedtest.net/apps/cli`; LibreSpeed: the `amd64` binary of v1.0.14). Then pick the engine in **WAN Monitor → Settings → Test engine**; the first time Ookla asks you to accept its license: `speedtest --accept-license --accept-gdpr`.
