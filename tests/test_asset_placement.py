import subprocess
import unittest
from rwstudio.builder import ROOT


class AssetPlacementControls(unittest.TestCase):
    def test_destructive_dashboard_actions_confirm_before_dispatch(self):
        result = subprocess.run(['node', 'tests/dashboard_removal_checks.js'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_basic_and_catalog_furnishings_are_editable_in_area(self):
        result = subprocess.run(['node', 'tests/asset_placement_checks.js'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
