import copy
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.adventure_builder import Placement
from rwstudio.authoring import seed, review
from rwstudio.authoring_ai import generate
from rwstudio.builder import ROOT, build_project
from rwstudio.companion_tasks import example, reply
from rwstudio.furnishing import RADII
from rwstudio.game_text import response_text
from rwstudio.layout import arrange, center, plan, TILES
from rwstudio.nwn.game_assets import GameAssets
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources
from rwstudio.provider import Provider
from rwstudio.storage import Store

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'


class PlaytestFixTests(unittest.TestCase):
    def test_social_and_visit_text_normalized_preserving_names_and_ids(self):
        value=dict(line_a='Bram\u2019s stock',line_b='\u201cHello\u201d, Ren\u00e9.',reply='Wait\u2026',id='unchanged\u2019id')
        result=response_text(value)
        self.assertEqual(result,dict(line_a="Bram's stock",line_b='"Hello", Ren\u00e9.',reply='Wait...',id='unchanged\u2019id'))
        self.assertEqual(value['reply'],'Wait\u2026')

    def test_furniture_groups_reserve_walk_lanes_and_actors(self):
        p=seed();rooms={r['id']:(a,r) for a in p['areas'] for r in a['rooms']};placement=Placement(rooms)
        rid='guest_hall';cx,cy=center(rooms[rid][1]);actor=placement.take(rid)
        table=placement.furnish(rid,'table','north')
        chair=placement.furnish(rid,'chair','north')
        self.assertLessEqual(math.dist(table[:2],chair[:2]),4)
        expected=math.degrees(math.atan2(table[1]-chair[1],table[0]-chair[0]))
        self.assertAlmostEqual(chair[2],expected)
        for (kind,x,y),(_,_,radius) in zip(placement.decor[rid],placement.footprints[rid]):
            self.assertGreaterEqual(abs(x-cx),3+radius);self.assertGreaterEqual(abs(y-cy),3+radius)
            self.assertGreaterEqual(math.dist((x,y),actor),radius+2)
        self.assertGreaterEqual(math.dist(table[:2],chair[:2]),RADII['table']+RADII['chair']+.2)

    def test_room_scale_and_repetition_review_preserve_author_data(self):
        p=seed();p['areas'][0]['rooms'][0]['width']=4;p['areas'][0]['rooms'][0]['height']=4
        f=p['furnishings'][0]
        p['furnishings'] += [dict(f,id='repeat'+str(i)) for i in range(4)]
        old=copy.deepcopy(p);warnings=review(p)['warnings']
        self.assertTrue(any('large room' in w for w in warnings));self.assertTrue(any('repeated table' in w for w in warnings));self.assertEqual(p,old)
        a=arrange(seed()['areas'][0]);self.assertTrue(all(r['width']<=3 and r['height']<=3 for r in a['rooms']))

    def test_design_provider_receives_room_purpose_and_scale_guide(self):
        p=seed();provider=Provider('unused')
        with patch.object(provider,'request',return_value=copy.deepcopy(p)) as request:
            generate(provider,p,'Furnish these rooms','populate','abbey')
        guide=request.call_args.args[1]['interior_design']
        self.assertIn('10 metres',guide['scale']);self.assertIn('dining',guide['groups'])

    def test_visiting_merchant_quotes_observed_stock_not_invented_prices(self):
        p=example();provider=Provider('unused')
        payload=dict(source=dict(kind='party',profile='seren',name='Seren',communication='speech'),target='bram',actor_uuid='actor',target_uuid='merchant',owner_uuid='owner',question='How much does a sword cost?',quests={},game={})
        with patch.object(provider,'request',return_value=dict(reply='A sword costs 999 gold.',action='none')):
            self.assertNotIn('999',reply(provider,p,payload)['reply'])
            from rwstudio.merchants import CATALOG
            sku=next(iter(CATALOG))
            payload['game']={'merchant':dict(npc='bram',available=1,items=[dict(item=sku,quantity=2,price=17)])}
            answer=reply(provider,p,payload)
        self.assertIn('17 gold',answer['reply']);self.assertNotIn('999',answer['reply']);self.assertEqual(answer['action'],'none')


@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.p=example()
        manifest=build_project(cls.p,Store(Path(cls.temp.name)),GAME,COMPILER)
        cls.entries={(n,k):b for n,k,b in resources(Path(manifest['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_every_connection_has_usable_markers_and_real_arrival_waypoints(self):
        markers={};waypoints=set()
        for a in self.p['areas']:
            git=read(self.entries[a['id'],2023])[1][1]
            waypoints.update(w[1]['Tag'][1].decode() for w in git['WaypointList'][1])
            for obj in git['Placeable List'][1]:
                tag=obj[1]['Tag'][1].decode()
                if tag.startswith('aw_port_'):markers[tag]=obj[1]
        self.assertEqual(len(markers),sum(2 if c['two_way'] else 1 for c in self.p['connections']))
        for obj in markers.values():
            self.assertEqual(obj['Useable'][1],1);self.assertEqual(obj['Static'][1],0)
            self.assertEqual(obj['OnUsed'][1],b'aw_exit')
            target=next(v[1]['Value'][1].decode() for v in obj['VarTable'][1] if v[1]['Name'][1]==b'AW_TARGET')
            self.assertIn(target,waypoints)

    def test_corridor_cells_are_unbroken_full_floor_tiles(self):
        layouts=plan(self.p)
        for a in self.p['areas']:
            tiles=read(self.entries[a['id'],2012])[1][1]['Tile_List'][1]
            for corridor in layouts[a['id']]['corridors']:
                cells=corridor['cells']
                for x,y in cells:self.assertEqual(tiles[y*a['width']+x][1]['Tile_ID'][1],TILES[a['type']][1])
                for left,right in zip(cells,cells[1:]):self.assertEqual(abs(left[0]-right[0])+abs(left[1]-right[1]),1)

    def test_window_contract_has_all_installed_native_fields(self):
        official=GameAssets(GAME).get('nw_inc_nui',2009).decode('latin1')
        implementation=official[official.index('// Implementation'):]
        window=implementation[implementation.index('NuiWindow('):implementation.index('NuiElement(')]
        expected=set(re.findall(r'JsonObjectSetInplace\(ret, "([a-z_]+)"',window))
        ours=(ROOT/'authoring_scripts/aw_ui.nss').read_text(encoding='utf-8')
        ours=ours[ours.index('json AWUIWindow('):ours.index('// Match')]
        actual=set(re.findall(r'JsonObjectSet\(out,"([a-z_]+)"',ours))
        self.assertEqual(actual,expected)


if __name__=='__main__':unittest.main()
