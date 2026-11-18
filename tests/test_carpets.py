import copy,json,math,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch

from tests.test_spatial_geometry import measured,GAME,COMPILER
from tests.test_platforms import dais,platform_project
from tests.test_floorplan_design import PNG
from rwstudio.authoring import validate
from rwstudio.carpets import tile_meshes,texture,LIFT
from rwstudio.layout import plan
from rwstudio.measured_geometry import export,validate_set
from rwstudio.asset_catalog import installed
from rwstudio.floorplan_design import analyze,generate_reviewed
from rwstudio.design_tools import area_test_project,attach_area
from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources
from rwstudio.custom_assets import FileArchive

def runner(**values):
    return dict(dict(id='runner',name='Audience runner',x=4.,y=2.,width=2.,depth=14.1,color='red',border='none',requirements=[]),**values)

def carpet_project(**values):
    p=platform_project();p['areas'][0]['rooms'][0]['carpets']=[runner(**values)];return p

def points(meshes):
    return [(vx+tx*10+5,vy+ty*10+5,vz) for (tx,ty),colors in meshes.items() for m in colors.values() for vx,vy,vz in m['vertices']]

def mesh_area(m):
    return sum(abs((m['vertices'][b][0]-m['vertices'][a][0])*(m['vertices'][c][1]-m['vertices'][a][1])-(m['vertices'][b][1]-m['vertices'][a][1])*(m['vertices'][c][0]-m['vertices'][a][0]))/2 for a,b,c,_ in m['faces'])

class Carpets(unittest.TestCase):
    def test_full_runner_matches_plan_and_uvs_remain_continuous_across_tiles(self):
        p=carpet_project();validate(p);meshes=tile_meshes(p['areas'][0]);vs=points(meshes)
        self.assertEqual(set(meshes),{(2,2),(2,3)})
        self.assertEqual((min(v[0] for v in vs),max(v[0] for v in vs)),(24,26))
        self.assertEqual((min(v[1] for v in vs),max(v[1] for v in vs)),(22,36.1))
        self.assertTrue(all(v[2]==LIFT for v in vs))
        self.assertAlmostEqual(sum(mesh_area(m) for cs in meshes.values() for m in cs.values()),28.2)
        for (tx,ty),cs in meshes.items():
            for m in cs.values():
                for (x,y,z),(u,v,_) in zip(m['vertices'],m['uv']):
                    self.assertTrue(-5<=x<=5 and -5<=y<=5)
                    self.assertAlmostEqual(u,(x+tx*10+5)*4);self.assertAlmostEqual(v,(y+ty*10+5)*4)

    def test_border_keeps_requested_total_size_and_does_not_repeat_inside(self):
        p=carpet_project(border='gold');meshes=tile_meshes(p['areas'][0])
        by_color={color:sum(mesh_area(cs[color]) for cs in meshes.values() if color in cs) for color in ('red','gold')}
        self.assertAlmostEqual(sum(by_color.values()),28.2)
        self.assertAlmostEqual(by_color['red'],(2-.16)*(14.1-.16))

    def test_red_texture_has_native_tga_header_opaque_pixels_and_red_fibres(self):
        raw=texture('red');self.assertEqual(len(raw),18+64*64*4);self.assertEqual(raw[2],2);self.assertEqual(raw[12:18],bytes([64,0,64,0,32,40]))
        pixels=list(zip(*[iter(raw[18:])]*4));self.assertTrue(all(r>g*3 and r>b*3 and a==255 for b,g,r,a in pixels))
        self.assertGreater(len(set(pixels)),3)

    def test_carpets_on_platforms_follow_height_but_cannot_cross_edges_or_steps(self):
        p=carpet_project(x=3.5,y=17.5,width=3,depth=2);validate(p)
        self.assertTrue(all(abs(v[2]-(.45+LIFT))<1e-6 for v in points(tile_meshes(p['areas'][0]))))
        for change in (dict(depth=15),dict(x=9),dict(width=0),dict(x=float('nan')),dict(x=2,y=18,width=4,depth=1)):
            with self.subTest(change=change),self.assertRaises(ValueError):validate(carpet_project(**change))
        p=carpet_project();p['areas'][0]['rooms'][0]['carpets'].append(runner(id='duplicate'))
        with self.assertRaisesRegex(ValueError,'overlap'):validate(p)

    def test_floorplan_uses_measured_textile_without_furniture_substitution(self):
        p=measured();a=p['areas'][0];a['references']=[dict(name='Hall',notes='A long red runner',data_url=PNG)]
        area=copy.deepcopy(a);area.pop('references');area.pop('geometry');area['rooms'][0].pop('interior')
        analysis=dict(area=area,connections=[],assumptions=[],measurements=[dict(room='arrival',width_m=10,height_m=20,basis='measured',evidence='Dimension labels')],objects=[dict(id='runner',name='Runner',room='arrival',count=1,description='2 x 14.1 m red textile',search='red carpet',required=True)],carpets=[dict(runner(requirements=['runner']),room='arrival')],platforms=[],openings=[])
        provider=Mock();provider.request.side_effect=[analysis,dict(matches=[],groups=[])];library=Mock();library.list.return_value={'assets':[]}
        result=analyze(provider,library,p,a['id'],0)['plan'];library.search.assert_not_called()
        self.assertEqual(result['matches'][0]['status'],'geometry');self.assertIn('textile',result['matches'][0]['reason'])
        provider.reset_mock();provider.request.side_effect=None
        with patch('rwstudio.authoring_ai.generate',side_effect=lambda provider,prepared,*args:{'proposal':copy.deepcopy(prepared)}):
            generated=generate_reviewed(provider,library,p,a['id'],result)['proposal']
        provider.request.assert_not_called();self.assertFalse(generated['furnishings']);self.assertFalse(generated.get('custom_placements'))
        self.assertEqual(generated['areas'][0]['rooms'][0]['carpets'][0]['depth'],14.1)
        target=measured();target.update(id='destination',design_mode='adventure');validate(attach_area(generated,a['id'],target)['proposal'])

    def test_editor_and_floorplan_review_expose_size_and_color(self):
        script=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');let html='';const buttons={};let plan;
