**Seguridad**
- **Autenticación en dos pasos (2FA).** En Admin Panel → «Seguridad» se activa escaneando un código QR con cualquier app (Google Authenticator, Aegis, 1Password…); la clave escrita queda como alternativa. Se entregan 10 códigos de recuperación de un solo uso. Con 2FA activo, todos los formularios de acceso piden el código; cada código sirve una vez y los intentos fallidos cuentan para el bloqueo. Un admin puede restablecer el 2FA de otro usuario. El QR se genera dentro de LabTower, sin librerías ni internet.
- **Registro de auditoría** en Admin Panel: quién creó o eliminó usuarios, cambió permisos o contraseñas, activó o restableció 2FA, cerró sesiones, creó/descargó/restauró/eliminó respaldos, cambió la configuración del WAN Monitor o la fecha de una batería, y los bloqueos por intentos fallidos. Guarda las últimas 5.000 entradas y nunca contraseñas ni códigos.
- **Aviso de versión nueva** en Admin Panel: consulta las versiones publicadas en GitHub (solo estables) cada 12 horas como máximo y avisa con el enlace a las notas. Solo lee; no descarga ni instala. Se desactiva con `LABTOWER_UPDATE_CHECK=0` en `/etc/default/labtower`.

**WAN Monitor**
- **Chequeo del router.** Pregunta al router si su enlace WAN está arriba, para saber si un corte es de la red local o de la línea. Tipos: Huawei (WiFi AX3, Mesh y otros), OpenWrt, DD-WRT y TP-Link clásico. Los cortes se marcan como «Red local (LAN)», «Línea / proveedor (WAN)» o «Internet». Botón «Probar router» con el motivo exacto si falla. Solo lee; la clave se guarda en el servidor y nunca se muestra. Los TP-Link nuevos con inicio de sesión cifrado no se pueden consultar.
- **Comparación con el router:** en «Conexión» muestra cuánto tiempo lleva conectada la WAN según el router y cuántos cortes registró LabTower en ese período («2 aquí · 0 WAN»).

**UPS Monitor**
- **Salud de la batería:** autonomía ahora, a batería llena y con 50 % más de carga; edad de la batería y tendencia de capacidad (avisa si cae 20 % o más en 120 días).
- **Fecha de cambio de la batería:** botón ✎ junto a la edad para indicarla a mano (tiene prioridad sobre la del UPS).
- **Edad de la batería:** se leen `battery.date` y `battery.mfr.date` y se usa la más reciente creíble; una edad de más de 10 años se ignora (algunos UPS dejan la fecha de fábrica).
- **Registro de autotests:** los últimos 8; un test fallido avisa en el Resumen. «Último resultado» muestra la fecha y hora en que LabTower lo vio, y si el UPS vuelve a «No test initiated» (APC Back-UPS) se muestra el último resultado real. Los resultados se traducen al español.

**Proxmox Monitor**
- **Diagnóstico del cluster:** reinicios de nodos con línea de tiempo (marca los simultáneos), quórum de corosync, Ceph (OSD y avisos) y SMART de los discos, incluido «Unsafe Shutdowns» en NVMe.
- **Respaldos (vzdump):** último respaldo de cada VM/CT, antigüedad, tamaño y verificación; marca «Sin respaldo» o «Muy viejo» y lista las tareas fallidas. Se pueden **ignorar** VMs de prueba o templates, y marcar varias a la vez. El token necesita `Datastore.Audit` y `Sys.Audit` (rol `PVEAuditor`).

**NAS Monitor**
- Ahora también lee **TrueNAS** (25.04 o más nuevo) y **OpenMediaVault** (7 o más nuevo), solo lectura.

**Net Monitor / Switch Monitor**
- Errores CRC por puerto (cable o tarjeta de red), aviso de enlaces que rebotan y casilla «Avisar por puerto».

**Respaldo**
- `labtower-sftp-backup verify` y cron diario: comprueba en el storage que la copia más reciente existe, no está vacía y es reciente.

**Cambios**
- Los textos y la documentación ya no dicen «la Pi»: dicen «el servidor». «Raspberry Pi» queda solo en la fuente de poder, la temperatura y la lista de equipos compatibles.
- La página de inicio ahora está en inglés y español, y la barra lateral dice «Resumen» en español.

**Correcciones**
- WOL Console: aviso «Net Monitor hosts file not readable» (los archivos compartidos quedaban en modo 600 en vez de 640).
- Proxmox: después de ignorar o dejar de ignorar una VM, la página podía mostrar el estado anterior hasta por 10 minutos.
- Textos sin traducir o mezclados entre idiomas en Net Monitor, Proxmox Monitor, WOL Console, NAS Monitor, WAN Monitor, Admin Panel y el Resumen; las fechas del UPS Monitor usan día/mes/año en español.
- NAS Monitor: el error de conexión ya no dice «esta Pi».
