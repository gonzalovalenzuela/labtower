#!/bin/bash
# teleporter.sh — backup, verify and restore LabTower (data + NUT + nginx)
#
#   teleporter backup  [file.tar.gz]        create a backup (needs root)
#   teleporter check   <file.tar.gz>        verify a backup (no changes made)
#   teleporter restore <file.tar.gz> [-y]   restore it on this server (needs root)
#
# Installed as /usr/local/bin/teleporter.sh, with a `teleporter` symlink.
#
# Design notes (lessons learned):
#  * All data lives in /var/lib/labtower (users.json, <module>/…, metrics.db); /opt/labtower-auth
#    (root-owned) holds SYMLINKS to the shared files — restore writes the real file and re-creates them.
#  * Root NEVER follows a symlink inside the folders the services control: every read/write/delete there
#    goes through the `sfs` helper (openat + O_NOFOLLOW from a trusted base) and SQLite snapshots are taken
#    by the unprivileged service user. A link planted by a compromised service cannot expose or overwrite
#    root files.
#  * Live sessions (sessions.json) are NOT part of a backup: a backup must not carry usable logins.
#  * history.db is copied with the SQLite backup API (consistent while running);
#    stale -wal/-shm files are removed on restore.
#  * `check` runs before every restore; nothing is touched if the archive is bad.
#  * A safety snapshot of the current state is taken before restoring.
#  * Services are always restarted, even if the restore fails half way.
#  * Archive members are whitelisted: absolute paths, "..", links are rejected.
#  * Files with secrets (tokens, SNMP/NUT passwords) are stored/restored 0600.
# ES: Teleporter = respaldo y restauración de LabTower (datos + NUT + nginx). Lo usa el administrador por consola
#     (backup / check / restore) y el panel web a través de sudo (gui-backup / gui-restore). Los comentarios de este
#     archivo están en inglés y, donde aporta, con su versión en español («ES:»).
#     Ideas clave: se verifica el respaldo ANTES de tocar nada; se toma una foto de seguridad del estado actual;
#     los servicios siempre se reinician aunque falle a medias; y el archivo solo admite miembros de una lista blanca.
set -uo pipefail

TELEPORTER_VERSION="2.2.0"

# Paths (overridable through the environment, used by the tests).
# Under sudo (the admin panel) every override is dropped: only the defaults apply.
# ES: Cuando corre por sudo (desde el panel) se ignoran todas las variables de entorno de prueba: solo valen las rutas reales, así nadie puede redirigir el script como root.
if [ -n "${SUDO_USER:-}" ]; then
  unset LABTOWER_HOME LABTOWER_DATA LABTOWER_AUTH_LINK LABTOWER_NUT_DIR LABTOWER_NGINX_CONF \
        LABTOWER_NGINX_ENABLED LABTOWER_SAFETY_DIR LABTOWER_LOCK TELEPORTER_SKIP_SYSTEM \
        TELEPORTER_DROP LABTOWER_RESTORE_LOG LABTOWER_SANDBOX_USER
fi
PI_HOME="${LABTOWER_HOME:-/opt/labtower}"
DATA_DIR="${LABTOWER_DATA:-/var/lib/labtower}"
AUTH_DIR="${LABTOWER_AUTH_LINK:-/opt/labtower-auth}"
NUT_DIR="${LABTOWER_NUT_DIR:-/etc/nut}"
NGINX_CONF="${LABTOWER_NGINX_CONF:-/etc/nginx/sites-available/labtower.conf}"
NGINX_ENABLED="${LABTOWER_NGINX_ENABLED:-/etc/nginx/sites-enabled/labtower.conf}"
SAFETY_DIR="${LABTOWER_SAFETY_DIR:-/var/backups/labtower}"
SPOOL_DIR="$DATA_DIR/teleporter"      # backups/uploads handled by the admin panel
LOCK_FILE="${LABTOWER_LOCK:-/run/lock/labtower-teleporter.lock}"
RESTORE_LOG="${LABTOWER_RESTORE_LOG:-/var/log/labtower/restore.log}"   # root-owned: the panel only reads it
# ES: Usuario SIN datos con el que se abre un respaldo no confiable (extraer, validar JSON/SQLite). «labtower» ya no es dueño de nada ni corre ningún servicio.
#     Cada archivo de datos pertenece al usuario de SU módulo (owner_of); el panel (labtower-auth) es dueño de auth/ y de la carpeta de intercambio.
# EN: Data-less user used to open an untrusted backup (extract, validate JSON/SQLite). "labtower" owns nothing and runs no service any more.
#     Every data file belongs to the user of ITS module (owner_of); the panel (labtower-auth) owns auth/ and the exchange folder.
SANDBOX_USER="${LABTOWER_SANDBOX_USER:-labtower}"
SERVICES="wol-console labtower-ups admin-panel net-monitor proxmox-monitor nas-monitor dns-monitor wan-monitor labtower-overview"
SKIP_SYSTEM="${TELEPORTER_SKIP_SYSTEM:-0}"   # 1 = no systemctl/nginx/chown (tests)
DROP_FORCE="${TELEPORTER_DROP:-0}"           # 1 = drop to the service user even with SKIP_SYSTEM (tests)
# Trusted base for the `sfs` helper: the (root-owned) parent of the data folder, resolved once.
DATA_PARENT="$(dirname -- "$DATA_DIR")"
SFS_BASE="$(realpath -m -- "$DATA_PARENT")"

