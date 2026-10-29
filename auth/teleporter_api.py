"""Teleporter helpers for the admin panel: list, create, upload, verify and restore
backups. Privileged work is done by /usr/local/bin/teleporter.sh through sudo; this
module only validates names/sizes and talks to that script."""
# Flujo: el panel (usuario sin privilegios «labtower») NO toca los respaldos directamente. Todo lo que
# requiere root (crear, restaurar) lo hace /usr/local/bin/teleporter.sh vía sudo con una regla muy
# acotada en sudoers; aquí solo se validan nombres y tamaños y se habla con ese script.
# EN: Flow: the panel (unprivileged user "labtower") does NOT touch backups directly. Everything that
#     needs root (create, restore) is done by /usr/local/bin/teleporter.sh through sudo with a very narrow
#     sudoers rule; here only names and sizes are validated and the script is called.
import os, re, shutil, subprocess, tempfile, time
from pathlib import Path

# Rutas y límites; las variables TELEPORTER_* permiten cambiarlos en las pruebas.
# EN: Paths and limits; the TELEPORTER_* variables let tests change them.
BIN        = os.environ.get("TELEPORTER_BIN", "/usr/local/bin/teleporter.sh")
SUDO       = os.environ.get("TELEPORTER_SUDO", "sudo -n").split()
SPOOL      = Path(os.environ.get("TELEPORTER_SPOOL", "/var/lib/labtower/teleporter"))
# El registro de restauración lo escribe root (el panel solo lo lee): así el panel no puede redirigir un archivo que root abre.
# EN: The restore log is written by root (the panel only reads it): the panel cannot redirect a file that root opens.
RESTORE_LOG = Path(os.environ.get("TELEPORTER_LOG", "/var/log/labtower/restore.log"))
MAX_UPLOAD = int(os.environ.get("TELEPORTER_MAX_UPLOAD", 200 * 1024 * 1024))
# Nombres de respaldo permitidos: «labtower-<texto seguro>.tar.gz» (creados por el sistema) o
# «upload-AAAAMMDD_HHMMSS.tar.gz» (subidos). Cualquier otro nombre se rechaza: evita rutas con «../».
# EN: Allowed backup names: "labtower-<safe text>.tar.gz" (created by the system) or
#     "upload-YYYYMMDD_HHMMSS.tar.gz" (uploaded). Any other name is rejected: this prevents "../" paths.
NAME_RE    = re.compile(r"^((labtower|pi-console)-[A-Za-z0-9._-]{1,80}|upload-\d{8}_\d{6})\.tar\.gz$")
# El script de restauración termina su registro con «RESULT: ok|errors|failed»; así se sabe cómo terminó.
# EN: The restore script ends its log with "RESULT: ok|errors|failed"; that is how we know how it ended.
RESULT_RE  = re.compile(r"^RESULT: (\w+)\s*$", re.M)
# Máximo de caracteres de salida que se devuelven al navegador.
# EN: Maximum number of output characters returned to the browser.
OUT_LIMIT  = 20000


# ¿El nombre cumple el patrón permitido?
# EN: Does the name match the allowed pattern?
def valid_name(name):
    return isinstance(name, str) and bool(NAME_RE.match(name))


# Ruta real de un respaldo, solo si el nombre es válido y es un archivo normal (nunca un enlace simbólico).
# EN: Real path of a backup, only if the name is valid and it is a regular file (never a symbolic link).
def path_of(name):
    """Return the spool path for a validated name (never follows symlinks)."""
    if not valid_name(name):
        return None
    p = SPOOL / name
    return p if p.is_file() and not p.is_symlink() else None


# ¿Está instalado teleporter.sh?
# EN: Is teleporter.sh installed?
def available():
    return os.path.isfile(BIN)


# Recorta la salida larga conservando el final, que es lo que suele importar.
# EN: Trim long output keeping the end, which is usually what matters.
def _tail(text, limit=OUT_LIMIT):
    return text if len(text) <= limit else "…" + text[-limit:]


# Cifrado de respaldos (gpg simétrico AES-256, el mismo formato que usa labtower-sftp-backup): un respaldo contiene hashes de contraseñas y tokens de API, así que lo
# que sale de esta máquina por el navegador va cifrado con una frase que el administrador elige. La frase viaja por una tubería (nunca en la línea de comandos).
# EN: Backup encryption (symmetric gpg AES-256, the same format labtower-sftp-backup uses): a backup holds password hashes and API tokens, so what leaves this machine
#     through the browser is encrypted with a passphrase the administrator chooses. The passphrase goes through a pipe (never on the command line).
MIN_PASSPHRASE = 12
GPG_MAGIC      = (0x8c, 0xc3, 0x84, 0x85)      # first byte of a gpg symmetric-encrypted message (old and new packet formats)

