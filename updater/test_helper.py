
#!/usr/bin/env python3

import ast
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).parent
HELPER = BASE_DIR / "helper.py"


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
        for name in ("refresh", "simulate", "install", "main"):
            self.assertIn(name, names)

    def test_apt_update_exists(self):
        self.assertIn('"update"', self.source)

    def test_full_upgrade_simulation_exists(self):
        self.assertIn('"apt-get", "-s", "full-upgrade"', self.source)

    def test_full_upgrade_install_exists(self):
        self.assertIn('"apt-get", "full-upgrade", "-y"', self.source)

    def test_autoremove_is_not_used(self):
        self.assertNotIn("autoremove", self.source)

    def test_removals_are_checked(self):
        self.assertIn("if removals:", self.source)

    def test_reboot_detection_exists(self):
        self.assertIn("/var/run/reboot-required", self.source)

    def test_shell_true_is_not_used(self):
        self.assertNotIn("shell=True", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
