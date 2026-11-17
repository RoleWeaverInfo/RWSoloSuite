import copy
import unittest
import tempfile
import math
from pathlib import Path
from unittest.mock import Mock, patch

from rwstudio.authoring import blank, validate, review
from rwstudio.floorplan_design import analyze, native_scale, generate_reviewed, validate_positions
from rwstudio.adventure_builder import Placement
from rwstudio.design_tools import area_test_project, attach_area

PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='

def example():
    p=blank();p['design_mode']='area';a=p['areas'][0]
    a['references']=[dict(name='Hall',notes='Two chairs along the north wall',data_url=PNG)]
    plan=dict(area=copy.deepcopy({k:v for k,v in a.items() if k!='references'}),connections=[],assumptions=['Dimensions estimated'],
        measurements=[dict(room='arrival',width_m=18,height_m=20,basis='estimated',evidence='Door proportions')],
        objects=[dict(id='seats',name='Chair',room='arrival',count=2,description='Along the north wall',search='chair',required=True)],
        matches=[dict(id='seats',asset_id='',stock_kind='chair',status='match',reason='Stock chair')],assets=[],reference_index=0)
    return p,plan

def generate_example():
    p,plan=example();provider=Mock();library=Mock();library.list.return_value={'assets':[]}
    provider.request.return_value={'positions':[dict(id='fp_seats_1',x=4,y=16,facing=270),dict(id='fp_seats_2',x=16,y=16,facing=270)]}
    with patch('rwstudio.authoring_ai.generate',side_effect=lambda provider,prepared,*args:{'proposal':copy.deepcopy(prepared)}):
        result=generate_reviewed(provider,library,p,'starting_area',plan)
    return p,plan,provider,result

