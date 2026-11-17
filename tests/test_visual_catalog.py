import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

from rwstudio.asset_catalog import builtin_assets,detail,model_bytes,visual_evidence
from rwstudio.custom_assets import AssetLibrary
from rwstudio.model_preview import geometry,contact_sheet
from rwstudio.authoring import blank,room,validate
from rwstudio.design_tools import attach_area,area_test_project
from rwstudio.adventure_builder import Placement
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

class MeshTests(unittest.TestCase):
    def test_ascii_parent_translation_and_hidden_collision_mesh(self):
        raw=b'''newmodel test
beginmodelgeom test
node dummy root
 parent NULL
 position 3 2 1
endnode
node trimesh visible
 parent root
 position 1 0 0
 verts 3
 0 0 0
 2 0 0
 0 1 0
 faces 1
 0 1 2 0 0 0 0 1
endnode
node aabb collision
 parent root
 verts 3
 -100 0 0
 100 0 0
 0 100 0
 faces 1
 0 1 2 0 0 0 0 1
endnode
endmodelgeom test'''
        mesh=geometry(raw)
        self.assertEqual(mesh['bounds'],[[4,2,1],[6,3,1]])
        self.assertEqual(len(mesh['faces']),1)
        self.assertTrue(contact_sheet([mesh]).startswith(b'\x89PNG'))

    def test_corrupt_offsets_and_nonfinite_vertices_fail_closed(self):
        with self.assertRaises(ValueError):geometry(b'\0'*20)
        with self.assertRaises(ValueError):geometry(b'node trimesh x\nverts 3\nnan 0 0\n1 0 0\n0 1 0\nfaces 1\n0 1 2\nendnode')

@unittest.skipUnless(GAME.is_dir(),'Installed NWN assets required')
class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.library=AssetLibrary(Path(self.tmp.name),str(GAME))

    def test_complete_installed_placeables_and_real_sizes(self):
        catalog=self.library.list();self.assertGreater(catalog['builtin_count'],200)
        for ident,label in ((183,'Throne'),(178,'Bench'),(57,'Brazier'),(105,'WeaponRack')):
            a=next(a for a in catalog['assets'] if a['id']=='builtin_ap'+str(ident));self.assertIn(label,a['name'])
            info,mesh=detail(self.library,a['id']);self.assertTrue(info['available']);self.assertGreater(len(mesh['faces']),5)
        self.assertEqual(detail(self.library,'builtin_ap178')[0]['dimensions'][:2],[1.9,.56])
        self.assertTrue(any(a['id']=='builtin_ap183' for a in self.library.search('throne',6)))
        self.assertEqual(self.library.search('high backed throne red gold',8,focus='South Facing Throne')[0]['id'],'builtin_ap183')
        self.assertTrue(any('pillar' in a['name'].lower() for a in self.library.search('stone columns',8)))

    def test_visual_evidence_has_numbered_identity_and_dimensions(self):
        assets=[a for a in self.library.list()['assets'] if a['appearance'] in (57,178,183)]
        labels,images=visual_evidence(self.library,assets)
        self.assertEqual([l['id'] for l in labels],[a['id'] for a in assets]);self.assertEqual([l['cell'] for l in labels],[1,2,3])
        self.assertEqual(len(images),1);self.assertTrue(images[0].startswith('data:image/png;base64,'))

    def test_rotated_model_footprints_fit_narrow_measured_hall(self):
        p=blank();a=p['areas'][0];r=a['rooms'][0];r.update(width=1,height=2)
        bounds=detail(self.library,'builtin_ap178')[0]['bounds'];placement=Placement({'arrival':(a,r)})
        for i,(x,y) in enumerate(((2,6.6),(8,6.6),(2,10.4),(8,10.4))):
            placement.exact('arrival','table',dict(id='bench'+str(i),x=x,y=y,facing=0),bounds)
        with self.assertRaisesRegex(ValueError,'overlap'):placement.exact('arrival','table',dict(id='overlap',x=2,y=6.7,facing=90),bounds)
        with self.assertRaisesRegex(ValueError,'beyond'):placement.exact('arrival','table',dict(id='outside',x=.2,y=1,facing=0),bounds)

    def test_builtin_asset_and_dimensions_survive_attach_without_hak(self):
        p=blank();p['design_mode']='area';asset=next(a for a in self.library.list()['assets'] if a['id']=='builtin_ap183')
        p['custom_assets']=[asset];p['custom_placements']=[dict(id='throne',room='arrival',name='Throne',asset_id=asset['id'],placement='north',description='')]
        p['asset_geometry']={asset['id']:detail(self.library,asset['id'])[0]['bounds']}
        target=attach_area(p,'starting_area',blank('target'))['proposal'];validate(target)
        self.assertEqual(target['asset_geometry'],p['asset_geometry']);self.assertEqual(self.library.resolve(p),[])

    @unittest.skipUnless(COMPILER.is_file(),'Installed compiler required')
    def test_builtin_throne_exports_as_real_appearance_with_no_hak(self):
        p=blank();p['design_mode']='area';asset=next(a for a in self.library.list()['assets'] if a['id']=='builtin_ap183')
        p['custom_assets']=[asset];p['custom_placements']=[dict(id='throne',room='arrival',name='Throne',asset_id=asset['id'],placement='north',description='')]
        p['asset_geometry']={asset['id']:detail(self.library,asset['id'])[0]['bounds']};p['object_positions']=[dict(id='throne',x=10,y=17,facing=0)]
        m=build_project(area_test_project(p,'starting_area'),Store(Path(self.tmp.name)/'buildtest'),GAME,COMPILER)
        res={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertEqual(read(res['throne',2044])[1][1]['Appearance'][1],183)
        self.assertEqual(read(res['module',2014])[1][1]['Mod_HakList'][1],[])
        saved=json.loads((Path(m['path']).parent/'project.json').read_text());validate(saved)

if __name__=='__main__':unittest.main()
