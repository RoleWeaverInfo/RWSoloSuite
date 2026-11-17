import configparser
import copy
import math
import tempfile
import unittest
from pathlib import Path

from rwstudio.authoring import blank, room, validate, review
from rwstudio.spatial import enable, dimensions, resolve_heights
from rwstudio.layout import plan, exit_point, TILESETS
from rwstudio.measured_geometry import tile_meshes, export, node_text
from rwstudio.native_groups import contains
from rwstudio.asset_catalog import installed, builtin_assets
from rwstudio.design_tools import area_test_project, edit_map
from rwstudio.floorplan_design import validate_positions
from rwstudio.builder import build_project, ROOT
from rwstudio.storage import Store
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

def measured(w=10,h=20):
    p=blank('measured_test','Measured room');p['design_mode']='area';a=p['areas'][0]
    a.update(width=6,height=6);a['rooms']=[room('arrival','Hall',2,2,math.ceil(w/10),math.ceil(h/10))]
    enable(a,[dict(room='arrival',width_m=w,height_m=h)]);return p

def triangles(meshes,material=4):
    return [tuple((walk['vertices'][i][0]+tx*10+5,walk['vertices'][i][1]+ty*10+5,walk['vertices'][i][2]) for i in f[:3])
            for (tx,ty),(_,_,walk) in meshes.items() for f in walk['faces'] if f[3]==material]

def supported_project():
    p=measured();p['custom_assets']=[];p['custom_placements']=[];p['asset_geometry']={};p['object_positions']=[]
    for ident,bounds in [('desk',[[-1,-.6,0],[1,.6,.9]]),('paper',[[-.2,-.15,.01],[.2,.15,.07]])]:
        aid='test_'+ident;p['custom_assets'].append(dict(id=aid,name=ident,pack='builtin',sha256='a'*64,resref='',model='test',appearance=1))
        p['custom_placements'].append(dict(id=ident,name=ident,room='arrival',asset_id=aid,description='',placement='south'))
        p['asset_geometry'][aid]=bounds;p['object_positions'].append(dict(id=ident,x=8,y=2,facing=0,z=0,support='desk' if ident=='paper' else ''))
    return p