def passphrase_error(pw):
    if not isinstance(pw, str) or len(pw) < MIN_PASSPHRASE: return f"The passphrase must have at least {MIN_PASSPHRASE} characters"
    if len(pw) > 256 or re.search(r"[\x00-\x1f\x7f]", pw): return "Invalid passphrase"
    return None

def _gpg(args, passphrase):
    home = tempfile.mkdtemp(prefix="ltg-")            # short path: gpg-agent sockets have a length limit
    r, w = os.pipe()
    try:
        os.write(w, passphrase.encode() + b"\n"); os.close(w)
        cmd = ["gpg", "--homedir", home, "--batch", "--yes", "--quiet", "--no-tty", "--pinentry-mode", "loopback", "--passphrase-fd", str(r)] + args
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600, pass_fds=(r,))
        return p.returncode == 0, (p.stderr or "").strip()[:300]
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)[:300]
    finally:
        try: os.close(r)
        except OSError: pass
        subprocess.run(["gpgconf", "--homedir", home, "--kill", "gpg-agent"], capture_output=True, timeout=10)
        shutil.rmtree(home, ignore_errors=True)

# Cifra un respaldo del spool a un temporal privado y devuelve su ruta (quien llama lo borra). None + error si falla.
# EN: Encrypt a spool backup into a private temp file and return its path (the caller deletes it). None + error on failure.
def encrypt_backup(name, passphrase):
    p = path_of(name)
    if not p: return None, "Backup not found"
    err = passphrase_error(passphrase)
    if err: return None, err
    out = SPOOL / f".export-{os.getpid()}-{os.urandom(4).hex()}.gpg"
    ok, msg = _gpg(["--symmetric", "--cipher-algo", "AES256", "-o", str(out), str(p)], passphrase)
    if not ok or not out.is_file():
        out.unlink(missing_ok=True)
        return None, "Could not encrypt the backup" + (f": {msg}" if msg else "")
    os.chmod(out, 0o600)
    return out, None

# Ejecuta teleporter.sh (con sudo si hace falta) y devuelve (éxito, salida). Cubre los fallos típicos:
# tiempo agotado, script ausente o error al lanzarlo.
# EN: Run teleporter.sh (with sudo if needed) and return (success, output). Covers the typical failures:
#     timeout, missing script or error when launching it.
def run(args, sudo=False, timeout=180):
    cmd = (SUDO if sudo else []) + [BIN] + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "The operation timed out"
    except FileNotFoundError:
        return False, "teleporter.sh is not installed"
    except Exception as e:
        return False, f"Could not run teleporter.sh: {e}"
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode == 0, _tail(out.strip())


# Lista los respaldos de la carpeta de intercambio, del más nuevo al más viejo, ignorando todo lo que no tenga nombre válido.
# EN: List the backups in the exchange folder, newest first, ignoring anything without a valid name.
def list_backups():
    items = []
    try:
        for p in SPOOL.iterdir():
            if not valid_name(p.name) or p.is_symlink() or not p.is_file():
                continue
            st = p.stat()
            items.append({"name": p.name, "size": st.st_size, "mtime": int(st.st_mtime),
                          "kind": "upload" if p.name.startswith("upload-") else "backup"})
    except FileNotFoundError:
        pass
    items.sort(key=lambda i: i["mtime"], reverse=True)
    return items


# Pide a teleporter.sh crear un respaldo (como root) y lee de su salida el nombre del archivo generado.
# EN: Ask teleporter.sh to create a backup (as root) and read the generated file name from its output.
def create_backup():
    ok, out = run(["gui-backup"], sudo=True, timeout=300)
    name = None
    m = re.search(r"^BACKUP_FILE=(\S+)\s*$", out, re.M)
    if m and valid_name(m.group(1)):
        name = m.group(1)
    return ok and name is not None, name, out


