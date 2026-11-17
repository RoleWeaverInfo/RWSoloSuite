import configparser
import unittest
from pathlib import Path

from rwstudio.measured_geometry import serialize_set, validate_set, export
from rwstudio.asset_catalog import installed
from rwstudio.authoring import blank
from rwstudio.spatial import enable
from rwstudio.layout import plan

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')


def extended_tileset():
    cfg=configparser.ConfigParser();cfg.optionxform=str
    cfg['GENERAL']={'Name':'testset','Type':'SET','Version':'V1.0'}
    for section in ('TERRAIN TYPES','CROSSER TYPES','PRIMARY RULES','SECONDARY RULES'):
        cfg[section]={'Count':'0'}
    cfg['TILES']={'Count':'2'}
    cfg['TILE0']={'Model':'existing','Doors':'1','Sounds':'0'}
    cfg['TILE0DOOR0']={'Type':'0'}
    cfg['GROUPS']={'Count':'1'}
    cfg['GROUP0']={'Name':'Existing group','Rows':'1','Columns':'1','Tile0':'0'}
    # Reproduce the crash regression: ConfigParser appends a new tile at EOF.
    cfg['TILE1']={'Model':'generated','Doors':'0','Sounds':'0'}
    return cfg


class TilesetSerialization(unittest.TestCase):
    def test_new_tiles_precede_groups_and_subsections_stay_with_their_tile(self):
        cfg=extended_tileset();raw=serialize_set(cfg);parsed=validate_set(raw)
        self.assertEqual(parsed.sections()[-5:],['TILE0','TILE0DOOR0','TILE1','GROUPS','GROUP0'])
        self.assertEqual(parsed['TILE1']['Model'],'generated')
        self.assertEqual(cfg.sections()[-1],'TILE1')  # serializer does not mutate input
        self.assertTrue(raw.endswith(b'\r\n'))
        self.assertNotIn(b'\n',raw.replace(b'\r\n',b''))

    def test_ordinary_ini_parser_accepts_the_crashing_order_but_guard_rejects_it(self):
        import io
        out=io.StringIO();extended_tileset().write(out)
        raw=out.getvalue().replace('\n','\r\n').encode()
        ordinary=configparser.ConfigParser();ordinary.read_string(raw.decode())
        self.assertEqual(ordinary['TILES']['count'],'2')
        self.assertEqual(ordinary['TILE1']['model'],'generated')
        with self.assertRaisesRegex(ValueError,'out of order'):validate_set(raw)

    def test_line_endings_and_missing_final_newline_are_rejected(self):
        raw=serialize_set(extended_tileset())
        for invalid in (raw.replace(b'\r\n',b'\n'),raw.rstrip(b'\r\n'),raw.replace(b'\r\n',b'\n',1)):
            with self.assertRaisesRegex(ValueError,'CRLF'):validate_set(invalid)

    def test_bad_counts_fail_before_a_hak_is_written(self):
        for section,key,value in [('TILES','Count','3'),('TILES','Count','1'),('TILE0','Doors','2'),('GROUPS','Count','0')]:
            cfg=extended_tileset();cfg[section][key]=value
            with self.assertRaisesRegex(ValueError,'counts do not match'):serialize_set(cfg)

    @unittest.skipUnless(GAME.is_dir(),'Installed NWN resources required')
    def test_real_castle_dungeon_and_cave_exports_follow_aurora_section_order(self):
        game=installed(str(GAME))
        for kind in ('castle','dungeon','cave'):
            with self.subTest(kind=kind):
                p=blank();p['design_mode']='area';a=p['areas'][0];a.update(type=kind,width=6,height=6)
                a['rooms'][0].update(x=2,y=2,width=1,height=2)
                enable(a)
                generated,layout=export(a,plan(p)[a['id']],game,'format-test')
                cfg=validate_set(generated[layout['tileset'],2013])
                names=cfg.sections();self.assertLess(names.index('TILE'+str(int(cfg['TILES']['Count'])-1)),names.index('GROUPS'))
                self.assertEqual(names[-1],'GROUP'+str(int(cfg['GROUPS']['Count'])-1))


if __name__=='__main__':unittest.main()
