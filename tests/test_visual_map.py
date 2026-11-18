import subprocess
import unittest

from rwstudio.builder import ROOT


class VisualMap(unittest.TestCase):
    def test_fixture_details_and_rotation(self):
        result = subprocess.run(['node', 'tests/fixture_map_checks.js'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_camera_and_editing_interactions(self):
        result = subprocess.run(['node', 'tests/visual_map_checks.js'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
