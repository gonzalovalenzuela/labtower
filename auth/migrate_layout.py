#!/usr/bin/env python3
"""
LabTower — migración al esquema con aislamiento entre módulos / migration to the module-isolation layout.

ES: Antes (< 2.1.3) todos los módulos compartían un único metrics.db. Ahora cada módulo guarda el suyo en su carpeta. Este programa
parte el metrics.db antiguo en un archivo por módulo. Lo usan postinst (al actualizar) y Teleporter (al restaurar un respaldo antiguo).
Se ejecuta SIEMPRE como un usuario sin privilegios que ya puede leer el origen (nunca como root sobre una carpeta que controla un servicio).
EN: Before (< 2.1.3) every module shared one metrics.db. Now each module keeps its own inside its folder. This program splits the old
metrics.db into one file per module. postinst (on upgrade) and Teleporter (when restoring an old backup) use it. It is ALWAYS run as an
unprivileged user that can already read the source (never as root over a folder a service controls).

    migrate_layout.py split-metrics <old metrics.db> <output folder>
"""
import os, shutil, sqlite3, sys, tempfile

# Tabla → módulo (nombre de su carpeta de datos). / Table → module (name of its data folder).
OWNERS = {
    "pi_samples":  "overview",
    "pve_samples": "proxmox-monitor",
    "nas_samples": "nas-monitor",
    "dns_samples": "dns-monitor",
    "wan_samples": "wan-monitor", "wan_speed": "wan-monitor", "wan_outages": "wan-monitor",
}
MODULES = ("overview", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor")


def _private_copy(src, tmpdir):
    """Copy the database (and its write-ahead log, if any) so it can be opened normally without ever touching the original."""
    dst = os.path.join(tmpdir, "src.db")
    shutil.copyfile(src, dst)
    if os.path.isfile(src + "-wal"): shutil.copyfile(src + "-wal", dst + "-wal")
    return dst


def split_metrics(src, outdir):
    """Write <outdir>/<module>.db for every module that has tables in `src`. Returns {module: [tables]}. Never modifies `src`."""
    src, outdir = os.path.abspath(src), os.path.abspath(outdir)
    os.makedirs(outdir, mode=0o700, exist_ok=True)
    result = {}
    old = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory(dir=outdir) as tmp:
            s = sqlite3.connect(_private_copy(src, tmp))
            try:
                if s.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("source database is damaged")
                ddl = {r[0]: r[1] for r in s.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")}
                indexes = s.execute("SELECT tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
                for mod in MODULES:
                    tables = [t for t, m in OWNERS.items() if m == mod and t in ddl]       # names come from OWNERS, never from the file
                    if not tables: continue
                    path = os.path.join(outdir, mod + ".db")
                    for ext in ("", "-wal", "-shm", "-journal"):
                        try: os.unlink(path + ext)
                        except FileNotFoundError: pass
                    d = sqlite3.connect(path)
                    try:
                        d.execute("PRAGMA journal_mode=DELETE")
                        for t in tables: d.execute(ddl[t])
                        for tbl, sql in indexes:
                            if tbl in tables: d.execute(sql)
                        for t in tables:
                            cur = s.execute(f"SELECT * FROM {t}")
                            marks = ",".join("?" * len(cur.description))
                            while True:
                                rows = cur.fetchmany(5000)
                                if not rows: break
                                d.executemany(f"INSERT INTO {t} VALUES ({marks})", rows)
                        d.commit()
                    finally:
                        d.close()
                    os.chmod(path, 0o600)
                    result[mod] = tables
            finally:
                s.close()
    finally:
        os.umask(old)
    return result


def main(argv):
    if len(argv) == 4 and argv[1] == "split-metrics":
        try: res = split_metrics(argv[2], argv[3])
        except Exception as e:
            print(f"error: {e}", file=sys.stderr); return 1
        for m, t in res.items(): print(f"{m}: {', '.join(t)}")
        return 0
    print(__doc__, file=sys.stderr); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