const ctx={E:String,areaIndex:0,roomIndex:0,foldAttributes:()=>'',app:{authoring_catalog:{furnishings:[]}},modal:s=>html=s,document:{querySelectorAll:()=>[]},$:s=>buttons[s]??={},clone:o=>JSON.parse(JSON.stringify(o))};vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/spatial.js','utf8'),ctx);vm.runInContext(fs.readFileSync('web/design.js','utf8'),ctx);
const p=JSON.parse(process.argv[1]),a=p.areas[0],r=a.rooms[0];const controls=ctx.spatialPanel(a,r);assert(controls.includes('Carpets and runners'));assert(controls.includes('14.1'));assert(controls.includes('removeCarpet_0'));assert(controls.includes('carpets.0.color'));
const svg=ctx.carpetOutlines(a,r);assert(svg.includes('fill="#8e161e"'));assert(svg.includes('height="1.41"'));
ctx.showReferenceChecklist({area:a,measurements:[],objects:[],matches:[],assets:[],assumptions:[]},a.id);assert(html.includes('data-plan-carpet="0.0.width"'));assert(html.includes('14.1'));
"""
        result=subprocess.run(['node','-e',script,json.dumps(carpet_project())],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(GAME.is_dir(),'Installed NWN resources required')
    def test_carpet_changes_visible_geometry_without_altering_walkmesh_or_set_format(self):
        p=carpet_project(border='gold');a=p['areas'][0];layout=plan(p)[a['id']];game=installed(str(GAME))
        with_carpet,info=export(a,layout,game,'carpet_test');without=copy.deepcopy(a);without['rooms'][0].pop('carpets');baseline,_=export(without,layout,game,'carpet_test')
        for key,raw in baseline.items():
            if key[1]==2016:self.assertEqual(raw,with_carpet[key])
        validate_set(with_carpet[info['tileset'],2013])
        nodes=[raw.decode() for (name,kind),raw in with_carpet.items() if kind==2002 and b'carpet_red' in raw]
        self.assertEqual(len(nodes),2)
        self.assertTrue(all('shadow 0' in s and 'tilefade 0' in s for s in nodes))
        for s in nodes:
            for line in s.splitlines():
                if line.strip().startswith('bitmap '):self.assertIn((line.split()[1],3),with_carpet)

    @unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'Installed NWN resources required')
    def test_native_module_share_contains_carpet_mesh_and_red_texture(self):
        import zipfile
        p=carpet_project();a=p['areas'][0]
        with tempfile.TemporaryDirectory() as tmp:
            m=build_project(area_test_project(p,a['id']),Store(Path(tmp)),GAME,COMPILER);folder=Path(m['path']).parent
            hak=FileArchive(next((folder/'hak').glob('*.hak')))
            mod={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())};ar=read(mod[a['id'],2012])[1][1];ts=ar['Tileset'][1].decode();cfg=validate_set(hak[ts,2013])
            found=[]
            for tile in ar['Tile_List'][1]:
                raw=hak[cfg['TILE'+str(tile[1]['Tile_ID'][1])]['Model'],2002]
                if b'carpet_red' in raw:found.append(raw)
            self.assertEqual(len(found),2);self.assertEqual(hak[ts+'c0',3],texture('red'))
            with zipfile.ZipFile(next(folder.glob('*-aurora.zip'))) as z:
                self.assertTrue(any(n.endswith(ts+'c0.tga') and n.startswith('geometry-source/') for n in z.namelist()))

if __name__=='__main__':unittest.main()
