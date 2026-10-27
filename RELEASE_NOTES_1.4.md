# Pi Console 1.4

## Español
Reúne los cambios desde 1.3 (builds 1.3a a 1.3g).

**Nuevo: NAS Monitor** (`/nas/`)
- Módulo nuevo para ver uno o varios **NAS Synology**, igual que se agregan clusters de Proxmox o servidores de UPS.
- Lee por **SNMP v3** (usuario, nivel, clave de autenticación y de cifrado, como en Net Monitor) o por v2c. Tiene botón *Probar conexión* antes de guardar.
- La página principal es como la de UPS Monitor: una tabla **Resumen de NAS** con todos los NAS. Cada fila se abre y muestra su detalle; por defecto se abre el primero.
- El detalle muestra medidores (CPU, RAM, volumen, temperatura, discos y tiempo encendido), volúmenes, discos, red y UPS conectado. Tiene tres gráficos (CPU/RAM, temperatura y red) con rangos 1h / 1d / 1mo / Todo y los valores al pasar el cursor.
- Avisa disco con falla, volumen degradado o casi lleno, temperatura alta y actualización de DSM. Un Storage Pool lleno no avisa, porque es normal que lo esté. Los avisos también salen en el Resumen.
- Permiso «NAS» en el Admin Panel, tarjeta en la página de inicio y en el Resumen, y entrada en el menú de todos los módulos. Los respaldos (Teleporter) incluyen la lista de NAS.
- Las claves SNMP se guardan con permisos 600, la API nunca las devuelve y no se pasan por la línea de comandos.
- Para activarlo en el Synology: *Panel de control → Terminal y SNMP → SNMP → Habilitar SNMPv3*.

**Seguridad**
- Proxmox Monitor: el estado de Ceph y la cantidad de núcleos de cada nodo ya no pueden meter HTML en la página.
- Protección CSRF más estricta: en navegadores antiguos que no envían `Sec-Fetch-Site` también se comparan el esquema y el puerto del origen.

**Interno:** 69 pruebas automáticas (eran 43). Se actualizaron los workflows de GitHub Actions.

**Al actualizar:** no hay cambios de configuración. Los usuarios existentes reciben el permiso «NAS» solos: administrador si administran WOL y solo lectura el resto. Se cambia en el Admin Panel.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.4/pi-console_1.4_all.deb
sha256sum pi-console_1.4_all.deb    # ef8135685fa92e0c5efc4be3a67233e1b2f095414ac9dab7d42d186caeee0e48
sudo apt-get install -y ./pi-console_1.4_all.deb
```

## English
Includes every change since 1.3 (builds 1.3a to 1.3g).

**New: NAS Monitor** (`/nas/`)
- New module to watch one or more **Synology NAS**, added the same way as Proxmox clusters or UPS servers.
- Reads over **SNMP v3** (user, level, auth and privacy keys, as in Net Monitor) or v2c. It has a *Test connection* button before saving.
- The main page works like UPS Monitor: a **NAS Summary** table with every NAS. Each row opens and shows its detail; the first one opens by default.
- The detail shows gauges (CPU, RAM, volume, temperature, disks and uptime), volumes, disks, network and attached UPS. It has three charts (CPU/RAM, temperature and network) with 1h / 1d / 1mo / All ranges and the values on hover.
- Alerts for a failed disk, a degraded or nearly full volume, high temperature and an available DSM update. A full Storage Pool does not alert, because it is normal for it to be full. Alerts also show on the Overview.
- «NAS» permission in the Admin Panel, a card on the home page and on the Overview, and an entry in every module's menu. Backups (Teleporter) include the NAS list.
- SNMP keys are stored with 600 permissions, the API never returns them and they are never put on the command line.
- To enable it on the Synology: *Control Panel → Terminal & SNMP → SNMP → Enable SNMPv3*.

**Security**
- Proxmox Monitor: the Ceph status and the node core count can no longer inject HTML into the page.
- Stricter CSRF protection: in old browsers that do not send `Sec-Fetch-Site`, the origin scheme and port are also compared.

**Internal:** 69 automated tests (was 43). The GitHub Actions workflows were updated.

**When updating:** no configuration changes. Existing users get the «NAS» permission automatically: administrator if they administer WOL, read-only otherwise. Change it in the Admin Panel.

**Install or update**
```bash
wget https://github.com/gonzalovalenzuela/pi-console/releases/download/1.4/pi-console_1.4_all.deb
sha256sum pi-console_1.4_all.deb    # ef8135685fa92e0c5efc4be3a67233e1b2f095414ac9dab7d42d186caeee0e48
sudo apt-get install -y ./pi-console_1.4_all.deb
```
