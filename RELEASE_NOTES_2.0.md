# LabTower 2.0

## Español
**Pi Console ahora se llama LabTower.** Es el mismo proyecto: ya no es solo para la Raspberry Pi y había muchos proyectos con el nombre anterior. Hay logo nuevo en la página de inicio, los iconos de la app y las capturas.

**Qué cambia**
- El paquete es `labtower` y reemplaza a `pi-console`. Las rutas pasan a `/opt/labtower`, `/var/lib/labtower`, `/etc/labtower`, `/var/log/labtower` y `/var/backups/labtower`.
- El usuario del sistema es `labtower`. Los servicios `pi-console-ups` y `pi-console-overview` ahora son `labtower-ups` y `labtower-overview`; los demás conservan el nombre.
- Los comandos son `labtower-https`, `labtower-health`, `labtower-resources` y `labtower-sftp-backup`. `teleporter` no cambia.
- Las variables `PICONSOLE_*` pasan a `LABTOWER_*` (las de `/etc/default` se renombran solas).
- Los respaldos hechos con la 1.x (`pi-console-*.tar.gz`) se pueden restaurar y descargar desde Teleporter.

**Al actualizar:** se hace sola. El instalador retira `pi-console` y mueve usuario, datos, certificados HTTPS, respaldo SFTP, registros y respaldos anteriores a los nombres nuevos. Las contraseñas y los datos no cambian; hay que iniciar sesión otra vez. Si tenías scripts propios con `pi-console-https` u otros comandos, cámbiales el nombre. Opcional: `sudo dpkg -P pi-console` limpia el registro del paquete viejo.

**Instalar o actualizar**
```bash
wget https://github.com/gonzalovalenzuela/labtower/releases/download/2.0/labtower_2.0_all.deb
sha256sum labtower_2.0_all.deb    # 68398345dd2f60edc0d489fa4d58aea673f1bab84f8a0d7e455159179c86d34f
sudo apt-get install -y ./labtower_2.0_all.deb
```

## English
**Pi Console is now called LabTower.** It is the same project: it is no longer Raspberry Pi only and many other projects shared the old name. There is a new logo on the home page, the app icons and the screenshots.

**What changes**
- The package is `labtower` and replaces `pi-console`. Paths become `/opt/labtower`, `/var/lib/labtower`, `/etc/labtower`, `/var/log/labtower` and `/var/backups/labtower`.
- The system user is `labtower`. The services `pi-console-ups` and `pi-console-overview` are now `labtower-ups` and `labtower-overview`; the others keep their names.
- Commands are `labtower-https`, `labtower-health`, `labtower-resources` and `labtower-sftp-backup`. `teleporter` is unchanged.
- The `PICONSOLE_*` variables become `LABTOWER_*` (the ones in `/etc/default` are renamed automatically).
- Backups made with 1.x (`pi-console-*.tar.gz`) can still be restored and downloaded from Teleporter.

**When upgrading:** it happens by itself. The installer removes `pi-console` and moves the user, data, HTTPS certificates, SFTP backup, logs and earlier backups to the new names. Passwords and data do not change; you have to log in again. If you had your own scripts calling `pi-console-https` or other commands, rename them. Optional: `sudo dpkg -P pi-console` cleans the old package record.

**Install or upgrade**
```bash
wget https://github.com/gonzalovalenzuela/labtower/releases/download/2.0/labtower_2.0_all.deb
sha256sum labtower_2.0_all.deb    # 68398345dd2f60edc0d489fa4d58aea673f1bab84f8a0d7e455159179c86d34f
sudo apt-get install -y ./labtower_2.0_all.deb
```