# member-in-archive | real path on disk
# ES: Tabla «miembro dentro del archivo | ruta real en disco» de los datos de cada módulo. Si se agrega un módulo con datos, se agrega aquí.
DATA_FILES=(
  "data/users.json|$DATA_DIR/auth/users.json"
  "data/wol-console/devices.json|$DATA_DIR/wol-console/devices.json"
  "data/wol-console/wake_log.json|$DATA_DIR/wol-console/wake_log.json"
  "data/nut-monitor/servers.json|$DATA_DIR/nut-monitor/servers.json"
  "data/nut-monitor/history.db|$DATA_DIR/nut-monitor/history.db"
  "data/net-monitor/hosts.json|$DATA_DIR/net-monitor/hosts.json"
  "data/net-monitor/config.json|$DATA_DIR/net-monitor/config.json"
  "data/net-monitor/switches.json|$DATA_DIR/net-monitor/switches.json"
  "data/net-monitor/switches.db|$DATA_DIR/net-monitor/switches.db"
  "data/proxmox-monitor/clusters.json|$DATA_DIR/proxmox-monitor/clusters.json"
  "data/nas-monitor/nas.json|$DATA_DIR/nas-monitor/nas.json"
  "data/dns-monitor/dns.json|$DATA_DIR/dns-monitor/dns.json"
  "data/wan-monitor/wan.json|$DATA_DIR/wan-monitor/wan.json"
  "data/wan-monitor/state.json|$DATA_DIR/wan-monitor/state.json"
  "data/overview/metrics.db|$DATA_DIR/overview/metrics.db"
  "data/proxmox-monitor/metrics.db|$DATA_DIR/proxmox-monitor/metrics.db"
  "data/nas-monitor/metrics.db|$DATA_DIR/nas-monitor/metrics.db"
  "data/dns-monitor/metrics.db|$DATA_DIR/dns-monitor/metrics.db"
  "data/wan-monitor/metrics.db|$DATA_DIR/wan-monitor/metrics.db"
)
# ES: Archivos de la versión 1.2.0o (historiales en JSON). Ya no se respaldan, pero un respaldo antiguo puede traerlos: al restaurar se dejan en su sitio y los servicios los importan a metrics.db una sola vez.
# EN: Files of version 1.2.0o (JSON histories). They are no longer backed up, but an old backup may carry them: on restore they are put back and the services import them into metrics.db once.
LEGACY_FILES=(
  "data/proxmox-monitor/history.json|$DATA_DIR/proxmox-monitor/history.json"
  "data/pi-history.json|$DATA_DIR/overview/pi-history.json"
)
# ES: Respaldos anteriores a 2.1.3 traen UN metrics.db compartido: al restaurar se parte por módulo (auth/migrate_layout.py).
# EN: Backups from before 2.1.3 carry ONE shared metrics.db: on restore it is split per module (auth/migrate_layout.py).
OLD_METRICS="data/metrics.db"
METRICS_MODULES="overview proxmox-monitor nas-monitor dns-monitor wan-monitor"
# ES: Igual para la configuración del sistema (nginx y NUT). Estos archivos solo se restauran por consola con --nut / --nginx.
CONF_FILES=(
  "conf/nginx/labtower.conf|$NGINX_CONF"
  "conf/nut/nut.conf|$NUT_DIR/nut.conf"
  "conf/nut/ups.conf|$NUT_DIR/ups.conf"
  "conf/nut/upsd.conf|$NUT_DIR/upsd.conf"
  "conf/nut/upsd.users|$NUT_DIR/upsd.users"
  "conf/nut/upsmon.conf|$NUT_DIR/upsmon.conf"
)

# ── output helpers ────────────────────────────────────────────────────────────
if [ -t 1 ]; then G=$'\033[0;32m'; Y=$'\033[1;33m'; R=$'\033[0;31m'; B=$'\033[0;34m'; N=$'\033[0m'
else G=""; Y=""; R=""; B=""; N=""; fi
# ES: Ayudantes de salida: ok (✓), warn (!, cuenta advertencias), err (✗, cuenta errores), hdr (título de sección) y die (error fatal).
ok()   { echo "  ${G}✓${N} $*"; }
warn() { echo "  ${Y}!${N} $*"; WARNINGS=$((WARNINGS+1)); }
err()  { echo "  ${R}✗${N} $*" >&2; ERRORS=$((ERRORS+1)); }
hdr()  { echo; echo "${B}▶ $*${N}"; }
die()  { echo "${R}Error:${N} $*" >&2; exit 1; }
WARNINGS=0; ERRORS=0

TMP=""; STAGE=""; WORKROOT=""
cleanup() { [ -n "$TMP" ] && rm -rf "$TMP"; [ -n "$STAGE" ] && rm -rf "$STAGE"; [ -n "$WORKROOT" ] && rm -rf "$WORKROOT"; return 0; }
# ES: Carpeta de trabajo para ABRIR un respaldo no confiable. El padre es de root (700) y la subcarpeta de extracción pertenecerá al usuario de servicio:
#     así ningún otro proceso de ese usuario puede alcanzarla por nombre mientras se extrae y se valida (solo el proceso lanzado desde ella la ve, por su cwd).
# EN: Work folder to OPEN an untrusted backup. The parent is root's (700) and the extraction subfolder will belong to the service user:
#     so no other process of that user can reach it by name while it is extracted and validated (only the process started from it sees it, via its cwd).
mk_work() {  # sets WORKROOT and TMP
  WORKROOT=$(mktemp -d) || die "cannot create a temporary directory"
  TMP="$WORKROOT/x"; mkdir -m 700 "$TMP" || die "cannot create a temporary directory"
}
trap cleanup EXIT

# ES: Exige ser root; si no, aborta indicando que se use sudo.
need_root() {
  [ "$SKIP_SYSTEM" = "1" ] && return 0
  [ "$(id -u)" -eq 0 ] || die "this command needs root: sudo teleporter $*"
}
need_tools() {
  for t in tar gzip python3 sha256sum; do
    command -v "$t" >/dev/null 2>&1 || die "missing required tool: $t"
  done
}
users_exist() {
  local u; for u in "$SANDBOX_USER" labtower-auth labtower-wol labtower-nut labtower-net labtower-pve labtower-nas labtower-dns labtower-wan labtower-overview; do
    id -u "$u" >/dev/null 2>&1 || { echo "$u"; return 1; }
  done
}

# ES: Ayudante «sfs»: toda operación de root sobre carpetas que controlan los servicios (datos, intercambio del panel) pasa por aquí.
#     Recorre la ruta componente a componente con openat + O_NOFOLLOW desde una base de confianza, así un enlace simbólico plantado
#     por un servicio comprometido nunca se sigue (ni para leer, ni para escribir, ni para borrar).
# EN: "sfs" helper: every root operation inside folders the services control (data, panel exchange folder) goes through here.
#     It walks the path component by component with openat + O_NOFOLLOW from a trusted base, so a symlink planted by a compromised
#     service is never followed (not to read, write nor delete).
SFS_PY=$(cat <<'PY'
import os, re, pwd, grp, sys, stat, time
NF = os.O_NOFOLLOW
def die(m, rc=1):
    sys.stderr.write("sfs: %s\n" % m); sys.exit(rc)
def split(base, path):
    base = os.path.realpath(base); path = os.path.normpath(path)
    if path != base and not path.startswith(base + "/"):
        die("path outside the trusted base: %s" % path)
    return base, [p for p in path[len(base):].split("/") if p]
def ids(user):
    if not user or user == "-": return -1, -1
    u = pwd.getpwnam(user); return u.pw_uid, u.pw_gid
def opendir(base, parts, create=False, uid=-1, gid=-1, mode=0o750):
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
    for p in parts:
        try:
            nfd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | NF, dir_fd=fd)
        except FileNotFoundError:
            if not create: os.close(fd); raise
            os.mkdir(p, mode, dir_fd=fd)
            nfd = os.open(p, os.O_RDONLY | os.O_DIRECTORY | NF, dir_fd=fd)
            if uid >= 0: os.fchown(nfd, uid, gid)
        except OSError as e:
            os.close(fd); die("refusing %s (%s)" % (p, e.strerror), 3)
        os.close(fd); fd = nfd
    return fd
