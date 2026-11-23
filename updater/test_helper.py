
#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV - Tests statiques

import ast
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).parent
HELPER = BASE_DIR / "helper.py"
APP = BASE_DIR / "app.py"


class HelperTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = HELPER.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_python_syntax(self):
        self.assertIsNotNone(self.tree)

    def test_required_functions(self):
        names = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, ast.FunctionDef)
        }

        for name in (
            "refresh",
            "simulate",
            "install",
            "main",
            "get_simulation",
            "save_plan"
        ):
            with self.subTest(function=name):
                self.assertIn(name, names)

    def test_apt_update_exists(self):
        self.assertIn('"apt-get", "update"', self.source)

    def test_full_upgrade_simulation_exists(self):
        self.assertIn(
            '"apt-get", "-s", "full-upgrade"',
            self.source
        )

    def test_full_upgrade_install_exists(self):
        self.assertIn(
            '"apt-get", "full-upgrade", "-y"',
            self.source
        )

    def test_autoremove_is_not_used(self):
        self.assertNotIn("autoremove", self.source)

    def test_package_removals_are_blocked(self):
        self.assertIn('line.startswith("Remv ")', self.source)
        self.assertIn("if removals:", self.source)

    def test_plan_identifier_is_generated(self):
        self.assertIn("secrets.token_urlsafe(32)", self.source)

    def test_plan_expiration_exists(self):
        self.assertIn("PLAN_LIFETIME = 300", self.source)
        self.assertIn("plan_file.unlink(missing_ok=True)", self.source)

    def test_plan_hash_is_verified(self):
        self.assertIn("hashlib.sha256", self.source)
        self.assertIn("current_hash != plan.get", self.source)

    def test_plan_is_required_for_installation(self):
        self.assertIn("elif action == \"install\" and len(sys.argv) == 3:", self.source)
        self.assertIn("install(sys.argv[2])", self.source)

    def test_reboot_detection_exists(self):
        self.assertIn("/var/run/reboot-required", self.source)

    def test_shell_true_is_not_used(self):
        self.assertNotIn("shell=True", self.source)

    def test_plan_directory_is_restricted(self):
        self.assertIn("os.chmod(PLAN_DIR, 0o700)", self.source)


class AppTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_app_python_syntax(self):
        self.assertIsNotNone(self.tree)

    def test_confirmation_dialog_exists(self):
        self.assertIn("Gtk.AlertDialog", self.source)

    def test_plan_id_is_passed_to_helper(self):
        self.assertIn('self.run_helper(\n            "install",\n            [plan_id]', self.source)

    def test_install_requires_plan_id(self):
        self.assertIn("if not self.plan_id:", self.source)

    def test_install_button_starts_disabled(self):
        self.assertIn("self.install_button.set_sensitive(False)", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
