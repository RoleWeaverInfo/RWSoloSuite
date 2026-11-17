import configparser
import copy
import math
import tempfile
import unittest
from pathlib import Path

from rwstudio.authoring import blank, room, npc, validate, review
from rwstudio.layout import plan, native_tiles, center, exit_point
from rwstudio.nwn.area_tools import node
from rwstudio.nwn.game_assets import GameAssets
from rwstudio.adventure_builder import Placement
from rwstudio.floorplan_design import native_scale
from rwstudio.design_tools import area_test_project, edit_map
from rwstudio.builder import ROOT, build_project
from rwstudio.storage import Store
from test_floorplan_design import example
from test_physical_doors import triangles, contains

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

def small_plan(kind='castle'):
    p=blank();p['design_mode']='area';p['start_room']='arrival'
    a=p['areas'][0];a.update(type=kind,width=14,height=14,room_count=5)
    a['rooms']=[room('arrival','Vestibule',5,5,1,1),room('north','North alcove',5,9,1,2),
        room('south','South alcove',5,1,2,1),room('east','East chamber',9,5,2,2),room('west','West alcove',1,5,1,1)]
    p['connections']=[dict(id='pass_'+side,name='Passage '+side,from_room='arrival',to_room=side,from_side=side,
        to_side={'north':'south','south':'north','east':'west','west':'east'}[side],kind='corridor',two_way=True,requires_quest='') for side in ('north','south','east','west')]
    return p

class SmallRoomTests(unittest.TestCase):
    def test_scale_preserves_small_dimensions_and_discloses_subtile_rounding(self):
        _,p=example();p['measurements'][0].update(width_m=6,height_m=10)
        q,warnings=native_scale(p)
        self.assertEqual((q['area']['rooms'][0]['width'],q['area']['rooms'][0]['height']),(1,1))
        self.assertIn('10m tiles',warnings[0]);self.assertEqual(q['measurements'][0]['width_m'],6)

    def test_one_tile_rooms_allow_opposing_passages_and_keep_larger_doors(self):
        p=small_plan();validate(p,complete=True);layout=plan(p)['starting_area']
        self.assertEqual(len(layout['openings']),7);self.assertEqual(len(layout['doorways']),1)
        self.assertEqual(len(layout['corridors']),4)
        self.assertTrue(review(p)['ready']);self.assertTrue(any('open corridor' in s for s in review(p)['warnings']))
        for r in p['areas'][0]['rooms']:
            self.assertIn((r['x'],r['y']),layout['floor'])

    def test_resize_supports_one_tile_but_rejects_zero(self):
        p=blank();p['design_mode']='area'
        result=edit_map(p,'arrival','resize',{'width':1,'height':1})['project']
        self.assertEqual(result['areas'][0]['rooms'][0]['width'],1)
        with self.assertRaises(ValueError):edit_map(p,'arrival','resize',{'width':0,'height':1})

    def test_narrow_room_arrival_does_not_land_in_opposite_exit(self):
        r=small_plan()['areas'][0]['rooms'][0]
        for side in ('north','south','east','west'):
            self.assertEqual(exit_point(r,side,8),center(r))

    def test_compact_furnishings_and_actor_fit_without_blocking_access(self):
        p=small_plan();a=p['areas'][0];layouts=plan(p);r=a['rooms'][0]
        placement=Placement({x['id']:(a,x) for x in a['rooms']},layouts[a['id']]['openings']+layouts[a['id']]['doorways'])
        x,y=placement.take('arrival');self.assertTrue(placement.compact_clear('arrival',x,y,1))
        x,y,_=placement.furnish('arrival','chair','north');self.assertTrue(placement.compact_clear('arrival',x,y,.7))
        with self.assertRaisesRegex(ValueError,'arrival|doorway|access'):
            placement.exact('arrival','chair',dict(id='blocked',x=5,y=5,facing=0))

    @unittest.skipUnless(GAME.is_dir(),'Installed stock resources required')
    def test_generic_castle_floor_is_not_a_bath_or_water_feature(self):
        from rwstudio.layout import TILES
        assets=GameAssets(GAME);cfg=configparser.ConfigParser(strict=False)
        cfg.read_string(assets.get('tic01',2013).decode('latin1'))
        full=TILES['castle'][1]
        for section in cfg.sections():
            if section.startswith('GROUP') and cfg[section].get('name')=='Bath':
                self.assertNotIn(str(full),[v for k,v in cfg[section].items() if k.startswith('tile')])
        model=assets.get(cfg['TILE'+str(full)]['model'],2002).lower()
        self.assertIn(b'tic01_floor',model);self.assertNotIn(b'tic01_water',model)

    @unittest.skipUnless(GAME.is_dir(),'Installed stock resources required')
    def test_stock_walkmeshes_connect_small_rooms_in_every_tileset(self):
        assets=GameAssets(GAME);meshes={}
        rows=[line.split() for line in assets.get('surfacemat',2017).decode('latin1').splitlines()]
        walkable={int(row[0]) for row in rows if row and row[0].isdigit() and row[2]=='1'}
        template=node(0,Tile_ID=(4,0),Tile_Orientation=(4,0),Tile_Height=(4,0))
        for kind in ('castle','dungeon','cave','forest'):
            p=small_plan(kind);a=p['areas'][0];layout=plan(p)[a['id']];tiles=native_tiles(template,a,layout)
            cfg=configparser.ConfigParser(strict=False);cfg.read_string(assets.get(layout['tileset'],2013).decode('latin1'))
            points=[center(r) for r in a['rooms']]
            for opening in layout['openings']+layout['doorways']:
                dx,dy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[opening['side']]
                for n in range(-9,10):
                    for lateral in (-.4,0,.4):points.append((opening['x']+dx*n*.5-dy*lateral,opening['y']+dy*n*.5+dx*lateral))
            for x,y in points:
                tx,ty=int(x//10),int(y//10);t=tiles[ty*a['width']+tx][1]
                model=cfg['TILE'+str(t['Tile_ID'][1])]['model'].lower()
                if model not in meshes:meshes[model]=triangles(assets.get(model,2016),walkable)
                angle=-t['Tile_Orientation'][1]*math.pi/2;lx=x-tx*10-5;ly=y-ty*10-5
                mx=lx*math.cos(angle)-ly*math.sin(angle);my=lx*math.sin(angle)+ly*math.cos(angle)
                self.assertTrue(any(contains(tri,mx,my) for tri in meshes[model]),(kind,model,x,y))

    @unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'Installed NWN compiler required')
    def test_small_room_native_module_compiles_with_actor_and_furniture(self):
        p=small_plan();p['npcs']=[npc('guard','Guard','arrival')]
        p['furnishings']=[dict(id='seat',name='Guard seat',kind='chair',room='arrival',placement='north',description='A single seat')]
        with tempfile.TemporaryDirectory() as tmp:
            manifest=build_project(area_test_project(p,'starting_area'),Store(Path(tmp)),GAME,COMPILER)
            self.assertTrue(Path(manifest['path']).is_file())

if __name__=='__main__':unittest.main()