def main():
    op, base, path = sys.argv[1:4]; a = sys.argv[4:]
    os.umask(0o077)
    base, parts = split(base, path)
    if op == "get":                      # get BASE SRC DST
        if not parts: die("bad path")
        try: d = opendir(base, parts[:-1])
        except FileNotFoundError: sys.exit(2)
        try: s = os.open(parts[-1], os.O_RDONLY | NF, dir_fd=d)
        except FileNotFoundError: sys.exit(2)
        except OSError as e: die("refusing %s (%s)" % (path, e.strerror), 3)
        if not stat.S_ISREG(os.fstat(s).st_mode): die("not a regular file: %s" % path, 3)
        o = os.open(a[0], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        while True:
            b = os.read(s, 1 << 20)
            if not b: break
            os.write(o, b)
        os.close(o); os.close(s); return
    if op == "put":                      # put BASE DST SRC MODE USER
        src, mode, user = a[0], int(a[1], 8), a[2]
        uid, gid = ids(user)
        if not parts: die("bad path")
        d = opendir(base, parts[:-1], True, uid, gid)
        name = parts[-1]; tmp = ".%s.sfs.%d" % (name, os.getpid())
        try: os.unlink(tmp, dir_fd=d)
        except FileNotFoundError: pass
        o = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NF, 0o600, dir_fd=d)
        with open(src, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b: break
                os.write(o, b)
        os.fsync(o); os.fchmod(o, mode)
        if uid >= 0: os.fchown(o, uid, gid)
        os.close(o); os.rename(tmp, name, src_dir_fd=d, dst_dir_fd=d); os.close(d); return
    if op == "rm":                       # rm BASE PATH
        try: d = opendir(base, parts[:-1])
        except (FileNotFoundError, SystemExit): return
        try: os.unlink(parts[-1], dir_fd=d)
        except FileNotFoundError: pass
        except IsADirectoryError: pass
        return
    if op == "mkdir":                    # mkdir BASE PATH USER MODE
        uid, gid = ids(a[0]); mode = int(a[1], 8)
        d = opendir(base, parts, True, uid, gid, mode)
        os.fchmod(d, mode)
        if uid >= 0: os.fchown(d, uid, gid)
        return
    if op == "prune":                    # prune BASE DIR KEEP
        keep = int(a[0])
        try: d = opendir(base, parts)
        except FileNotFoundError: return
        bk = re.compile(r"^(labtower|pi-console)-[A-Za-z0-9._-]{1,80}\.tar\.gz$"); up = re.compile(r"^(upload-\d{8}_\d{6}\.tar\.gz|\.upload-[0-9]+-[0-9a-f]{8}\.tmp)$")
        files = []
        for n in os.listdir(d):
            try: st = os.stat(n, dir_fd=d, follow_symlinks=False)
            except OSError: continue
            if not stat.S_ISREG(st.st_mode): continue
            if bk.match(n): files.append((st.st_mtime, n))
            elif up.match(n) and time.time() - st.st_mtime > 86400: os.unlink(n, dir_fd=d)
        files.sort(reverse=True)
        for _, n in files[keep:]: os.unlink(n, dir_fd=d)
        return
    die("unknown op")
main()
PY
)
sfs() {  # sfs <op> <path> [args…]   (paths under $DATA_DIR are re-based on the resolved parent)
  local op="$1" path="$2"; shift 2
  python3 -I -c "$SFS_PY" "$op" "$SFS_BASE" "${path/#$DATA_PARENT\//$SFS_BASE/}" "$@"
}
# ES: Ejecuta un comando como el usuario de servicio sin privilegios (en producción siempre; en pruebas solo con TELEPORTER_DROP=1).
as_service() {
  if [ "$SKIP_SYSTEM" = "1" ] && [ "$DROP_FORCE" != "1" ]; then "$@"
  elif [ "$(id -u)" != "0" ]; then "$@"          # already unprivileged (e.g. "check" run by the panel itself): nothing to drop
  else runuser -u "$SANDBOX_USER" -- "$@"; fi
}
# ES: Dueño de un archivo de datos según su carpeta (un usuario del sistema por módulo). «-» = no cambiar dueño (pruebas sin permisos de root).
# EN: Owner of a data file according to its folder (one system user per module). "-" = do not change the owner (tests without root).
owner_of() {  # <path under $DATA_DIR>
  if [ "$SKIP_SYSTEM" = "1" ]; then [ "$DROP_FORCE" = "1" ] && echo "$SANDBOX_USER" || echo "-"; return; fi
  local rel="${1#"$DATA_DIR"/}"
  case "${rel%%/*}" in
    auth|teleporter) echo labtower-auth;;   wol-console) echo labtower-wol;;      nut-monitor) echo labtower-nut;;
    net-monitor) echo labtower-net;;        proxmox-monitor) echo labtower-pve;;   nas-monitor) echo labtower-nas;;
    dns-monitor) echo labtower-dns;;        wan-monitor) echo labtower-wan;;       overview) echo labtower-overview;;
    *) return 1;;
  esac
}
# wol-console and net-monitor each publish ONE file for the other (group labtower reads it); everything else is private.
dir_mode()  { case "$(basename -- "$1")" in wol-console|net-monitor) echo 710;; *) echo 700;; esac; }
file_mode() { case "$1" in */wol-console/devices.json|*/net-monitor/hosts.json) echo 640;; *) echo 600;; esac; }
# Run a command as the owner of a data file (so a database is read by the user that owns it, never by root).
as_owner() {  # <user> cmd…
  local u="$1"; shift
  if [ "$u" = "-" ] || [ "$(id -u)" != "0" ] || { [ "$SKIP_SYSTEM" = "1" ] && [ "$DROP_FORCE" != "1" ]; }; then "$@"
  else runuser -u "$u" -- "$@"; fi
}
is_secret() {
  case "$1" in
    *users.json|*sessions.json|*config.json|*clusters.json|*nas.json|*dns.json|*servers.json|*upsd.users|*upsmon.conf) return 0;;
  esac
  return 1
}

