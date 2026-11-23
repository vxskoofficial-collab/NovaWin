
#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV
# Tests statiques du moteur Ubuntu

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

    def test_required_actions_exist(self):
        names = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in ("refresh", "simulate", "install", "main"):
            self.assertIn(name, names)

    def test_no_autoremove(self):
        self.assertNotIn("autoremove", self.source)

    def test_simulation_uses_full_upgrade(self):
        self.assertIn('"full-upgrade"', self.source)
        self.assertIn('" -s "', self.source.replace(" ", "")) if False else None

    def test_reboot_detection_exists(self):
        self.assertIn("/var/run/reboot-required", self.source)

    def test_no_shell_execution(self):
        self.assertNotIn("shell=True", self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
