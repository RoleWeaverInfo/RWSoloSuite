import copy
import json
import math
import subprocess
import tempfile
import unittest
from collections import defaultdict,deque
from pathlib import Path
from unittest.mock import Mock,patch

from tests.test_spatial_geometry import measured,triangles,supported_project,GAME,COMPILER
from tests.test_floorplan_design import example
from rwstudio.authoring import validate
from rwstudio.spatial import resolve_heights
from rwstudio.platforms import ground,stair_rect,platform_rect,entry
from rwstudio.measured_geometry import tile_meshes,path_nodes,validate_set
from rwstudio.layout import plan,center
from rwstudio.floorplan_design import analyze,validate_plan,generate_reviewed,validate_positions
from rwstudio.design_tools import area_test_project,attach_area
from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read

def dais(**kw):
    return dict(dict(id='dais',name='Throne dais',x=3.,y=17.,width=4.,depth=3.,height=.45,stair_side='south',stair_width=4.,stair_run=.9,steps=3,stair_offset=2.,requirements=[]),**kw)

def platform_project(w=10,h=20,**kw):
    p=measured(w,h);p['areas'][0]['rooms'][0]['platforms']=[dais(**kw)];return p

def height_at(tri,x,y):
    a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-9:return None
    u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
    v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
    if min(u,v,1-u-v)<-1e-7:return None
    return u*a[2]+v*b[2]+(1-u-v)*c[2]

