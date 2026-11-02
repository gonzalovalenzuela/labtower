**VPN Monitor (nuevo módulo)**
- **Nueva Funcionalidad:** VPN Monitor (`/vpn/`): muestra quién está conectado a Tailscale, OpenVPN y WireGuard, desde cuándo, con qué dirección y cuánto tráfico, con las sesiones recientes y el gráfico de tendencia.
- **Nueva Funcionalidad:** Tailscale se lee por su API con una clave de solo lectura. OpenVPN (archivo de estado, versiones 1, 2 y 3) y WireGuard (`wg show all dump`) se leen por SSH en el servidor VPN, que puede ser otra VM, un CT o un NAS. LabTower genera su propia llave SSH, ejecuta solo dos comandos fijos y se recomienda restringir la llave en `authorized_keys` con `command="…"`.
- **Nueva Funcionalidad:** Opción «Ejecutar con sudo» para servidores donde el archivo de estado o `wg show` son solo de root (por ejemplo Synology). Usa `sudo -n` y solo con los dos comandos fijos.
- **Nueva Funcionalidad:** Los peers de WireGuard se nombran con alias por clave pública.
- **Nueva Funcionalidad:** Avisos de conexión y desconexión en la línea de tiempo del Resumen y tarjeta de VPN en el Resumen.
- **Nueva Funcionalidad:** Permiso propio «vpn» (Admin Panel → usuarios), servicio con usuario propio y respaldo de `vpn.json` y `state.json`. La llave SSH no se respalda: después de restaurar hay que crearla de nuevo e instalarla en el servidor VPN.

**Administración**
- **Nueva Funcionalidad:** Comando `sudo labtower-resetpw [usuario]` para recuperar el acceso desde la consola: genera una contraseña aleatoria (se debe cambiar en el próximo inicio de sesión), cierra las sesiones de ese usuario, quita su bloqueo por intentos fallidos y lo anota en la auditoría. Opciones: `--ask` (tú escribes la contraseña), `--disable-2fa` (perdiste el teléfono) y `--list`.
- **Fix:** Subir respaldo: el selector de archivos aceptaba solo `.gz`, pero los respaldos descargados del panel salen cifrados (`.gpg`). Ahora acepta también `.gpg`.

**Portada**
- **Mejora:** Cada tarjeta muestra el estado de su módulo junto a la flecha: verde «activo», amarillo «con avisos», rojo «con fallas» y gris «sin respuesta». Antes solo había dos indicadores (WOL y NUT) y «activo» solo significaba que el servicio contestaba. En pantallas angostas se ve solo el punto.

**WAN Monitor**
- **Nueva Funcionalidad:** Ajustes «Bajada contratada» y «Subida contratada» (Mb/s). La tarjeta de velocidad muestra el porcentaje entregado en la última prueba y su promedio de 7 días (verde desde 90 %, naranja desde 70 %, rojo bajo eso).

**NAS Monitor**
- **Mejora:** Los umbrales de espacio de los volúmenes se configuran por NAS (Editar NAS → «Aviso de volumen» y «Crítico de volumen», por defecto 90 % y 95 %).
- **Fix:** Las alertas usaban 90 y 95 %, pero los colores de la página NAS y del Resumen usaban 80 y 90 % fijos, así que un volumen al 84 % salía en naranja o rojo sin alerta. Ahora todo usa los mismos valores.

**Proxmox Monitor**
- **Nueva Funcionalidad:** Botón «Expandir todo / Contraer todo» en Diagnóstico del cluster, para abrir o cerrar de una vez reinicios, respaldos y SMART.

**Resumen**
- **Quitado:** La tarjeta «Monitores sugeridos» (generaba demasiados falsos positivos).

**Instalación en un CT de Proxmox**
- **Fix:** Restaurar un respaldo desde el Admin Panel fallaba con «The "no new privileges" flag is set». El servicio `admin-panel` (el único que usa `sudo`) ahora se instala sin las opciones de systemd que activan ese indicador. En una VM no cambia nada.