# Guarda un respaldo subido, leyéndolo por bloques de 1 MB a un temporal privado (0600). Comprueba tamaño,
# que llegue completo y que empiece con la firma de gzip; solo entonces lo renombra a «upload-<fecha>».
# EN: Save an uploaded backup, reading it in 1 MB blocks into a private temp file (0600). Checks the size,
#     that it arrives complete and that it starts with the gzip signature; only then renames it to "upload-<date>".
def save_upload(rfile, length, passphrase=None):
    """Stream `length` bytes from rfile into the spool. Returns (name, error)."""
    if length <= 0:
        return None, "Empty upload"
    if length > MAX_UPLOAD:
        return None, f"File too large (limit {MAX_UPLOAD // (1024 * 1024)} MB)"
    try:
        SPOOL.mkdir(parents=True, exist_ok=True)
        os.chmod(SPOOL, 0o700)
    except OSError as e:
        return None, f"Cannot use the backup directory: {e}"
    tmp = SPOOL / f".upload-{os.getpid()}-{os.urandom(4).hex()}.tmp"   # unique per upload: two simultaneous uploads must not share a file
    got, first = 0, b""
    try:
        with open(tmp, "wb") as f:
            os.chmod(tmp, 0o600)
            while got < length:
                chunk = rfile.read(min(1 << 20, length - got))
                if not chunk:
                    break
                if not first:
                    first = chunk[:2]
                f.write(chunk)
                got += len(chunk)
        if got != length:
            tmp.unlink(missing_ok=True)
            return None, "Upload interrupted"
        if first[:1] and first[0] in GPG_MAGIC and first != b"\x1f\x8b":
            # Respaldo cifrado: se descifra con la frase indicada a otro temporal y se sigue con ese. / EN: Encrypted backup: decrypt it with the given passphrase to another temp file and go on with that one.
            if not passphrase:
                tmp.unlink(missing_ok=True)
                return None, "This backup is encrypted: enter its passphrase"
            dec = SPOOL / f".upload-{os.getpid()}-{os.urandom(4).hex()}.dec"
            ok, msg = _gpg(["--decrypt", "-o", str(dec), str(tmp)], passphrase)
            tmp.unlink(missing_ok=True)
            if not ok or not dec.is_file():
                dec.unlink(missing_ok=True)
                return None, "Could not decrypt the backup (wrong passphrase or damaged file)"
            os.chmod(dec, 0o600)
            tmp = dec
            with open(tmp, "rb") as f: first = f.read(2)
        if first != b"\x1f\x8b":
            tmp.unlink(missing_ok=True)
            return None, "Not a .tar.gz file"
        for _ in range(5):
            name = time.strftime("upload-%Y%m%d_%H%M%S.tar.gz")
            dest = SPOOL / name
            try:
                os.link(tmp, dest)            # atomic and fails if the name is taken: simultaneous uploads never overwrite each other
            except FileExistsError:
                time.sleep(1.1)
                continue
            tmp.unlink(missing_ok=True)
            return name, None
        tmp.unlink(missing_ok=True)
        return None, "Could not allocate a file name"
    except OSError as e:
        try: tmp.unlink(missing_ok=True)
        except OSError: pass
        return None, f"Could not save the upload: {e}"


# Verifica un respaldo sin cambiar nada (no necesita root).
# EN: Verify a backup without changing anything (no root needed).
def verify(name):
    p = path_of(name)
    if not p:
        return False, "Backup not found"
    return run(["check", str(p)], sudo=False, timeout=180)


# Lanza la restauración como proceso aparte. El panel se reinicia durante ella, por eso no se espera el resultado.
# EN: Start the restore as a separate process. The panel restarts during it, so the result is not awaited.
def start_restore(name):
    """Restore from the panel. NUT and nginx are never restored here (CLI only: see teleporter.sh)."""
    if not path_of(name):
        return False, "Backup not found"
    ok, out = run(["gui-restore", name, "0", "0"], sudo=True, timeout=60)
    return ok and "RESTORE_STARTED=1" in out, out


# Borra un respaldo (solo con nombre válido).
# EN: Delete a backup (only with a valid name).
def delete(name):
    p = path_of(name)
    if not p:
        return False
    try:
        p.unlink()
        return True
    except OSError:
        return False


# Estado de la última restauración leyendo restore.log: idle (nunca), running (reciente y sin resultado),
# ok / errors / failed (según el RESULT final) o failed si pasaron 15 min sin terminar.
# EN: State of the last restore read from restore.log: idle (never), running (recent and no result),
#     ok / errors / failed (from the final RESULT) or failed if 15 min passed without finishing.
def restore_status():
    log = RESTORE_LOG
    try:
        st = log.stat()
        text = log.read_text(errors="replace")
    except (FileNotFoundError, PermissionError):
        return {"state": "idle", "log": ""}
    m = RESULT_RE.findall(text)
    if m:
        state = m[-1]                      # ok | errors | failed
    elif time.time() - st.st_mtime < 900:
        state = "running"
    else:
        state = "failed"
    return {"state": state, "log": _tail(text, 8000), "mtime": int(st.st_mtime)}
