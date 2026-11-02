import unittest
from unittest.mock import patch

from tools import start_app


class LauncherTests(unittest.TestCase):
    def test_reuses_only_beta_project_intelligence(self):
        with patch.object(start_app, "health", return_value={"app": "beta-project-intelligence"}), \
             patch.object(start_app, "open_standalone") as open_app, \
             patch.object(start_app.subprocess, "Popen") as spawn:
            self.assertEqual(start_app.main(), 0)
            open_app.assert_called_once_with()
            spawn.assert_not_called()

    def test_refuses_to_open_another_apps_port(self):
        with patch.object(start_app, "health", return_value={"app": "keycore-hub"}), \
             patch.object(start_app, "port_is_open", return_value=True), \
             patch.object(start_app, "open_standalone") as open_app, \
             patch.object(start_app.subprocess, "Popen") as spawn:
            self.assertEqual(start_app.main(), 1)
            open_app.assert_not_called()
            spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