# ── validators ────────────────────────────────────────────────────────────────
# ES: Validadores: JSON bien formado, base SQLite íntegra (devuelve la cantidad de filas) y que users.json tenga al menos un usuario (si no, restaurarlo dejaría fuera a todos).
# ES: Los validadores abren un archivo NO confiable (sobre todo el analizador de SQLite): corren como el usuario de servicio, con la carpeta del archivo como
#     directorio actual (ruta relativa), y no como root.
# EN: The validators open an UNTRUSTED file (above all the SQLite parser): they run as the service user, with the file's folder as the current directory
#     (relative path), and not as root.
in_dir_as_service() {  # <file> <python source>  → runs the source with sys.argv[1] = the file's base name
  local f="$1" src="$2"
  ( cd "$(dirname -- "$f")" && as_service python3 -I -c "$src" "$(basename -- "$f")" ) 2>/dev/null
}
validate_json() {  # file -> prints nothing, rc 0/1
  in_dir_as_service "$1" 'import json, sys
with open(sys.argv[1], encoding="utf-8") as f: json.load(f)'
}
validate_sqlite() {  # file -> prints row count on success
  in_dir_as_service "$1" 'import sqlite3, sys
# SQLite resuelve la ruta absoluta y la carpeta de trabajo no es alcanzable por nombre: se lee el archivo (ruta relativa) y se analiza en memoria.
# EN: SQLite resolves the absolute path and the work folder is not reachable by name: the file is read (relative path) and analysed in memory.
# Una imagen en modo WAL (respaldos de versiones anteriores) no se abre sin su -wal: se marca como modo clásico (bytes 18 y 19 del encabezado).
# EN: A WAL-mode image (backups from older versions) cannot be opened without its -wal: it is flagged as rollback-journal mode (header bytes 18 and 19).
c = sqlite3.connect(":memory:")
with open(sys.argv[1], "rb") as f: raw = bytearray(f.read())
if len(raw) > 20 and raw[18] == 2 and raw[19] == 2: raw[18] = raw[19] = 1
c.deserialize(bytes(raw))
r = c.execute("PRAGMA integrity_check").fetchone()
if not r or r[0] != "ok": sys.exit(1)
try: n = c.execute("SELECT COUNT(*) FROM history").fetchone()[0]
except Exception:
    try: n = sum(c.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in ("pi_samples", "pve_samples"))
    except Exception: n = "?"
print(n)'
}
users_have_admin() {  # users.json con forma válida: nombres seguros, hash de texto y niveles conocidos / users.json with a valid shape
  in_dir_as_service "$1" 'import json, re, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
if not isinstance(d, dict) or not d: sys.exit(1)
LV = ("none", "readonly", "execute", "admin")
for name, u in d.items():
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name): sys.exit(1)
    if not isinstance(u, dict) or not isinstance(u.get("password_hash"), str): sys.exit(1)
    p = u.get("permissions", {})
    if not isinstance(p, dict) or any(not isinstance(k, str) or v not in LV for k, v in p.items()): sys.exit(1)
sys.exit(0)'
}