class Platforms(unittest.TestCase):
    def test_exact_throne_platform_steps_and_continuous_walking_surface(self):
        p=platform_project();validate(p);a=p['areas'][0];meshes=tile_meshes(a,plan(p)[a['id']]);walk=triangles(meshes)
        for y,expected in ((16.,0),(16.1,0),(16.25,.075),(16.4,.15),(16.7,.30),(17.,.45),(18.8,.45)):
            heights={round(v,6) for t in walk if (v:=height_at(t,25,20+y)) is not None}
            self.assertEqual(heights,{round(expected,6)},(y,heights))
        # Actual visual treads, not a rendered slope or decorative furniture.
        visible=[tuple((floor['vertices'][i][0]+tx*10+5,floor['vertices'][i][1]+ty*10+5,floor['vertices'][i][2]) for i in face[:3]) for (tx,ty),(floor,_,_) in meshes.items() for face in floor['faces']]
        for y,z in ((16.2,.15),(16.5,.30),(16.8,.45),(18.8,.45)):
            self.assertEqual({round(v,6) for t in visible if (v:=height_at(t,25,20+y)) is not None},{z})
        # Bottom floor connects to the dais using shared 3D triangle edges.
        edges=defaultdict(list)
        for i,t in enumerate(walk):
            t=[tuple(round(n,6) for n in v) for v in t]
            for x,y in zip(t,t[1:]+t[:1]):edges[tuple(sorted((x,y)))].append(i)
        neighbors=defaultdict(set)
        for ids in edges.values():
            for i in ids:neighbors[i].update(set(ids)-{i})
        start=next(i for i,t in enumerate(walk) if height_at(t,25,25)==0)
        todo=deque([start]);seen={start}
        while todo:
            for i in neighbors[todo.popleft()]-seen:seen.add(i);todo.append(i)
        self.assertTrue(any(height_at(walk[i],25,38.8) is not None for i in seen))
        # No degenerate WOK faces, even where a sloping side tapers to zero.
        for _,_,m in meshes.values():
            self.assertEqual(len(m['vertices']),len(set(m['vertices'])))
            for f in m['faces']:
                a,b,c=[m['vertices'][i] for i in f[:3]];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
                self.assertGreater(sum((u[i]*v[(i+1)%3]-u[(i+1)%3]*v[i])**2 for i in range(3)),1e-16)

    def test_cardinal_stairs_and_raised_tile_seams(self):
        for side in ('north','east','south','west'):
            p=platform_project(20,20,x=8,y=8,width=4,depth=4,stair_side=side,stair_run=1.2,stair_width=2)
            validate(p);r=p['areas'][0]['rooms'][0];a=p['areas'][0];meshes=tile_meshes(a,plan(p)[a['id']]);walk=triangles(meshes)
            sr=stair_rect(r['platforms'][0]);x=(sr[0]+sr[2])/2;y=(sr[1]+sr[3])/2
            self.assertAlmostEqual(ground(r,x,y),.225)
            self.assertEqual({round(v,6) for t in walk if (v:=height_at(t,20+x,20+y)) is not None},{.225})
            self.assertEqual({round(v,6) for t in walk if (v:=height_at(t,30,30)) is not None},{.45})
            paths=path_nodes(meshes)
            self.assertNotEqual(paths[2,2][0],'T');self.assertNotEqual(paths[3,3][0],'T')
            self.assertTrue(any(all(abs(v[0]-28)<1e-6 for v in tri) and max(v[2] for v in tri)>.4 for tri in triangles(meshes,2)))

    def test_invalid_shapes_headroom_and_landing_are_rejected(self):
        for change in (dict(height=3.1),dict(steps=1),dict(stair_run=.1),dict(x=9),dict(stair_width=5),dict(stair_offset=0),dict(y=.9),dict(height=float('nan'))):
            with self.subTest(change=change),self.assertRaises(ValueError):validate(platform_project(**change))
        p=platform_project();p['areas'][0]['rooms'][0]['platforms'].append(dais(id='other'))
        with self.assertRaisesRegex(ValueError,'overlap'):validate(p)
        p=platform_project();p['areas'][0]['type']='forest';p['areas'][0].pop('geometry')
        with self.assertRaisesRegex(ValueError,'measured'):validate(p)

    def test_furniture_follows_platform_and_support_chains(self):
        p=supported_project();r=p['areas'][0]['rooms'][0];r['platforms']=[dais()]
        for pos in p['object_positions']:pos.update(x=5,y=18.5)
        validate_positions(p);self.assertAlmostEqual(resolve_heights(p)['desk']['z'],.45);self.assertAlmostEqual(resolve_heights(p)['paper']['z'],1.34)
        p['object_positions'][0]['x']=3.2
        with self.assertRaisesRegex(ValueError,'supporting surface|straddles'):validate_positions(p)
        for pos in p['object_positions']:pos.update(x=5,y=16.5)
        with self.assertRaisesRegex(ValueError,'platform|stairs'):validate_positions(p)
        for pos in p['object_positions']:pos.update(x=5,y=15.7)
        with self.assertRaisesRegex(ValueError,'stairs|landing'):validate_positions(p)

    def test_center_on_stairs_is_relocated_and_floor_is_not_added_twice(self):
        p=platform_project(20,20,x=8,y=10.5,width=4,depth=4,stair_run=1.2,stair_width=2)
        r=p['areas'][0]['rooms'][0];self.assertNotEqual(entry(r),(10,10));self.assertEqual(center(r),(20+entry(r)[0],20+entry(r)[1]))

    def test_flat_rug_can_meet_bottom_tread_without_blocking_the_landing(self):
        from rwstudio.platforms import check_footprint
        r=platform_project()['areas'][0]['rooms'][0]
        rug=[(4,14),(6,14),(6,16.1),(4,16.1)]
        check_footprint(r,rug,.01,.01,'rug')
        with self.assertRaisesRegex(ValueError,'stairs|landing'):check_footprint(r,rug,0,.7,'bench')
        rug[2]=(6,16.3);rug[3]=(4,16.3)
        with self.assertRaisesRegex(ValueError,'stairs'):check_footprint(r,rug,.01,.01,'rug')

    def test_coarse_path_nodes_follow_shared_edges_and_rotation(self):
        p=measured(20,20);a=p['areas'][0];nodes=path_nodes(tile_meshes(a,plan(p)[a['id']]))
        self.assertEqual({xy:nodes[xy] for xy in ((2,2),(2,3),(3,2),(3,3))},{(2,2):('H','180'),(2,3):('H','90'),(3,2):('H','270'),(3,3):('H','0')})
        self.assertEqual(nodes[0,0],('T','0'))

    def test_inference_skips_asset_search_for_generated_architecture(self):
        p,check=example();a=measured()['areas'][0];p['areas'][0]['rooms']=copy.deepcopy(a['rooms']);p['areas'][0]['geometry']=copy.deepcopy(a['geometry']);p['areas'][0]['width']=6;p['areas'][0]['height']=6
        analysis=dict(area={k:v for k,v in a.items() if k!='geometry'},connections=[],assumptions=[],measurements=[dict(room='arrival',width_m=10,height_m=20,basis='measured',evidence='Drawing dimensions')],objects=[dict(id='dais',name='Dais',room='arrival',count=1,description='Raised stone floor',search='dais',required=True),dict(id='steps',name='Stairs',room='arrival',count=1,description='Three steps',search='stairs',required=True)],platforms=[dict(dais(requirements=['dais','steps']),room='arrival')],openings=[])
        analysis['area']['rooms'][0].pop('interior',None)
        provider=Mock();provider.request.side_effect=[analysis,dict(matches=[],groups=[])];library=Mock();library.list.return_value={'assets':[]}
        result=analyze(provider,library,p,a['id'],0)['plan'];validate_plan(result)
        self.assertTrue(all(m['status']=='geometry' for m in result['matches']));library.search.assert_not_called()
        provider.reset_mock()
        with patch('rwstudio.authoring_ai.generate',side_effect=lambda provider,prepared,*args:{'proposal':copy.deepcopy(prepared)}):
            generated=generate_reviewed(provider,library,p,a['id'],result)['proposal']
        self.assertFalse(generated.get('custom_placements'));self.assertFalse(generated['furnishings']);self.assertEqual(generated['areas'][0]['rooms'][0]['platforms'][0]['height'],.45)
        target=measured();target['design_mode']='adventure'
        provider.request.assert_not_called();validate(attach_area(generated,a['id'],target)['proposal'])

    def test_editor_and_review_show_platform_controls(self):
        script="""
const fs=require('fs'),vm=require('vm'),assert=require('assert');const ctx={E:String,areaIndex:0,roomIndex:0};vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/spatial.js','utf8'),ctx);
const r=JSON.parse(process.argv[1]);const html=ctx.spatialPanel({geometry:{wall_height:5,wall_thickness:.3,corridor_width:2}},r);assert(html.includes('Number of steps'));assert(html.includes('stair_side'));assert(html.includes('removePlatform_0'));
const svg=ctx.platformOutlines({height:6},r);assert.equal((svg.match(/<rect /g)||[]).length,4);assert(svg.includes('Step 3'));
"""
        r=platform_project()['areas'][0]['rooms'][0]
        result=subprocess.run(['node','-e',script,json.dumps(r)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'Installed NWN resources required')
    def test_native_export_platform_height_entry_npc_and_aurora_format(self):
        from rwstudio.authoring import npc
        p=platform_project(20,20,x=4,y=4,width=12,depth=12,stair_width=4,stair_offset=6)
        # The arrival point, room waypoint, merchant store and nearby actors
        # occupy the raised surface in this fixture.
        n=npc('test_npc','Test NPC','arrival');p['npcs']=[n]
        p['furnishings']=[dict(id='chair',name='Chair',room='arrival',kind='chair',placement='north',description='')]
        p['object_positions']=[dict(id='chair',x=7,y=13,facing=0,z=0,support='')]
        with tempfile.TemporaryDirectory() as tmp:
            manifest=build_project(area_test_project(p,'starting_area'),Store(Path(tmp)),GAME,COMPILER)
            mod={(n,k):b for n,k,b in resources(Path(manifest['path']).read_bytes())}
            ifo=read(mod['module',2014])[1][1];self.assertAlmostEqual(ifo['Mod_Entry_Z'][1],.45)
            git=read(mod['starting_area',2023])[1][1]
            self.assertTrue(all(abs(o[1]['ZPosition'][1]-.45)<1e-6 for o in git['WaypointList'][1]))
            self.assertAlmostEqual(git['Placeable List'][1][0][1]['Z'][1],.45)
            for o in git['Creature List'][1]:
                x,y=o[1]['XPosition'][1]-20,o[1]['YPosition'][1]-20
                self.assertAlmostEqual(o[1]['ZPosition'][1],ground(p['areas'][0]['rooms'][0],x,y),places=6)
            self.assertIn(b'entry_z',mod['aw_config',2009])
            from rwstudio.custom_assets import FileArchive
            hak=FileArchive(next((Path(manifest['path']).parent/'hak').glob('*.hak')))
            tileset=read(mod['starting_area',2012])[1][1]['Tileset'][1].decode();cfg=validate_set(hak[tileset,2013])
            self.assertTrue(any(s.startswith('TILE') and cfg[s].get('PathNode')=='A' for s in cfg.sections()))

if __name__=='__main__':unittest.main()
