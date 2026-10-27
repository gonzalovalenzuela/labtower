# Pruebas de LabTower. Solo biblioteca estándar: `python3 -m unittest discover -s tests -t . -v` desde la raíz del repo.
# Antes de importar nada se apunta todo el estado (usuarios, sesiones, datos de módulos) a una carpeta temporal, así que no se toca /var/lib/labtower.
# EN: LabTower tests. Standard library only: `python3 -m unittest discover -s tests -t . -v` from the repo root.
#     Before anything is imported all state (users, sessions, module data) is pointed at a temporary folder, so /var/lib/labtower is never touched.
import os, tempfile, atexit, shutil, logging
logging.disable(logging.WARNING)       # los módulos registran cada petición y aviso; las pruebas solo muestran errores
TMP = tempfile.mkdtemp(prefix="labtower-tests-")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["LABTOWER_USERS"] = os.path.join(TMP, "users.json")
os.environ["LABTOWER_SESSIONS"] = os.path.join(TMP, "sessions.json")
os.environ.setdefault("NET_NO_SCAN", "1")
