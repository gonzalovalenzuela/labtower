"""ES: El campo del código 2FA va dentro del formulario de acceso (también en el Resumen, donde la contraseña no está en un .field) y se quita al entrar.
EN: The 2FA code field goes inside the login form (also in the Overview, where the password is not in a .field) and is removed after a successful login."""
import pathlib
import unittest

SRC = (pathlib.Path(__file__).resolve().parent.parent / "assets" / "theme" / "theme.js").read_text()


class LoginCodeField(unittest.TestCase):
    def test_inserted_next_to_the_password_not_outside_its_form(self):
        # Without a .field wrapper the anchor is the password input itself (before: its parent, which put the field outside the card).
        self.assertIn("pw.closest('.field,.lfield,.fld')||pw;host.parentNode.insertBefore(w,host.nextSibling)", SRC)
        self.assertNotIn("||pw.parentNode;host.parentNode", SRC)

    def test_removed_after_a_successful_login(self):
        self.assertIn("if(r.ok){var e=document.getElementById('lt-code')", SRC)


if __name__ == "__main__":
    unittest.main()
