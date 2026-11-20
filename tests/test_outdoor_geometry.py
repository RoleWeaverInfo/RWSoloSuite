import copy
import unittest
from pathlib import Path
from rwstudio.authoring import blank,room,validate
from rwstudio.layout import plan
from rwstudio.outdoor_geometry import tile_meshes,export
from rwstudio.measured_geometry import path_nodes,validate_set,tile_meshes as interior_meshes
from rwstudio.native_groups import contains
from rwstudio.nwn.game_assets import GameAssets
from tests.test_spatial_geometry import measured,triangles


def courtyard(kind='forest'):
    p=blank('courtyard_test','Courtyard');p['design_mode']='area';a=p['areas'][0]
    a.update(type=kind,width=10,height=10,room_count=3,rooms=[room('court','Court',1,6,3,2),room('gate','Gatehouse',1,3,2,1),room('field','Field',1,1,2,1)])
    a['outdoor_layout']=dict(courtyard_rooms=['court','gate'],wall_height=4,wall_thickness=.5,road_width=4)
    p['start_room']='court';p['connections']=[dict(id=ident,name=ident,from_room=f,to_room=t,from_side='south',to_side='north',kind='corridor',two_way=True,requires_quest='') for ident,f,t in [('approach','court','gate'),('road','gate','field')]]
    return p


class OutdoorGeometry(unittest.TestCase):
    def test_closed_boundaries_and_continuous_paved_approach(self):
        p=courtyard();validate(p);a=p['areas'][0];l=plan(p)[a['id']];meshes=tile_meshes(a,l);walk=triangles(meshes)
        can_walk=lambda x,y:any(contains(t,x,y) for t in walk)
        for x,y in [(15,65),(25,60),(25,57),(20,50),(20,40),(20,30),(20,25),(20,15),(60,50)]:self.assertTrue(can_walk(x,y),(x,y))
        # Courtyard sides and gatehouse side walls cannot be bypassed.
        for x,y in [(9.75,70),(40.25,70),(20,80.25),(9.75,35),(30.25,35),(12,29.75),(28,29.75),(22.25,48)]:self.assertFalse(can_walk(x,y),(x,y))
        self.assertEqual(len(l['doorways']),1);self.assertEqual((l['doorways'][0]['x'],l['doorways'][0]['y'],l['doorways'][0]['width']),(20,30,4))
        self.assertEqual(len(path_nodes(meshes)),100)
        for floor,wall,wok in meshes.values():self.assertEqual(len(wok['vertices']),len(set(wok['vertices'])))
        self.assertEqual({face[3] for floor,_,_ in meshes.values() for face in floor['faces']},{0,1,2})

    def test_bad_or_foreign_zone_settings_rejected(self):
        for change in [dict(courtyard_rooms=['missing']),dict(courtyard_rooms=[]),dict(courtyard_rooms=['court','court']),dict(wall_height=float('nan')),dict(road_width=0)]:
            p=courtyard();p['areas'][0]['outdoor_layout'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):validate(p)
        p=courtyard();p['areas'][0]['type']='castle'
        with self.assertRaises(ValueError):validate(p)

    def test_solid_interior_mass_is_visible_but_never_walkable(self):
        p=measured(8,13);a=p['areas'][0];layout=plan(p)[a['id']]
        before=triangles(interior_meshes(a,layout));a['geometry']['solid_exterior']=True;validate(p)
        meshes=interior_meshes(a,layout);self.assertEqual(before,triangles(meshes))
        self.assertEqual(len(meshes),a['width']*a['height'])
        cap=[floor['vertices'][v] for floor,_,_ in meshes.values() for face in floor['faces'] if face[3]==3 for v in face[:3]]
        self.assertTrue(cap);self.assertTrue(all(abs(v[2]-4.99)<1e-6 for v in cap))

    def test_courtyard_settings_survive_ai_and_area_copies(self):
        from rwstudio.design_extensions import base_project
        from rwstudio.design_tools import apply_interpretation,attach_area,area_test_project
        from rwstudio.area_presets import preserve
        p=courtyard();a=p['areas'][0];raw=base_project(p)['areas'][0]
        self.assertNotIn('outdoor_layout',raw);preserve(a,raw)
        self.assertEqual(raw['outdoor_layout'],a['outdoor_layout'])
        result=apply_interpretation(p,a['id'],dict(area=base_project(p)['areas'][0],connections=p['connections']))['proposal']
        self.assertEqual(result['areas'][0]['outdoor_layout'],a['outdoor_layout'])
        self.assertEqual(area_test_project(p,a['id'])['areas'][0]['outdoor_layout'],a['outdoor_layout'])
        target=blank('dest','Destination');target['design_mode']='adventure'
        attached=attach_area(p,a['id'],target)['proposal'];self.assertIn('outdoor_layout',attached['areas'][-1]);validate(attached)

    @unittest.skipUnless(Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights').is_dir(),'NWN assets required')
    def test_native_resources_include_valid_tilesets_and_real_gate(self):
        game=GameAssets(Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights'))
        for kind in ('forest','desert','winter'):
            p=courtyard(kind);a=p['areas'][0];resources,layout=export(a,plan(p)[a['id']],game,'test-outdoors')
            validate_set(resources[layout['tileset'],2013]);self.assertEqual(len(layout['measured_tiles']),100)
            self.assertEqual(len([1 for name,t in resources if t==2052]),1)
            self.assertTrue(any(t==2002 and b'node trimesh floor1' in raw for (name,t),raw in resources.items()))
