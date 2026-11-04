#!/usr/bin/env python3
"""labtower-resetpw — reset the password of a LabTower user from the console (no login needed).

Runs as the authentication user (labtower-auth), started by /usr/local/bin/labtower-resetpw, with the same code the Admin Panel uses:
the new password is hashed the same way, every session of that account is closed, the login brakes are cleared and the audit log records it.
ES: Restablece la contraseña de un usuario desde la consola. Por defecto es aleatoria y obliga a cambiarla en el próximo inicio de sesión.
"""
from __future__ import annotations  # permite «X | None» en Python 3.9 / allows «X | None» on Python 3.9
import argparse, getpass, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auth  # noqa: E402


def reset(username: str, password: str | None = None, keep_2fa: bool = True, must_change: bool = True):
    """Set the password (random if None). Returns (password, notes). Raises KeyError if the user does not exist, ValueError if the password is weak."""
    notes = []
    if password is None: password = auth._random_password()
    else:
        err = auth.password_error(password, username)
        if err: raise ValueError(err)
        password = password.strip()
    with auth.users_lock():
        users = auth.load_users()
        if username not in users: raise KeyError(username)
        users[username]["password_hash"] = auth._hash(password)
        users[username]["must_change_password"] = bool(must_change)
        if not keep_2fa and (users[username].get("totp") or users[username].get("totp_pending")):
            users[username].pop("totp", None); users[username].pop("totp_pending", None)
            notes.append("2FA disabled")
        auth.save_users(users)
    auth.delete_user_sessions(username)
    for key in ("u:" + username, "pw:" + username): auth.throttle_clear(key)
    if username == "admin": auth.clear_initial_password()
    auth.audit("console", "password_reset", username, "labtower-resetpw" + (" (2FA disabled)" if notes else ""), "local")
    return password, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="labtower-resetpw", description="Reset the password of a LabTower user.")
    ap.add_argument("user", nargs="?", default="admin", help="user name (default: admin)")
    ap.add_argument("--list", action="store_true", help="list the users and exit")
    ap.add_argument("--ask", action="store_true", help="type the new password instead of generating a random one")
    ap.add_argument("--disable-2fa", action="store_true", help="also turn off two-factor authentication for that user (lost phone)")
    ap.add_argument("--no-change", action="store_true", help="do not force a password change at the next login (only with --ask)")
    a = ap.parse_args(argv)
    users = auth.load_users()
    if a.list:
        for n in sorted(users): print(f"{n}{'  (2FA on)' if users[n].get('totp') else ''}")
        return 0
    if a.user not in users:
        print(f"labtower-resetpw: user '{a.user}' does not exist. Users: {', '.join(sorted(users)) or '(none)'}", file=sys.stderr)
        return 1
    pw = None
    if a.ask:
        pw = getpass.getpass("New password: ")
        if pw != getpass.getpass("Repeat it: "):
            print("labtower-resetpw: the passwords do not match", file=sys.stderr); return 1
    elif a.no_change:
        print("labtower-resetpw: --no-change only makes sense with --ask", file=sys.stderr); return 1
    try: pw, notes = reset(a.user, pw, keep_2fa=not a.disable_2fa, must_change=not (a.ask and a.no_change))
    except ValueError as e:
        print(f"labtower-resetpw: {e}", file=sys.stderr); return 1
    print(f"Password of '{a.user}' reset. All its sessions were closed and its login lock was cleared." + (" " + "; ".join(notes) + "." if notes else ""))
    if not a.ask:
        print(f"New password: {pw}")
        print("It must be changed at the next login.")
    elif not a.no_change:
        print("It must be changed at the next login.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