class FloorplanTests(unittest.TestCase):
    def test_analysis_uses_image_and_checks_object_matches(self):
        p,plan=example();provider=Mock();library=Mock()
        library.list.return_value={'assets':[]};library.search.return_value=[]
        analysis={k:v for k,v in plan.items() if k not in ('matches','assets','reference_index')}
        provider.request.side_effect=[analysis,{'matches':plan['matches']}]
        result=analyze(provider,library,p,'starting_area',0)
        self.assertEqual(result['plan']['objects'][0]['count'],2)
        self.assertEqual(provider.request.call_args_list[0].kwargs['images'],[PNG])
        self.assertEqual(result['plan']['area']['rooms'][0]['width'],2)
        self.assertEqual(result['plan']['area']['rooms'][0]['interior']['width_m'],18)
        self.assertFalse(result['scale_warnings'])
        context=provider.request.call_args_list[0].args[1]
        self.assertNotIn('description',context)
        self.assertNotIn('existing_rooms',context)
        self.assertIn('Written dimensions',provider.request.call_args_list[0].args[0])

    def test_replacement_workspace_can_merge_obsolete_furnished_rooms(self):
        from rwstudio.authoring import room
        p,plan=example();a=p['areas'][0];a['rooms'].append(room('obsolete','Old invented vestibule',7,2,2,2));a['room_count']=2
        p['furnishings']=[dict(id='oldchair',name='Old chair',room='obsolete',description='',kind='chair',placement='north')]
        provider=Mock();library=Mock();library.list.return_value={'assets':[]}
        provider.request.return_value={'positions':[dict(id='fp_seats_1',x=4,y=16,facing=270),dict(id='fp_seats_2',x=16,y=16,facing=270)]}
        with patch('rwstudio.authoring_ai.generate',side_effect=lambda provider,prepared,*args:{'proposal':copy.deepcopy(prepared)}):
            result=generate_reviewed(provider,library,p,'starting_area',plan)['proposal']
        self.assertEqual(len(result['areas'][0]['rooms']),1)
        self.assertNotIn('oldchair',[f['id'] for f in result['furnishings']])
        self.assertTrue(result['areas'][0]['design_plan'])
        self.assertEqual(len(p['areas'][0]['rooms']),2)

    def test_legacy_floorplan_request_cannot_bypass_checklist(self):
        from rwstudio.server import Application
        p,_=example();app=Mock()
        with self.assertRaisesRegex(ValueError,'objects-and-scale review'):
            Application.post(app,'/api/author/generate',{'project':p,'scope':'area','area_id':'starting_area'})
        app.authoring_provider.request.assert_not_called()

    def test_scale_uses_metres_and_reports_rounding_without_mutation(self):
        p,plan=example();old=copy.deepcopy(plan)
        scaled,warnings=native_scale(plan)
        self.assertEqual(scaled['area']['rooms'][0]['width'],2)
        self.assertEqual(plan,old);self.assertIn('18 × 20',warnings[0])
        plan['measurements'][0].update(width_m=25,height_m=10)
        scaled,_=native_scale(plan)
        self.assertEqual((scaled['area']['rooms'][0]['width'],scaled['area']['rooms'][0]['height']),(3,1))

    def test_substitution_requires_acceptance_before_any_ai_call(self):
        p,plan=example();plan['matches'][0]['status']='substitute';provider=Mock()
        with self.assertRaisesRegex(ValueError,'accept'):
            generate_reviewed(provider,Mock(),p,'starting_area',plan)
        provider.request.assert_not_called()

    def test_reviewed_counts_positions_and_source_image_survive(self):
        p,plan,provider,result=generate_example();q=result['proposal']
        self.assertEqual(len(q['furnishings']),2)
        self.assertEqual(q['object_positions'][0]['x'],4)
        self.assertEqual(q['areas'][0]['design_plan'],native_scale(plan)[0])
        self.assertEqual(provider.request.call_args.kwargs['images'],[PNG])
        validate(q);validate_positions(q)
        self.assertFalse(result['review']['errors'])
        self.assertEqual(p['furnishings'],[])
        test=area_test_project(q,'starting_area')
        self.assertEqual(test['object_positions'],q['object_positions'])
        attached=attach_area(q,'starting_area',blank('destination'))['proposal']
        self.assertEqual(attached['object_positions'],q['object_positions'])
        validate(attached)

    def test_exact_position_keeps_facing_and_allows_focal_axis(self):
        p,_=example();a=p['areas'][0];r=a['rooms'][0];r.update(width=2,height=2)
        placement=Placement({r['id']:(a,r)})
        point=placement.exact(r['id'],'chair',dict(id='chair',x=10,y=17,facing=270))
        self.assertEqual(point,(r['x']*10+10,r['y']*10+17,270))
        with self.assertRaisesRegex(ValueError,'overlap'):
            placement.exact(r['id'],'chair',dict(id='other',x=10,y=17,facing=0))
        with self.assertRaisesRegex(ValueError,'outside'):
            placement.exact(r['id'],'chair',dict(id='other',x=100,y=17,facing=0))

    def test_bad_positions_block_build_review(self):
        _,_,_,result=generate_example();p=result['proposal']
        p['object_positions'][0]['x']=1000
        self.assertFalse(review(p)['ready'])
        self.assertTrue(any('outside' in error for error in review(p)['errors']))

    def test_native_export_preserves_exact_coordinates_and_rotation(self):
        from rwstudio.builder import build_project, ROOT
        from rwstudio.storage import Store
        from rwstudio.nwn.module_copy import resources
        from rwstudio.nwn.gff import read
        game=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights');compiler=ROOT/'vendor/nwnsc/nwnsc.exe'
        if not game.is_dir() or not compiler.is_file():self.skipTest('Local compiler unavailable')
        _,_,_,result=generate_example();p=area_test_project(result['proposal'],'starting_area')
        with tempfile.TemporaryDirectory() as tmp:
            manifest=build_project(p,Store(Path(tmp)),game,compiler)
            entries={(n,k):b for n,k,b in resources(Path(manifest['path']).read_bytes())}
            git=read(entries['starting_area',2023])[1]
            objects={obj[1]['Tag'][1].decode():obj[1] for obj in git[1]['Placeable List'][1]}
            room=p['areas'][0]['rooms'][0]
            for pos in p['object_positions']:
                obj=objects[pos['id']]
                self.assertAlmostEqual(obj['X'][1],room['x']*10+pos['x'])
                self.assertAlmostEqual(obj['Y'][1],room['y']*10+pos['y'])
                self.assertAlmostEqual(obj['Bearing'][1],math.radians(pos['facing']),places=5)

    def test_missing_or_duplicate_position_is_rejected(self):
        p,plan=example();provider=Mock();library=Mock();library.list.return_value={'assets':[]}
        provider.request.return_value={'positions':[]}
        with patch('rwstudio.authoring_ai.generate',side_effect=lambda provider,prepared,*args:{'proposal':copy.deepcopy(prepared)}):
            with self.assertRaisesRegex(ValueError,'every required object'):
                generate_reviewed(provider,library,p,'starting_area',plan)

if __name__=='__main__':unittest.main()
