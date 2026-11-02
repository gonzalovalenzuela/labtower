**Resumen**
- **Nueva Funcionalidad:** Búsqueda global en la barra superior (también con la tecla `/`). Busca equipos de Net Monitor, UPS, VMs y contenedores de Proxmox, NAS, servidores DNS y equipos de Wake-on-LAN. Solo muestra lo que cada usuario tiene permiso de ver.
- **Nueva Funcionalidad:** Tarjeta «Reglas de alerta»: los administradores definen umbrales sobre las métricas del servidor, UPS, NAS, Proxmox, DNS e internet (por ejemplo, «temperatura del servidor > 65 °C» o «batería del UPS < 50 %»), como aviso o crítico. Las reglas que se cumplen aparecen en el panel de atención y en el estado general. Se evalúan mientras el Resumen está abierto.
- **Nueva Funcionalidad:** Tarjeta «Monitores sugeridos»: si Net Monitor ve un equipo con puertos típicos de un servicio que LabTower puede monitorear (Proxmox, servidor UPS, Pi-hole o AdGuard Home, Synology) y aún no está configurado, lo sugiere con un enlace al módulo. Solo la ven los administradores de ese módulo y cada sugerencia se puede descartar.
- **Nueva Funcionalidad:** Se puede pausar y reanudar el bloqueo de Pi-hole / AdGuard desde la tarjeta DNS (5 min, 30 min, 1 hora o hasta reanudar). Requiere nivel «ejecutar» en DNS Monitor.
- **Mejora:** En modo kiosko no se muestran los controles para pausar el bloqueo de Pi-hole.

**Gráficos (UPS, NAS, DNS, WAN y switches)**
- **Mejora:** Todos los gráficos de detalle se ven y funcionan igual: mismos colores, ejes, etiquetas de fecha y ventana con valores al pasar el mouse.
- **Nueva Funcionalidad:** Rango de 1 semana en UPS, NAS, DNS y WAN.
- **Nueva Funcionalidad:** Botón «vs anterior», que dibuja con línea punteada el período justo anterior para comparar.
- **Nueva Funcionalidad:** Los eventos importantes (cortes de energía, cambios de IP, caídas) aparecen como marcas sobre el gráfico del módulo correspondiente.

**Net Monitor**
- **Nueva Funcionalidad:** Las VM y contenedores de Proxmox se reconocen en la tabla de equipos: insignia «VM 100» / «CT 200» junto al nombre, detalle con la VM/CT correspondiente y búsqueda por «proxmox», «vm», «ct» o número. Se cruza por MAC, luego por IP y, si no hay ninguna, por nombre idéntico.
- **Nueva Funcionalidad:** Opción «Quitar sin conexión tras N días» para eliminar solos los equipos que dejaron de responder (0 = nunca). Solo la ven y la cambian los administradores.
- **Nueva Funcionalidad:** Switch Monitor: los switches se listan en la barra lateral y se puede elegir uno para verlo solo.
- **Nueva Funcionalidad:** Switch Monitor: la velocidad de cada puerto tiene color (10G, 2.5G, 1G, 100M, 10M) en el panel, en la tabla y en una leyenda.
- **Nueva Funcionalidad:** El panel de Pi-hole muestra cuántos dispositivos, concesiones DHCP y registros de DNS local leyó, y avisa si alguno no se pudo leer.
- **Mejora:** Las tarjetas «Hosts descubiertos», «Online» y «Offline» se pueden tocar y filtran la tabla igual que los botones; tocar de nuevo la activa vuelve a mostrar todos.
- **Mejora:** Los nombres de Pi-hole incluyen los registros de «Local DNS» y las concesiones DHCP, con prioridad sobre el DNS inverso. Se actualizan cada 5 minutos (antes 30) y al empezar cada escaneo; si Pi-hole no responde, se conservan los que ya había.
- **Mejora:** Los nombres también se piden directo al DNS de Pi-hole (puerto 53), sin contraseña ni API, así aparecen aunque la contraseña de aplicación no pueda leer la configuración.
- **Fix:** Los equipos apagados o sin respuesta (por ejemplo la interfaz AMT de un servidor apagado) no recibían nombre de Pi-hole ni del DNS; ahora sí.
- **Fix:** La purga de equipos offline no borra nada si en el escaneo no respondió ningún equipo (por ejemplo, si el servidor perdió la red).
- **Seguridad:** Los nombres que vienen de Pi-hole o del DNS se limpian de caracteres de control y se limitan a 80 caracteres. La consulta directa al DNS aplica la misma regla anti-SSRF que la API de Pi-hole.

**Proxmox Monitor**
- **Nueva Funcionalidad:** Click en el nombre de una VM o contenedor lleva a su detalle en Net Monitor (como en UPS Monitor), con tarjeta de datos al pasar el mouse.
- **Nueva Funcionalidad:** Lee la MAC y las IP de cada VM/CT (fijas del contenedor, agente de invitado en las VM, interfaz del contenedor), cada 5 minutos, en `/api/guests`.
- **Nueva Funcionalidad:** Botón «Ocultar detenidas» para esconder las VM y contenedores apagados (se recuerda en el navegador).
- **Mejora:** Los días para marcar un respaldo como viejo se configuran por cluster (solo administradores). Por defecto son 7 días (antes 36 horas).
- **Mejora:** Los nombres de las VM y contenedores ya no se cortan; las métricas pasan a una segunda línea bajo el nombre.
- **Fix:** Corregido un error que impedía cargar la página.

**UPS Monitor**
- **Mejora:** Los equipos conectados al UPS muestran el nombre que Net Monitor conoce; si no tiene, la IP.
- **Mejora:** Si la batería tiene menos de 1 año, la edad se muestra en meses.
- **Mejora de rendimiento:** El estado de envejecimiento de la batería se calcula en segundo plano (antes frenaba la página más de un segundo) y se guardan unos segundos las pruebas de batería y la fecha de cambio para no leer disco y base de datos en cada consulta.

**WAN Monitor**
- **Mejora:** El aviso de cambio de IP pública indica la IP anterior, dura 24 horas y queda en la línea de tiempo del Resumen. La IP pública aparece también en la barra lateral.

**Admin Panel**
- **Nueva Funcionalidad:** La tabla de usuarios tiene la columna «Última conexión».
- **Fix:** «Última conexión» ya no sale vacía para quien tiene una sesión abierta.
- **Mejora:** El aviso de versión nueva muestra los comandos para actualizar (`wget` y `sudo apt install`) con un botón para copiarlos.

**Instalador**
- **Mejora:** Al terminar ya no recomienda activar el HTTPS si ya está activado; muestra que está habilitado.

**Interno**
- **Mejora:** Scripts de respaldo, HTTPS e instalación sin avisos de `shellcheck` (incluye una protección para que una variable vacía nunca borre `/etc`) y se quitó código que ya no se usaba. No cambia comportamientos.
- **Mejora:** Los escaneos de seguridad de GitHub (bandit y gitleaks) quedan en verde.
