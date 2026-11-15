import unittest
from pathlib import Path
from rwstudio.inventory_icons import icon_catalog
from rwstudio.nwn.game_assets import GameAssets

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')

@unittest.skipUnless(GAME.exists(),'Installed game assets required')
class InventoryIconTests(unittest.TestCase):
    def test_inventory_icons_resolve_to_installed_textures(self):
        game=GameAssets(GAME);icons=icon_catalog(game)
        self.assertGreater(len(icons),50)
        self.assertTrue(icons[49].startswith('iit_potion'))
        for base,icon in icons.items():
            with self.subTest(base=base,icon=icon):
                self.assertTrue((icon,3) in game.index or (icon,2033) in game.index)
                self.assertLessEqual(len(icon),16)