class SpatialGeometry(unittest.TestCase):
    def test_exact_clear_dimensions_and_closed_walls_for_subtile_rooms(self):
        for w,h in [(10,20),(6,8),(8.4,13.7)]:
            p=measured(w,h);validate(p);a=p['areas'][0];meshes=tile_meshes(a,plan(p)[a['id']]);walk=triangles(meshes)
            points=[point for tri in walk for point in tri]
            self.assertAlmostEqual(max(v[0] for v in points)-min(v[0] for v in points),w)
            self.assertAlmostEqual(max(v[1] for v in points)-min(v[1] for v in points),h)
            self.assertFalse(any(contains(t,19.9,22) for t in walk))
            self.assertTrue(triangles(meshes,2))
            # Every floor edge inside a tile has shared indices, not disconnected quads.
            for floor,wall,wok in meshes.values():
                self.assertEqual(len(wok['vertices']),len(set(wok['vertices'])))
                self.assertTrue(all(-5.00001<=v[0]<=5.00001 and -5.00001<=v[1]<=5.00001 for v in wok['vertices']))

    def test_offset_doorways_are_walkable_and_other_wall_segments_stay_closed(self):
        p=measured(8,13);a=p['areas'][0];a.update(width=10,room_count=2)
        a['rooms'].append(room('other','Other',6,2,1,2));a['rooms'][1]['interior']=dict(width_m=8,depth_m=13)
        for r,side in zip(a['rooms'],('east','west')):r['openings']=[dict(side=side,offset=9,width=1.2)]
        p['connections']=[dict(id='passage',name='Passage',from_room='arrival',to_room='other',from_side='east',to_side='west',kind='corridor',two_way=True,requires_quest='')]
        validate(p);layout=plan(p)[a['id']];walk=triangles(tile_meshes(a,layout))
        for x in (27.8,28,28.2,28.5,59.8,60,60.2):
            self.assertTrue(any(contains(t,x,29) for t in walk),(x,29))
        self.assertFalse(any(contains(t,28.2,25) for t in walk))
        self.assertEqual(exit_point(a['rooms'][0],'east',0),(28,29))
        self.assertTrue(all(o['width']==1.2 for o in layout['openings']))

    def test_opening_without_destination_is_only_a_recess(self):
        p=measured();r=p['areas'][0]['rooms'][0];r['openings']=[dict(side='east',offset=15.6,width=1.2)]
        validate(p);layout=plan(p)['starting_area'];self.assertEqual(p['connections'],[])
        self.assertEqual(layout['openings'][0]['y'],35.6)
        walk=triangles(tile_meshes(p['areas'][0],layout))
        self.assertTrue(any(contains(t,30.3,35.6) for t in walk))
        self.assertFalse(any(contains(t,31,35.6) for t in walk))
        r['openings'][0]['offset']=.1
        with self.assertRaisesRegex(ValueError,'corners'):validate(p)

    def test_measured_modes_do_not_replace_native_outdoor_terrain(self):
        for kind in ('forest','desert','winter'):
            p=blank();p['design_mode']='area';a=p['areas'][0];a['type']=kind
            self.assertEqual(plan(p)[a['id']]['tileset'],TILESETS[kind])
            with self.assertRaisesRegex(ValueError,'outdoor'):enable(a)

    def test_support_height_vertical_collision_and_rotation(self):
        p=supported_project();validate(p);validate_positions(p)
        self.assertAlmostEqual(resolve_heights(p)['paper']['z'],.89)
        p['object_positions'][0]['z']=.2
        self.assertAlmostEqual(resolve_heights(p)['paper']['z'],1.09)
        p['object_positions'][1]['support']='';p['object_positions'][1]['z']=.3
        with self.assertRaisesRegex(ValueError,'overlap'):validate_positions(p)
        p=supported_project();p['object_positions'][1]['x']=10
        with self.assertRaisesRegex(ValueError,'supporting surface'):resolve_heights(p)
        p=supported_project();p['object_positions'][0]['support']='paper'
        with self.assertRaisesRegex(ValueError,'Cyclic'):resolve_heights(p)
        p=supported_project();p['object_positions'][0]['z']=5
        with self.assertRaisesRegex(ValueError,'wall height'):validate_positions(p)

    def test_rotation_and_room_bounds_are_checked_against_actual_dimensions(self):
        p=supported_project();p['custom_placements']=p['custom_placements'][:1];p['object_positions']=p['object_positions'][:1]
        p['areas'][0]['rooms'][0]['interior']['width_m']=8
        pos=p['object_positions'][0];pos.update(x=7,y=2,facing=90)
        validate_positions(p)
        pos['facing']=0
        with self.assertRaisesRegex(ValueError,'beyond the room'):validate_positions(p)
        q=edit_map(measured(),'arrival','resize',dict(width=2,height=3))['project']
        self.assertEqual(dimensions(q['areas'][0]['rooms'][0]),(20,30))

    def test_editor_renders_support_controls_and_moves_a_supported_item(self):
        import subprocess,shutil
        if not shutil.which('node'):self.skipTest('Node is required for editor checks')
        result=subprocess.run(['node','-e',r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={project:{furnishings:[],custom_placements:[{id:'desk',name:'Desk',room:'r',asset_id:'desk_mesh'},{id:'paper',name:'Paper',room:'r',asset_id:'paper_mesh'}],asset_geometry:{desk_mesh:[[0,0,0],[2,1,.9]],paper_mesh:[[0,0,0],[.2,.2,.01]]},object_positions:[{id:'desk',x:3,y:2,facing:0},{id:'paper',x:4,y:2,facing:0,z:0,support:'desk'}]},clone:o=>JSON.parse(JSON.stringify(o)),E:s=>String(s??''),areaIndex:0,roomIndex:0};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/spatial.js','utf8'),ctx);
const html=ctx.placementPanel({rooms:[{id:'r'}]});assert(html.includes('Height above support'));assert(html.includes('data-rotate'));
ctx.supportedChildren('desk',{x:3,y:2,facing:0},{x:5,y:4,facing:90});const paper=ctx.project.object_positions[1];assert.equal(paper.x,5);assert.equal(paper.y,5);assert.equal(paper.facing,90);
const geometry=ctx.spatialPanel({geometry:{wall_height:5,wall_thickness:.3,corridor_width:2}}, {name:'Room',width:1,height:2,interior:{width_m:6,depth_m:13},openings:[{side:'east',offset:9,width:1.2}]});assert(geometry.includes('Clear width'));assert(geometry.includes('Centre along wall'));
"""],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'Installed NWN resources required')
    def test_supported_item_native_z_and_rotation_survive_export(self):
        from rwstudio.model_preview import geometry
        p=measured();assets={a['appearance']:a for a in builtin_assets(str(GAME))}
        p['custom_assets']=[assets[12],assets[457]];p['custom_placements']=[];p['asset_geometry']={}
        for ident,asset in zip(('desk','paper'),p['custom_assets']):
            p['custom_placements'].append(dict(id=ident,name=ident,room='arrival',asset_id=asset['id'],description='',placement='south'))
            p['asset_geometry'][asset['id']]=geometry(installed(str(GAME)).get(asset['model'],2002))['bounds']
        p['object_positions']=[dict(id='desk',x=8,y=2,facing=0,z=0,support=''),dict(id='paper',x=7.6,y=2,facing=0,z=0,support='desk')]
        validate_positions(p)
        with tempfile.TemporaryDirectory() as tmp:
            m=build_project(area_test_project(p,'starting_area'),Store(Path(tmp)),GAME,COMPILER)
            entries={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
            git=read(entries['starting_area',2023])[1][1]
            paper=next(obj[1] for obj in git['Placeable List'][1] if obj[1]['Tag'][1]==b'paper')
            self.assertAlmostEqual(paper['Z'][1],.89,places=5)
            self.assertAlmostEqual(paper['Bearing'][1],0,places=5)

    @unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'Installed NWN resources required')
    def test_build_contains_matching_hak_set_palette_walkmeshes_and_editable_sources(self):
        p=measured(6,8);a=p['areas'][0]
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp));m=build_project(area_test_project(p,a['id']),store,GAME,COMPILER)
            folder=Path(m['path']).parent;hak=next((folder/'hak').glob('*.hak'))
            from rwstudio.custom_assets import FileArchive
            packed=FileArchive(hak)
            module={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
            ar=read(module[a['id'],2012])[1][1];ts=ar['Tileset'][1].decode()
            from rwstudio.measured_geometry import validate_set
            cfg=validate_set(packed[ts,2013])
            self.assertIn((ts+'palstd',2030),packed)
            ifo=read(module['module',2014])[1][1]
            self.assertIn(hak.stem,[h[1]['Mod_Hak'][1].decode() for h in ifo['Mod_HakList'][1]])
            for tile in ar['Tile_List'][1]:
                model=cfg['TILE'+str(tile[1]['Tile_ID'][1])]['Model'];self.assertIn((model,2002),packed);self.assertIn((model,2016),packed)
                lines=[l.strip().split() for l in packed[model,2016].decode().splitlines()]
                face_count=int(next(l[1] for l in lines if l and l[0]=='faces'))
                start=next(i for i,l in enumerate(lines) if l and l[0]=='aabb')
                leaves=[int((l[1:] if l[0]=='aabb' else l)[-1]) for l in lines[start:] if len(l) in (7,8)]
                self.assertEqual(sorted(v for v in leaves if v>=0),list(range(face_count)))
            self.assertTrue(list((folder/'geometry-source').glob('*.wok')))
            self.assertIn(b'width_m',module['aw_config',2009])

if __name__=='__main__':unittest.main()
