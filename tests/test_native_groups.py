import configparser
import copy
import math
import tempfile
import unittest
from pathlib import Path

from rwstudio.native_groups import catalog,apply,rotated,point_test,prepare_navigation,verify_installed,walk_triangles,contains
from rwstudio.asset_catalog import installed
from rwstudio.authoring import blank,room,validate
from rwstudio.layout import TILESETS,plan,native_tiles,center
from rwstudio.nwn.area_tools import node
from rwstudio.adventure_builder import Placement
from rwstudio.design_tools import area_test_project
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'
TEMPLATE=node(0,Tile_ID=(4,0),Tile_Orientation=(4,0),Tile_Height=(4,0))

def bedroom():
    p=blank();p['design_mode']='area';a=p['areas'][0];a.update(width=12,height=12,room_count=2)
    a['rooms']=[room('arrival','Bedroom',3,3,1,2),room('hall','Hall',3,8,2,2)]
    p['connections']=[dict(id='passage',name='Passage',from_room='arrival',to_room='hall',from_side='north',to_side='south',kind='corridor',two_way=True,requires_quest='')]
    return apply(p,'arrival',next(g for g in catalog(str(GAME),'tic01') if g['name']=='Bedroom01_1x2'))['project']

@unittest.skipUnless(GAME.is_dir(),'Installed native tilesets required')
class NativeGroups(unittest.TestCase):
    def test_each_environment_has_compatible_and_explicitly_unsupported_groups(self):
        for kind,ts in TILESETS.items():
            groups=catalog(str(GAME),ts)
            self.assertTrue(any(g['mode']!='unsupported' for g in groups),kind)
            self.assertTrue(any(g['mode']=='unsupported' for g in groups),kind)
            for g in groups:
                if -1 in g['tiles']:self.assertEqual(g['mode'],'unsupported')

    def test_rotations_preserve_entire_group_and_its_door_side(self):
        g=next(g for g in catalog(str(GAME),'tic01') if g['name']=='Bedroom01_1x2')
        for rot,side in enumerate(('north','west','south','east')):
            p=blank();p['design_mode']='area';p=apply(p,'arrival',g,rot)['project'];a=p['areas'][0];r=a['rooms'][0]
            record=r['native_group'];shape=rotated(record);self.assertEqual(shape['ports'][0]['side'],side)
            layout=plan(p)[a['id']];tiles=native_tiles(TEMPLATE,a,layout)
            for t in shape['tiles']:
                actual=tiles[(r['y']+t['y'])*a['width']+r['x']+t['x']][1]
                self.assertEqual((actual['Tile_ID'][1],actual['Tile_Orientation'][1]),(t['id'],rot))
            nav=prepare_navigation(p,GAME);x,y=center(r);self.assertTrue(nav[r['id']](x,y))

    def test_native_group_door_has_walkable_seam_into_generated_corridor(self):
        p=bedroom();a=p['areas'][0];layout=plan(p)[a['id']];tiles=native_tiles(TEMPLATE,a,layout)
        cfg=configparser.ConfigParser(strict=False);cfg.read_string(installed(str(GAME)).get('tic01',2013).decode('latin1'))
        for d in layout['doorways']:
            dx,dy={'north':(0,1),'south':(0,-1),'east':(1,0),'west':(-1,0)}[d['side']]
            for n in range(-6,7):
                for lateral in (-.4,0,.4):
                    x,y=d['x']+dx*n*.25-dy*lateral,d['y']+dy*n*.25+dx*lateral;tx,ty=int(x//10),int(y//10)
                    tile=tiles[ty*a['width']+tx][1];angle=-tile['Tile_Orientation'][1]*math.pi/2;lx,ly=x-tx*10-5,y-ty*10-5
                    mx,my=lx*math.cos(angle)-ly*math.sin(angle),lx*math.sin(angle)+ly*math.cos(angle)
                    model=cfg['TILE'+str(tile['Tile_ID'][1])]['model']
                    self.assertTrue(any(contains(t,mx,my) for t in walk_triangles(str(GAME),model)),(d['room'],model,x,y))

    def test_wrong_size_tileset_door_and_forged_stamp_are_rejected(self):
        p=bedroom();p['areas'][0]['rooms'][0]['width']=2
        with self.assertRaisesRegex(ValueError,'stretched'):validate(p)
        p=bedroom();p['connections'][0]['from_side']='east'
        with self.assertRaisesRegex(ValueError,'doorway'):plan(p)
        p=bedroom();p['areas'][0]['type']='cave'
        with self.assertRaisesRegex(ValueError,'tileset'):validate(p)
        p=bedroom();p['areas'][0]['rooms'][0]['native_group']['definition']['tiles'][0]=175
        with self.assertRaisesRegex(ValueError,'differs'):verify_installed(p,GAME)

    def test_cave_and_outdoor_feature_arrivals_avoid_native_obstacles(self):
        for kind,name in [('cave','Pillar01'),('forest','Ruin'),('desert','Ruin'),('winter','Crystal')]:
            p=blank();p['design_mode']='area';p['areas'][0]['type']=kind
            group=next(g for g in catalog(str(GAME),TILESETS[kind]) if g['name']==name)
            p=apply(p,'arrival',group)['project'];nav=prepare_navigation(p,GAME);a=p['areas'][0];r=a['rooms'][0];x,y=center(r)
            self.assertTrue(nav['arrival'](x,y));native_tiles(TEMPLATE,a,plan(p)[a['id']])
            placement=Placement({'arrival':(a,r)},navigation=nav)
            # A footprint filling the tile necessarily intersects its native feature.
            with self.assertRaises(ValueError):placement.exact('arrival','table',dict(id='bad',x=5,y=5,facing=0),[[-4,-4,0],[4,4,1]])

    @unittest.skipUnless(COMPILER.is_file(),'Installed compiler required')
    def test_native_group_compiles_and_exported_project_remains_editable(self):
        p=bedroom()
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp));m=build_project(area_test_project(p,'starting_area'),store,GAME,COMPILER)
            saved=store.built_project(m['build_id']);validate(saved);self.assertNotIn('_entry_point',saved['areas'][0]['rooms'][0])
            res={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
            tiles=read(res['starting_area',2012])[1][1]['Tile_List'][1]
            self.assertEqual(tiles[3*12+3][1]['Tile_ID'][1],43);self.assertEqual(tiles[4*12+3][1]['Tile_ID'][1],42)
            self.assertIn(b'entry_x',res['aw_config',2009]);self.assertTrue(res['aw_beat',2010])

if __name__=='__main__':unittest.main()
