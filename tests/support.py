"""Ayudas comunes: carga de módulos por ruta, usuarios y sesiones de prueba, y un servidor HTTP en un hilo."""
import importlib.util, json, sys, threading, http.client
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "auth"))
import auth  # noqa: E402  (la ruta se agrega arriba)

_loaded = {}
def load(rel):
    """Importa ROOT/rel (p. ej. 'nut-monitor/server.py') con un nombre único; los guiones no sirven en `import`."""
    if rel not in _loaded:
        name = "pct_" + rel.replace("/", "_").replace("-", "_").replace(".py", "")
        spec = importlib.util.spec_from_file_location(name, ROOT / rel)
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m
        spec.loader.exec_module(m); _loaded[rel] = m
    return _loaded[rel]

def make_user(name, perms, password="Test-pass-12345"):
    """Crea (o reemplaza) un usuario y devuelve el token de una sesión nueva."""
    with auth.users_lock():
        users = auth.load_users()
        users[name] = {"password_hash": auth._hash(password), "permissions": dict(perms), "created": 1, "must_change_password": False}
        auth.save_users(users)
    return auth.create_session(name, dict(perms), auth.SESSION_TTL)

ADMIN = {"wol": "admin", "nut": "admin", "net": "admin", "pve": "admin"}
READONLY = {"wol": "readonly", "nut": "readonly", "net": "readonly", "pve": "readonly"}
NONE = {"wol": "none", "nut": "none", "net": "none", "pve": "none"}

class Server:
    """Levanta el manejador `H` de un módulo en un puerto libre, dentro de un hilo."""
    def __init__(self, handler):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), handler); self.srv.daemon_threads = True
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
    def call(self, method, path, body=None, token=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        h = {"X-Real-IP": "198.51.100.7"}; h.update(headers or {})
        if token: h["Cookie"] = "session=" + token
        data = None
        if body is not None: data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
        c.request(method, path, data, h); r = c.getresponse(); raw = r.read(); c.close()
        try: j = json.loads(raw)
        except Exception: j = raw
        return r.status, j
    def close(self): self.srv.shutdown(); self.srv.server_close()