# ── archive safety ────────────────────────────────────────────────────────────
# Rejects absolute paths, "..", links/devices and unknown members.
# ES: Seguridad del archivo: rechaza rutas absolutas, «..», enlaces, dispositivos y cualquier miembro que no esté en la lista blanca.
archive_is_safe() {  # archive
  local archive="$1" listing m
  gzip -t "$archive" 2>/dev/null || { err "not a valid gzip file"; return 1; }
  listing=$(tar -tzvf "$archive" 2>/dev/null) || { err "tar cannot read the archive"; return 1; }
  while IFS= read -r line; do
    case "${line:0:1}" in
      -|d) ;;
      *) err "archive contains a link or special file: $line"; return 1;;
    esac
  done <<<"$listing"
  # ES: Tope de tamaño descomprimido (anti «bomba gzip»): un .tar.gz de 200 MB podría expandirse a decenas de GB y llenar el disco.
  # EN: Cap on the uncompressed size (anti gzip bomb): a 200 MB .tar.gz could expand to tens of GB and fill the disk.
  local total
  total=$(awk '{s+=$3} END{printf "%d", s}' <<<"$listing")
  [ "${total:-0}" -le 2147483648 ] || { err "archive expands to more than 2 GiB — refusing"; return 1; }
  while IFS= read -r m; do
    m="${m#./}"; m="${m%/}"
    if [ -z "$m" ] || [ "$m" = "." ]; then continue; fi
    case "$m" in
      /*|*..*) err "unsafe path in archive: $m"; return 1;;
    esac
    case "$m" in
      backup.json|SHA256SUMS|data|data/*|conf|conf/*) ;;
      *) err "unexpected member in archive: $m"; return 1;;
    esac
  done < <(tar -tzf "$archive")
  return 0
}

# ES: Extrae el archivo ya validado en la carpeta de trabajo (ver mk_work) COMO el usuario de servicio sin privilegios: el contenido de un respaldo no confiable
#     nunca lo procesa root. La carpeta se le entrega a ese usuario y tar arranca con ella como directorio actual (la ruta por nombre no le sirve a nadie más).
# EN: Extracts the already-checked archive into the work folder (see mk_work) AS the unprivileged service user: the content of an untrusted backup is
#     never processed by root. The folder is handed to that user and tar starts with it as its current directory (the path by name is of no use to anyone else).
extract_archive() {  # archive dest
  if [ "$(id -u)" = "0" ] && ! { [ "$SKIP_SYSTEM" = "1" ] && [ "$DROP_FORCE" != "1" ]; }; then chown "$SANDBOX_USER" "$2" || { err "could not prepare the work folder"; return 1; }; fi
  ( cd "$2" && as_service tar -xzf - --no-same-owner --no-same-permissions ) < "$1" 2>/dev/null \
    || { err "could not extract the archive"; return 1; }
  # Legacy layout (teleporter 1.x): data/auth/{users,sessions}.json
  local f
  for f in users sessions; do
    if [ -f "$2/data/auth/$f.json" ] && [ ! -f "$2/data/$f.json" ]; then
      mv "$2/data/auth/$f.json" "$2/data/$f.json"
    fi
  done
  return 0
}

# ── BACKUP ────────────────────────────────────────────────────────────────────
# ES: BACKUP. Copia los datos (la base SQLite con su API de respaldo, que es consistente aunque el servicio esté escribiendo), la configuración, escribe backup.json (versión, fecha, host) y SHA256SUMS, empaqueta con modo 600 y verifica lo que acaba de escribir.
cmd_backup() {
  need_root backup "$@"; need_tools; take_lock
  local dest="${1:-}"
  if [ -z "$dest" ]; then
    mkdir -p "$SAFETY_DIR" 2>/dev/null || true
    dest="$SAFETY_DIR/labtower-$(hostname -s)-$(date +%Y%m%d_%H%M%S).tar.gz"
  fi
  case "$dest" in *.tar.gz|*.tgz) ;; *) dest="$dest.tar.gz";; esac
  [ -e "$dest" ] && die "destination already exists: $dest"
  [ -d "$(dirname "$dest")" ] || die "destination directory does not exist: $(dirname "$dest")"

  TMP=$(mktemp -d) || die "cannot create a temporary directory"
  trap cleanup EXIT
  umask 077
  mkdir -p "$TMP/data" "$TMP/conf"

  echo "${B}LabTower Teleporter — backup${N}"
  echo "  Host: $(hostname)   Date: $(date -Iseconds)"

  hdr "Module data"
  local entry rel src n_data=0
  for entry in "${DATA_FILES[@]}"; do
    rel="${entry%%|*}"; src="${entry#*|}"
    if [ ! -f "$src" ]; then warn "$rel — not present, skipped"; continue; fi
    mkdir -p "$TMP/$(dirname "$rel")"
    if [[ "$rel" == *.db ]]; then
      # ES: La instantánea SQLite la toma el usuario del servicio (no root): root solo recoge el resultado sin seguir enlaces.
      # ES: La toma el DUEÑO del archivo (su módulo) y la deja en su propia carpeta; root solo la recoge sin seguir enlaces.
      local snap="$(dirname -- "$src")/.snap.$$.db" owner
      owner=$(owner_of "$src") || { err "$rel — unknown owner"; continue; }
      if as_owner "$owner" python3 -I -c 'import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
d = sqlite3.connect(sys.argv[2])
s.backup(d)
d.execute("PRAGMA journal_mode=DELETE")     # the copy is a single self-contained file (a WAL-mode image cannot be opened without its -wal)
d.close(); s.close()' "$src" "$snap" 2>/dev/null \
         && sfs get "$snap" "$TMP/$rel"
      then ok "$rel ($(du -h "$TMP/$rel" | cut -f1)) — consistent SQLite snapshot"
      else err "$rel — SQLite backup failed"; sfs rm "$snap"; continue; fi
      sfs rm "$snap"
    else
      sfs get "$src" "$TMP/$rel" || { err "$rel — copy failed"; continue; }
      if [[ "$rel" == *.json ]] && ! python3 -I -c 'import json, sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$TMP/$rel" 2>/dev/null; then
        warn "$rel — source is not valid JSON (copied as is)"
      else ok "$rel ($(du -h "$TMP/$rel" | cut -f1))"; fi
    fi
    n_data=$((n_data+1))
  done

  hdr "System configuration"
  for entry in "${CONF_FILES[@]}"; do
    rel="${entry%%|*}"; src="${entry#*|}"
    if [ -r "$src" ] && [ -f "$src" ]; then
      mkdir -p "$TMP/$(dirname "$rel")"
      cp -- "$src" "$TMP/$rel" && ok "$src"
    else warn "$src — not present or unreadable, skipped"; fi
  done

  [ "$n_data" -gt 0 ] || die "no LabTower data found — is the package installed?"

  hdr "Packing"
  local pkg_ver
  pkg_ver=$(dpkg-query -W -f='${Version}' labtower 2>/dev/null || echo unknown)
  python3 -I - "$TMP" "$TELEPORTER_VERSION" "$pkg_ver" "$SERVICES" <<'PY'
import json, os, socket, subprocess, sys, time
tmp, tver, pver, services = sys.argv[1:5]
def state(s):
    try: return subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception: return "unknown"
json.dump({
  "teleporter_version": tver, "package_version": pver,
  "date": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "hostname": socket.gethostname(),
  "services": {s: state(s) for s in services.split()},
}, open(os.path.join(tmp, "backup.json"), "w"), indent=2)
PY
  ( cd "$TMP" && find data conf backup.json -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
  tar -czf "$dest" -C "$TMP" backup.json SHA256SUMS data conf || die "could not create $dest"
  chmod 600 "$dest"
  ok "Backup written: $dest ($(du -h "$dest" | cut -f1)) — mode 600, it contains passwords and tokens"

  # Verify what we just wrote
  hdr "Self-check"
  if cmd_check_quiet "$dest"; then ok "archive verified"; else die "the new archive failed verification"; fi
  echo; echo "${G}Backup completed.${N}  Next: teleporter check \"$dest\""
}

# ── CHECK ─────────────────────────────────────────────────────────────────────
# check_archive <archive> <extract-dir> ; fills counters, returns 1 on hard errors
# ES: CHECK. Verifica un respaldo sin cambiar nada: archivo seguro, backup.json válido, sumas SHA-256, cada JSON/SQLite íntegro y un usuario al menos. Devuelve error solo si hay errores duros; los archivos opcionales ausentes son advertencias.
check_archive() {
  local archive="$1" dir="$2" entry rel f size
  [ -f "$archive" ] || { err "file not found: $archive"; return 1; }
  archive_is_safe "$archive" || return 1
  extract_archive "$archive" "$dir" || return 1

  [ -f "$dir/backup.json" ] || { err "backup.json missing — not a LabTower backup"; return 1; }
  validate_json "$dir/backup.json" || { err "backup.json is not valid JSON"; return 1; }

  if [ -f "$dir/SHA256SUMS" ]; then
    if ( cd "$dir" && sha256sum --quiet -c SHA256SUMS >/dev/null 2>&1 ); then ok "checksums match"
    else err "checksum mismatch — the archive is corrupted or was modified"; return 1; fi
  else warn "no SHA256SUMS (backup made by an older teleporter)"; fi

  local found=0
  for entry in "${DATA_FILES[@]}"; do
    rel="${entry%%|*}"; f="$dir/$rel"
    if [ ! -f "$f" ]; then warn "$rel — not in backup"; continue; fi
    found=$((found+1)); size=$(du -h "$f" | cut -f1)
    if [[ "$rel" == *.json ]]; then
      if validate_json "$f"; then ok "$rel ($size) — valid JSON"; else err "$rel — INVALID JSON"; fi
    else
      local rows
      if rows=$(validate_sqlite "$f"); then ok "$rel ($size) — SQLite OK, $rows rows"
      else err "$rel — SQLite CORRUPT"; fi
    fi
  done
  if [ -f "$dir/$OLD_METRICS" ]; then
    local rows
    if rows=$(validate_sqlite "$dir/$OLD_METRICS"); then ok "$OLD_METRICS (old shared database) — SQLite OK, $rows rows; will be split per module"
    else err "$OLD_METRICS — SQLite CORRUPT"; fi
    found=$((found+1))
  fi
  [ "$found" -gt 0 ] || { err "the backup contains no data files"; return 1; }
  if [ -f "$dir/data/users.json" ]; then
    users_have_admin "$dir/data/users.json" || err "data/users.json has no users or an invalid structure — restoring it would lock you out"
  else warn "data/users.json not in backup: current users will be kept"; fi
  for entry in "${CONF_FILES[@]}"; do
    rel="${entry%%|*}"
    [ -f "$dir/$rel" ] && ok "$rel" || warn "$rel — not in backup"
  done
  [ "$ERRORS" -eq 0 ]
}

# ES: Igual que check_archive pero sin imprimir (se usa en la autoverificación del respaldo).
cmd_check_quiet() { local d; d=$(mktemp -d) || return 1; mkdir -m 700 "$d/x" || { rm -rf "$d"; return 1; }; ( check_archive "$1" "$d/x" >/dev/null 2>&1 ); local rc=$?; rm -rf "$d"; return $rc; }

# ES: Comando «check» para el usuario: muestra el resultado y de dónde viene el respaldo (host, fecha, versiones).
cmd_check() {
  need_tools
  [ $# -ge 1 ] || die "usage: teleporter check <file.tar.gz>"
  mk_work
  echo "${B}LabTower Teleporter — check${N}"
  echo "  Backup: $1"
  hdr "Archive"
  check_archive "$1" "$TMP"; local rc=$?
  if [ -f "$TMP/backup.json" ]; then
    hdr "Origin"
    in_dir_as_service "$TMP/backup.json" 'import json, sys
d = json.load(open(sys.argv[1]))
print("  Host:     %s" % d.get("hostname", "?"))
print("  Date:     %s" % d.get("date", "?"))
print("  Package:  %s   teleporter %s" % (d.get("package_version", "?"), d.get("teleporter_version", "?")))'
  fi
  echo
  if [ $rc -ne 0 ]; then echo "${R}Backup NOT usable — $ERRORS error(s), $WARNINGS warning(s).${N}"; exit 1
  elif [ $WARNINGS -gt 0 ]; then echo "${Y}Backup OK with $WARNINGS warning(s) (missing optional files).${N}"
  else echo "${G}Backup OK.${N}"; fi
}

# ── RESTORE ───────────────────────────────────────────────────────────────────
SERVICES_STOPPED=0
# ES: RESTORE. Arranca los 5 servicios e informa cuál falla (con el comando para ver su log).
start_services() {
  [ "$SKIP_SYSTEM" = "1" ] && return 0
  systemctl daemon-reload 2>/dev/null || true
  local s
  for s in $SERVICES; do
    if systemctl start "$s" 2>/dev/null; then ok "$s started"
    else err "$s failed to start — journalctl -u $s -n 20"; fi
  done
}
RESTORE_FINISHED=0; RM_SOURCE=""
# ES: Se ejecuta SIEMPRE al salir de una restauración (incluso si se aborta): reinicia los servicios, marca «RESULT: failed» si no terminó bien y borra el respaldo temporal.
on_exit_restore() {
  local rc=$?
  # Always bring the services back, even after an abort.
  if [ "$SERVICES_STOPPED" -eq 1 ]; then SERVICES_STOPPED=0; echo; echo "Restarting services after abort…"; start_services; fi
  [ "$RESTORE_FINISHED" -eq 1 ] || echo "RESULT: failed"
  if [ -n "$RM_SOURCE" ]; then
    case "$(dirname "$RM_SOURCE")" in /var/tmp/teleporter.*|"$SAFETY_DIR"/.restore.*) rm -rf -- "$(dirname "$RM_SOURCE")";; *) rm -f -- "$RM_SOURCE";; esac
  fi
  cleanup
  return $rc
}

# ES: Instala un archivo de forma atómica: copia a un temporal junto al destino, fija modo y dueño, y lo mueve encima (también reemplaza un enlace simbólico perdido).
install_file() {  # src dst mode owner:group
  local src="$1" dst="$2" mode="$3" owner="$4" tmpf
  mkdir -p "$(dirname "$dst")" || return 1
  tmpf="$dst.teleporter.$$"
  cp -- "$src" "$tmpf" && chmod "$mode" "$tmpf" || { rm -f "$tmpf"; return 1; }
  [ "$SKIP_SYSTEM" = "1" ] || chown "$owner" "$tmpf" 2>/dev/null || true
  mv -f -- "$tmpf" "$dst"          # atomic replace; also replaces a stray symlink
}

# ES: Pasos de la restauración: 1) verificar el respaldo sin tocar nada · 2) pedir confirmación · 3) foto de seguridad del estado actual
#     · 4) detener servicios · 5) restaurar datos (borrando restos -wal/-shm de SQLite) · 6) recrear los enlaces de auth
#     · 7) configuración del sistema (NUT y nginx solo si se pidió con --nut / --nginx; nginx se prueba con «nginx -t» y, si falla, vuelve la anterior)
#     · 8) permisos · 9) arrancar servicios. Termina con «RESULT: ok|errors|failed», que el panel lee en restore.log.
cmd_restore() {
  need_root restore "$@"; need_tools
  local archive="" assume_yes=0 with_nut=0 with_nginx=0 rm_source=0 a
  for a in "$@"; do case "$a" in
    -y|--yes) assume_yes=1;;
    --nut) with_nut=1;;
    --nginx) with_nginx=1;;
    --rm-source) rm_source=1;;
    -*) die "unknown option: $a";;
    *) archive="$a";;
  esac; done
  [ -n "$archive" ] || die "usage: sudo teleporter restore <file.tar.gz> [-y] [--nut] [--nginx]"
  RM_SOURCE=""; [ "$rm_source" -eq 1 ] && RM_SOURCE="$archive"
  take_lock
  [ -d "$PI_HOME" ] || die "$PI_HOME not found — install the package first: sudo dpkg -i labtower_*.deb"
  if [ "$SKIP_SYSTEM" != "1" ]; then miss=$(users_exist) || die "system user '$miss' not found — install the package first"; fi

  mk_work
  trap on_exit_restore EXIT
  umask 077
  echo "${B}LabTower Teleporter — restore${N}"
  echo "  Backup: $archive"

  hdr "Verifying backup (nothing is changed yet)"
  check_archive "$archive" "$TMP" || die "the backup failed verification — aborting, no changes were made"

  echo
  echo "${Y}  This will OVERWRITE the current LabTower data and NUT/nginx configuration.${N}"
  if [ "$assume_yes" -ne 1 ]; then
    read -r -p "  Continue? [y/N] " ans || ans=""
    [[ "$ans" =~ ^[yYsS]$ ]] || { echo "Cancelled."; exit 0; }
  fi

  hdr "Safety snapshot of the current state"
  mkdir -p "$SAFETY_DIR" && chmod 700 "$SAFETY_DIR"
  local snap="$SAFETY_DIR/pre-restore-$(date +%Y%m%d_%H%M%S).tar.gz"
  # ES: En un subshell: cmd_backup limpia SUS carpetas al salir y no debe tocar la carpeta de trabajo de esta restauración (WORKROOT/TMP).
  # EN: In a subshell: cmd_backup cleans up ITS folders on exit and must not touch this restore's work folder (WORKROOT/TMP).
  if ( ERRORS=0; WORKROOT=""; STAGE=""; cmd_backup "$snap" >/dev/null 2>&1 ); then ok "saved to $snap"
  else warn "could not create the safety snapshot (continuing)"; fi

  hdr "Stopping services"
  if [ "$SKIP_SYSTEM" != "1" ]; then
    local s; SERVICES_STOPPED=1
    for s in $SERVICES; do systemctl stop "$s" 2>/dev/null && ok "$s stopped" || warn "$s was not running"; done
  fi

  hdr "Restoring data"
  local entry rel dst src mode owner m n_restored=0
  [ -d "$TMP/data" ] || { err "the verified backup is no longer in the work folder — nothing was restored"; return 1; }
  sfs mkdir "$DATA_DIR" - 750 || err "$DATA_DIR — unsafe or not usable"
  # ES: Respaldo antiguo con un metrics.db común: se parte por módulo (con el usuario sin datos) y cada parte ocupa el lugar que le toca.
  # EN: Old backup with one shared metrics.db: it is split per module (by the data-less user) and each part takes its place.
  if [ -f "$TMP/$OLD_METRICS" ]; then
    if as_service python3 -I "$PI_HOME/auth/migrate_layout.py" split-metrics "$TMP/$OLD_METRICS" "$TMP/data/.split" >/dev/null 2>&1; then
      for m in $METRICS_MODULES; do
        [ -f "$TMP/data/$m/metrics.db" ] || as_service sh -c 'mkdir -p "$1/data/$2" && [ -f "$1/data/.split/$2.db" ] && mv "$1/data/.split/$2.db" "$1/data/$2/metrics.db"' sh "$TMP" "$m" 2>/dev/null || true
      done
      ok "$OLD_METRICS split per module"
    else warn "$OLD_METRICS — could not be split, the charts start empty"; fi
  fi
  put_data() {  # <rel> <dst> <src> -> sfs put with the owner/modes of the module
    local o d
    o=$(owner_of "$2") || return 1
    d=$(dirname -- "$2")
    [ "$d" = "$DATA_DIR" ] || sfs mkdir "$d" "$o" "$(dir_mode "$d")" || return 1
    sfs put "$2" "$3" "$(file_mode "$2")" "$o"
  }
  for entry in "${DATA_FILES[@]}"; do
    rel="${entry%%|*}"; dst="${entry#*|}"; src="$TMP/$rel"
    [ -f "$src" ] || { warn "$rel — not in backup, current file kept"; continue; }
    [[ "$rel" == *.db ]] && { sfs rm "$dst-wal"; sfs rm "$dst-shm"; sfs rm "$dst-journal"; }
    if put_data "$rel" "$dst" "$src"; then ok "$rel"; n_restored=$((n_restored+1)); else err "$rel — could not be restored"; fi
  done
  [ "$n_restored" -gt 0 ] || err "no data file was restored"
  for entry in "${LEGACY_FILES[@]}"; do
    rel="${entry%%|*}"; dst="${entry#*|}"; src="$TMP/$rel"
    [ -f "$src" ] || continue
    if put_data "$rel" "$dst" "$src"; then ok "$rel (old format, will be imported)"; else warn "$rel — could not be restored"; fi
  done

  hdr "Auth links"
  mkdir -p "$AUTH_DIR"
  # ES: /opt/labtower-auth es de root: los servicios no pueden cambiar estos enlaces. sessions.json ya no se enlaza (el servicio lo crea en su carpeta de datos).
  ln -sfn "$PI_HOME/auth/auth.py" "$AUTH_DIR/auth.py"
  ln -sfn "$DATA_DIR/auth/users.json" "$AUTH_DIR/users.json"
  rm -f "$AUTH_DIR/sessions.json"
  ok "$AUTH_DIR → $DATA_DIR"

  hdr "System configuration"
  local nginx_bak=""
  for entry in "${CONF_FILES[@]}"; do
    rel="${entry%%|*}"; dst="${entry#*|}"; src="$TMP/$rel"
    [ -f "$src" ] || { warn "$dst — not in backup, kept"; continue; }
    case "$rel" in
      conf/nut/*)
        if [ "$with_nut" -ne 1 ]; then warn "$dst — kept (NUT config is only restored with --nut)"; continue; fi
        if [ ! -d "$NUT_DIR" ]; then warn "$NUT_DIR does not exist (is 'nut' installed?) — skipped"; continue; fi
        mode=640; grp=root; getent group nut >/dev/null 2>&1 && grp=nut
        install_file "$src" "$dst" "$mode" "root:$grp" && ok "$dst" || err "$dst — could not be restored";;
      conf/nginx/*)
        if [ "$with_nginx" -ne 1 ]; then warn "$dst — kept (the package ships its own; use --nginx to overwrite)"; continue; fi
        [ -f "$dst" ] && { nginx_bak="$TMP/nginx.prev"; cp -- "$dst" "$nginx_bak"; }
        install_file "$src" "$dst" 644 "root:root" && ok "$dst" || err "$dst — could not be restored";;
    esac
  done
  if [ "$SKIP_SYSTEM" != "1" ] && [ -f "$NGINX_CONF" ]; then
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
    rm -f /etc/nginx/sites-enabled/default
    if command -v nginx >/dev/null 2>&1; then
      if nginx -t >/dev/null 2>&1; then systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null; ok "nginx reloaded"
      else
        err "nginx -t failed with the restored config"
        if [ -n "$nginx_bak" ]; then cp -- "$nginx_bak" "$NGINX_CONF" && nginx -t >/dev/null 2>&1 \
          && { systemctl reload nginx 2>/dev/null; warn "previous nginx config put back"; }; fi
      fi
    fi
  fi

  # ES: El código en /opt/labtower es de root y de solo lectura para los servicios; solo los datos (/var/lib/labtower) son suyos.
  hdr "Permissions"
  ok "code in $PI_HOME stays root-owned; every module owns only its folder in $DATA_DIR"

  hdr "Starting services"
  SERVICES_STOPPED=0
  start_services

  echo
  if [ "$ERRORS" -eq 0 ]; then echo "${G}Restore completed.${N}"; else echo "${Y}Restore finished with $ERRORS error(s) — review the messages above.${N}"; fi
  echo "  URL: http://$(hostname -I 2>/dev/null | awk '{print $1}')"
  echo "  Previous state: $snap"
  RESTORE_FINISHED=1
  if [ "$ERRORS" -eq 0 ]; then echo "RESULT: ok"; else echo "RESULT: errors"; fi
  [ "$ERRORS" -eq 0 ]
}

# ── lock (one backup/restore at a time) ───────────────────────────────────────
LOCK_HELD=0
# ES: Candado: solo un respaldo/restauración a la vez (flock sobre un archivo de /run/lock).
take_lock() {
  [ "$LOCK_HELD" = 1 ] && return 0
  command -v flock >/dev/null 2>&1 || return 0
  mkdir -p "$(dirname "$LOCK_FILE")" 2>/dev/null || return 0
  { exec 9>"$LOCK_FILE"; } 2>/dev/null || return 0
  flock -n 9 || die "another backup/restore is already running"
  LOCK_HELD=1
}
release_lock() { exec 9>&-; LOCK_HELD=0; }

# ── admin-panel entry points (run through sudo as root; strict argument checks) ─
# ES: PUNTOS DE ENTRADA DEL PANEL (corren como root vía sudo, con validación estricta). El nombre del respaldo debe cumplir este patrón: evita rutas con «../».
NAME_RE='^((labtower|pi-console)-[A-Za-z0-9._-]{1,80}|upload-[0-9]{8}_[0-9]{6})\.tar\.gz$'
# ES: Prepara la carpeta de intercambio con el panel (modo 700, dueño labtower-auth).
spool_init() {
  local o; o=$(owner_of "$SPOOL_DIR")
  sfs mkdir "$SPOOL_DIR" "$o" 700 || die "the exchange folder $SPOOL_DIR is not safe"
}
# ES: Limpieza: se conservan los 5 respaldos más nuevos y se borran las subidas con más de un día.
spool_prune() {  # keep the newest 5 backups, drop uploads older than a day (never follows links)
  sfs prune "$SPOOL_DIR" 5 2>/dev/null || true
}

# ES: Crea un respaldo para el panel y imprime «BACKUP_FILE=<nombre>» (la línea que el panel lee).
cmd_gui_backup() {
  need_root gui-backup "$@"; need_tools; take_lock
  spool_init
  local name="labtower-$(hostname -s | tr -c 'A-Za-z0-9.\n-' '_')-$(date +%Y%m%d_%H%M%S).tar.gz"
  [[ "$name" =~ $NAME_RE ]] || die "could not build a valid backup name"
  # ES: Se arma en una carpeta de root y luego se entrega al panel sin seguir enlaces (la carpeta del panel la controla un servicio).
  local o; o=$(owner_of "$SPOOL_DIR")
  mkdir -p "$SAFETY_DIR" && chmod 700 "$SAFETY_DIR"
  STAGE=$(mktemp -d "$SAFETY_DIR/.gui.XXXXXX") || die "cannot create a staging directory"
  cmd_backup "$STAGE/$name" || exit 1
  sfs put "$SPOOL_DIR/$name" "$STAGE/$name" 600 "$o" || die "could not hand the backup to the panel"
  rm -rf "$STAGE"; STAGE=""
  spool_prune
  echo "BACKUP_FILE=$name"
}

# ES: Restaura para el panel. Trabaja sobre una COPIA privada propiedad de root (así el usuario sin privilegios no puede cambiar el archivo entre la verificación y la extracción) y la lanza separada del servicio del panel, porque la restauración reinicia ese mismo servicio. Desde el panel NUT/nginx nunca se restauran.
cmd_gui_restore() {  # <name> <nut:0|1> <nginx:0|1>
  need_root gui-restore "$@"; need_tools; take_lock
  local name="${1:-}" nut="${2:-0}" ngx="${3:-0}" src copy
  [[ "$name" =~ $NAME_RE ]] || die "invalid backup name"
  [[ "$nut" =~ ^[01]$ && "$ngx" =~ ^[01]$ ]] || die "invalid option"
  # The GUI path runs as root through sudo: restoring /etc/nut or the nginx site there would
  # let anyone who can upload a backup run commands as root. Those two are CLI-only.
  [ "$nut" = 0 ] && [ "$ngx" = 0 ] || die "restoring NUT/nginx is only available from the command line (teleporter restore --nut/--nginx)"
  src="$SPOOL_DIR/$name"
  # Work on a root-owned private copy so the unprivileged user cannot swap the
  # file between verification and extraction (and a link in the exchange folder is never followed).
  # ES: La copia va en el directorio de respaldos (root, 700) y NO en /var/tmp: el panel corre con PrivateTmp y el trabajo de restauración (systemd-run) no vería ese /var/tmp privado.
  # EN: The copy goes in the backups directory (root, 700), NOT in /var/tmp: the panel runs with PrivateTmp and the restore job (systemd-run) would not see that private /var/tmp.
  mkdir -p "$SAFETY_DIR" && chmod 700 "$SAFETY_DIR"
  copy=$(mktemp -d "$SAFETY_DIR/.restore.XXXXXX") || die "cannot create a temporary directory"
  sfs get "$src" "$copy/restore.tar.gz" || { rm -rf "$copy"; die "backup not found: $name"; }
  chmod 600 "$copy/restore.tar.gz"
  local flags=(-y --rm-source); [ "$nut" = 1 ] && flags+=(--nut); [ "$ngx" = 1 ] && flags+=(--nginx)
  local log="$RESTORE_LOG"
  release_lock   # the detached job takes it again
  spool_init; mkdir -p "$(dirname "$log")" && chmod 755 "$(dirname "$log")"; rm -f -- "$log"
  # Detached from the admin-panel cgroup: the restore stops and restarts that very service.
  if [ "$SKIP_SYSTEM" != "1" ] && command -v systemd-run >/dev/null 2>&1; then
    systemctl reset-failed labtower-restore.service 2>/dev/null || true
    systemd-run --quiet --collect --unit=labtower-restore \
      -p StandardOutput="file:$log" -p StandardError="file:$log" \
      "$0" restore "$copy/restore.tar.gz" "${flags[@]}" \
      || { rm -rf "$copy"; die "could not start the restore job"; }
  else
    ( umask 022; setsid "$0" restore "$copy/restore.tar.gz" "${flags[@]}" >"$log" 2>&1 & )
  fi
  echo "RESTORE_STARTED=1"
}

# ── main ──────────────────────────────────────────────────────────────────────
# ES: Ayuda de uso del comando.
usage() {
  cat <<EOF
LabTower Teleporter v$TELEPORTER_VERSION

  teleporter backup  [file.tar.gz]        create a backup (default: $SAFETY_DIR/)
  teleporter check   <file.tar.gz>        verify a backup, changes nothing
  teleporter restore <file.tar.gz> [-y] [--nut] [--nginx]
                                          restore on this server (verifies first, takes a
                                          safety snapshot, restarts services). The NUT
                                          and nginx configuration are kept unless you
                                          pass --nut / --nginx.

Backup contents: users, WOL devices, UPS servers + history.db (includes UPS temperature),
Net Monitor hosts + config (SNMP), switches (list + history), Proxmox clusters, NAS list (SNMP), metrics.db (Proxmox and NAS CPU/memory and Pi
temperature/under-voltage histories), NUT config, nginx site.
The archive holds passwords and tokens (mode 600) — keep it private.
EOF
}
# ES: Despacho de comandos: backup, check, restore (consola) y gui-backup, gui-restore (panel).
CMD="${1:-}"; [ $# -gt 0 ] && shift
case "$CMD" in
  backup)  cmd_backup "$@";;
  check)   cmd_check "$@";;
  restore) cmd_restore "$@";;
  gui-backup)  cmd_gui_backup "$@";;
  gui-restore) cmd_gui_restore "$@";;
  -h|--help|help|"") usage; [ -n "$CMD" ] || exit 1;;
  *) echo "Unknown command: $CMD" >&2; usage; exit 1;;
esac
