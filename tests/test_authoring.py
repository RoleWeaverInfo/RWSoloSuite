import configparser
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import seed,blank,validate,review
from rwstudio.layout import arrange,plan,native_tiles,TILESETS,rotate_corners
from rwstudio.adventure_builder import Placement,json_function
from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store
from rwstudio.provider import Provider
from rwstudio.authoring_ai import generate,npc_reply
from rwstudio.nwn.game_assets import GameAssets
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

class DesignTests(unittest.TestCase):
    def test_complete_story_is_not_a_courier_template(self):
        p=validate(seed(),True);r=review(p)
        self.assertTrue(r['ready']);self.assertEqual(r['summary']['rooms'],7);self.assertEqual(len(p['quests']),2)
        self.assertFalse(any(n['id'].startswith('mc_') for n in p['npcs']))
    def test_blank_drafts_save_but_do_not_build(self):
        p=validate(blank());self.assertFalse(review(p)['ready'])
        with self.assertRaises(ValueError):validate(p,True)
    def test_requested_room_count_is_enforced(self):
        p=seed();p['areas'][0]['room_count']=3
        self.assertTrue(any('requested 3' in e for e in review(p)['errors']))
    def test_unconnected_rooms_and_duplicate_ports_rejected(self):
        p=seed();p['connections'].pop();self.assertTrue(any('unreachable' in e for e in review(p)['errors']))
        p=seed();p['connections'][1]['from_side']='east';self.assertTrue(any('used more than once' in e for e in review(p)['errors']))
    def test_cross_area_corridors_rejected(self):
        p=seed();p['connections'][1]['kind']='corridor'
        self.assertTrue(any('different areas require' in e for e in review(p)['errors']))
    def test_one_way_exit_cannot_trap_a_return_objective(self):
        p=seed();p['connections'][1]['two_way']=False
        self.assertTrue(any('one-way exit prevents travel' in e for e in review(p)['errors']))
    def test_native_identifier_limits_are_enforced(self):
        p=seed();p['quests'][0]['steps'][0]['id']='an_identifier_that_is_too_long'
        with self.assertRaisesRegex(ValueError,'steps'):validate(p)
    def test_no_self_locked_quest(self):
        p=seed();p['connections'][1]['requires_quest']='road_safe'
        self.assertTrue(any('blocked by quest gates' in e for e in review(p)['errors']))
    def test_no_encounter_prerequisite_deadlock(self):
        p=seed();p['encounters'][1]['after_quest']='bell_fate'
        self.assertTrue(any('blocked by quest gates' in e for e in review(p)['errors']))
    def test_branch_targets_and_cycles_rejected(self):
        p=seed();p['quests'][1]['steps'][2]['choices'][0]['next']='missing'
        self.assertTrue(any('unknown next' in e for e in review(p)['errors']))
        p=seed();p['quests'][0]['steps'][-1]['next']='meet_ilyra'
        self.assertTrue(any('must end' in e for e in review(p)['errors']))
    def test_item_consumption_cannot_break_a_later_step(self):
        p=seed();s=p['quests'][1]['steps'][1];s['consume']=True
        final=p['quests'][1]['steps'][3];final.update(kind='retrieve',target='bell_clapper')
        self.assertTrue(any('consumed' in e for e in review(p)['errors']))
    def test_room_layout_and_object_placement_are_bounded(self):
        a=seed()['areas'][0];a['room_count']=4;a['width']=18;a['height']=18;a=arrange(a)
        self.assertEqual(len(a['rooms']),4)
        for r in a['rooms']:self.assertLess(r['x']+r['width'],a['width']);self.assertLess(r['y']+r['height'],a['height'])
        a['room_count']=16;a['width']=6;a['height']=6
        with self.assertRaises(ValueError):arrange(a)
        p=seed();rooms={r['id']:(a,r) for a in p['areas'] for r in a['rooms']};place=Placement(rooms)
        points=[place.take('guest_hall') for _ in range(12)]
        self.assertEqual(len(points),len(set(points)))
    def test_scope_is_enforced_in_code(self):
        p=seed();response=copy.deepcopy(p);response['story']='Revised story';response['npcs']=[]
        provider=Provider('unused')
        with patch.object(provider,'request',return_value=response):r=generate(provider,p,'Rewrite the story','story')
        self.assertEqual(r['proposal']['npcs'],p['npcs']);self.assertEqual(r['proposal']['story'],'Revised story')
    def test_invalid_ai_proposal_is_repaired_once(self):
        p=seed();bad=copy.deepcopy(p);bad['connections'][0]['to_room']='missing'
        provider=Provider('unused')
        with patch.object(provider,'request',side_effect=[bad,p]) as call:r=generate(provider,p,'Improve this adventure')
        self.assertEqual(call.call_count,2);self.assertTrue(r['repaired']);self.assertTrue(r['review']['ready'])
    def test_character_secrets_do_not_leak_before_quest(self):
        p=seed();provider=Provider('unused')
        with patch.object(provider,'request',return_value={'reply':'Hello','action':'turn_in'}) as call:
            answer=npc_reply(provider,p,'cael','What happened?',{'quests':{}},'')
            context=call.call_args.args[1];self.assertNotIn('secret',context['npc']);self.assertEqual(answer['action'],'none')
        with patch.object(provider,'request',return_value={'reply':'Hello','action':'none'}) as call:
            npc_reply(provider,p,'cael','What happened?',{'quests':{'road_safe':-1}},'')
            self.assertIn('secret',call.call_args.args[1]['npc'])
    def test_native_booleans_are_explicit_integers(self):
        code=json_function('Demo',[{'optional':True,'scale':False}]);self.assertIn('optional\\\":1',code);self.assertNotIn(':true',code)

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeAdventureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name));cls.p=seed()
        cls.manifest=build_project(cls.p,cls.store,GAME,COMPILER)
        cls.resources={(n,k):b for n,k,b in resources(Path(cls.manifest['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_standalone_has_no_mailbox_or_courier_dependency(self):
        self.assertTrue(self.manifest['standalone']);self.assertFalse(self.manifest['optional_live_ai'])
        for (n,k),raw in self.resources.items():
            self.assertFalse(n.startswith('mc_'))
            if k==2009:self.assertNotIn(b'SqlPrepareQueryCampaign',raw);self.assertNotIn(b'NWNX_',raw)
        module=read(self.resources['module',2014])[1];self.assertEqual(module[1]['Mod_Entry_Area'][1],b'abbey')
    def test_area_dimensions_and_terrain_match_native_tilesets(self):
        game=GameAssets(GAME);layout=plan(self.p)
        for a in self.p['areas']:
            native=read(self.resources[a['id'],2012])[1];tiles=native[1]['Tile_List'][1]
            self.assertEqual(len(tiles),a['width']*a['height']);self.assertEqual(native[1]['Tileset'][1].decode(),TILESETS[a['type']])
            config=configparser.ConfigParser(strict=False);config.read_string(game.get(TILESETS[a['type']],2013).decode('latin1'))
            vertices={tuple(v) for v in layout[a['id']]['vertices']}
            for i,t in enumerate(tiles):
                definition=config['TILE'+str(t[1]['Tile_ID'][1])];corners=tuple(definition[k].lower() in ('floor','rich','forest') for k in ('topleft','topright','bottomleft','bottomright'))
                for _ in range(t[1]['Tile_Orientation'][1]):corners=rotate_corners(corners)
                x=i%a['width'];y=i//a['width'];wanted=tuple(v in vertices for v in ((x,y+1),(x+1,y+1),(x,y),(x+1,y)))
                self.assertEqual(corners,wanted)
    def test_exits_are_real_native_triggers_with_valid_destinations(self):
        markers=set();targets=[]
        for a in self.p['areas']:
            git=read(self.resources[a['id'],2023])[1]
            markers|={w[1]['Tag'][1] for w in git[1]['WaypointList'][1]}
            for trigger in git[1]['TriggerList'][1]:
                self.assertEqual(trigger[1]['ScriptOnEnter'][1],b'aw_exit');self.assertEqual(len(trigger[1]['Geometry'][1]),4)
                targets.extend(v[1]['Value'][1] for v in trigger[1]['VarTable'][1] if v[1]['Name'][1]==b'AW_TARGET')
        self.assertEqual(len(targets),4);self.assertTrue(all(t in markers for t in targets))
    def test_branch_choices_compile_into_native_conversation(self):
        dlg=read(self.resources['ilyra',2029])[1]
        scripts=[r[1]['Script'][1] for r in dlg[1]['ReplyList'][1]]
        self.assertIn(b'aqa_1_2_0',scripts);self.assertIn(b'aqa_1_2_1',scripts)
        for name in ('aqa_1_2_0','aqa_1_2_1','aqc_1_2','awp_1_1'):self.assertIn((name,2010),self.resources)
        self.assertIn(b'restore_bell',self.resources['aqa_1_2_0',2009]);self.assertIn(b'seal_bell',self.resources['aqa_1_2_1',2009])
        journal=read(self.resources['module',2056])[1];self.assertEqual(len(journal[1]['Categories'][1]),2)
    def test_share_package_is_complete_and_has_no_key(self):
        folder=Path(self.manifest['path']).parent
        with zipfile.ZipFile(folder/'rw_silent_bell-aurora.zip') as z:
            self.assertIsNone(z.testzip())
            for name in ('rw_silent_bell.mod','rw_silent_bell.rwproject.json','PLAY.txt','layout.json','validation.json','source/aw_quest.nss'):self.assertIn(name,z.namelist())
            self.assertFalse(any(n.endswith('.env') or n.endswith('settings.json') for n in z.namelist()))
    def test_optional_ai_variant_retains_native_quest_engine(self):
        p=copy.deepcopy(self.p);p['ai_conversations']=True;m=build_project(p,self.store,GAME,COMPILER);r={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertIn(('sp_chat',2010),r);self.assertIn(('aw_beat',2010),r);self.assertIn(b'AQTick(pc)',r['aw_beat',2009]);self.assertIn(b'AQStates()',r['sp_inc',2009]);self.assertNotIn(b'MCReward',r['sp_inc',2009])

if __name__=='__main__':unittest.main()
