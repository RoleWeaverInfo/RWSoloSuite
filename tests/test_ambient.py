import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import seed,validate,review
from rwstudio.ambient import example,defaults,npc_defaults,permitted,reply
from rwstudio.authoring_ai import generate
from rwstudio.provider import Provider,AIError
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'
PAYLOAD=dict(source='mira',target='tomas',source_uuid='mira-instance',target_uuid='tomas-instance',history='A public greeting.')

class AmbientTests(unittest.TestCase):
    def test_old_projects_migrate_off_without_mutating(self):
        p=seed();p.pop('ambient')
        for n in p['npcs']:n.pop('behavior')
        upgraded=validate(p);self.assertEqual(upgraded['ambient'],defaults());self.assertEqual(upgraded['npcs'][0]['behavior'],npc_defaults())
        self.assertNotIn('ambient',p);self.assertNotIn('behavior',p['npcs'][0])
    def test_patrols_require_reachable_same_area_stops(self):
        for route in ([],['guest_hall'],['guest_hall','missing'],['guest_hall','road_camp']):
            p=example();p['npcs'][-2]['behavior']['route']=route
            with self.subTest(route=route):self.assertFalse(review(p)['ready'])
        p=example();p['connections'][0]['kind']='exit';self.assertFalse(review(p)['ready'])
        self.assertTrue(review(example())['ready'])
        a,b=example()['npcs'][-2:];self.assertTrue(b['behavior']['patrol_enabled']);self.assertEqual(a['behavior']['route'],b['behavior']['route'])
    def test_numeric_and_size_limits(self):
        for key,value in [('social_interval',59),('social_budget',13)]:
            p=example();p['ambient'][key]=value
            with self.assertRaises(ValueError):validate(p)
        for key,value in [('wait_seconds',5),('cooldown',59),('route',['guest_hall']*17),('partners',['tomas']*17)]:
            p=example();p['npcs'][-2]['behavior'][key]=value
            with self.assertRaises(ValueError):validate(p)
    def test_social_partners_must_exist_and_not_repeat(self):
        for partners in (['missing'],['mira'],['tomas','tomas']):
            p=example();p['npcs'][-2]['behavior']['partners']=partners;self.assertFalse(review(p)['ready'])
    def test_both_sides_must_opt_in_and_allow_each_other(self):
        p=example();a,b=p['npcs'][-2:];self.assertTrue(permitted(p,a,b));self.assertTrue(permitted(p,b,a))
        for target,key,value in [(a['behavior'],'social_enabled',False),(b['behavior'],'partners',['ilyra']),(a,'ai_enabled',False),(p['ambient'],'social',False)]:
            old=target[key];target[key]=value;self.assertFalse(permitted(p,a,b));target[key]=old
        a['behavior']['partners']=[];b['behavior']['partners']=[];self.assertTrue(permitted(p,a,b))
    def test_each_speaker_has_only_own_public_context(self):
        p=example();a,b=p['npcs'][-2:];a.update(secret='SECRET_A',knowledge='PUBLIC_A');b.update(secret='SECRET_B',knowledge='PUBLIC_B')
        provider=Provider('unused')
        with patch.object(provider,'request',side_effect=[dict(line='Good morning.',action='give_gold'),dict(line='Welcome back.',action='advance_quest')]) as request:
            result=reply(provider,p,dict(PAYLOAD,history='public history',private_player_history='PRIVATE_TRANSCRIPT'))
        first,second=[c.args[1] for c in request.call_args_list]
        raw=json.dumps([first,second]);self.assertNotIn('SECRET_',raw);self.assertNotIn('PRIVATE_TRANSCRIPT',raw);self.assertNotIn(p['story'],raw)
        self.assertNotIn('PUBLIC_B',json.dumps(first));self.assertNotIn('PUBLIC_A',json.dumps(second));self.assertEqual(second['heard_public_line'],'Good morning.')
        self.assertEqual(result,dict(line_a='Good morning.',line_b='Welcome back.',action='none'))
        self.assertEqual(request.call_args_list[0].args[2]['properties']['action']['enum'],['none'])
    def test_disabled_identity_and_ownership_requests_do_not_call_provider(self):
        p=example();provider=Provider('unused')
        for mutate in ('ai','social','partner','identity'):
            q=copy.deepcopy(p);payload=dict(PAYLOAD)
            if mutate=='ai':q['ai_conversations']=False
            if mutate=='social':q['ambient']['social']=False
            if mutate=='partner':q['npcs'][-1]['behavior']['social_enabled']=False
            if mutate=='identity':payload['target_uuid']=payload['source_uuid']
            with patch.object(provider,'request') as request:
                with self.assertRaises(AIError):reply(provider,q,payload)
                request.assert_not_called()
    def test_public_lines_bounded_nonverbal_and_yield_between_speakers(self):
        p=example();p['npcs'][-2]['behavior']['communication']='nonverbal';provider=Provider('unused')
        with patch.object(provider,'request',side_effect=[dict(line='She says "hello"',action='none'),dict(line='x'*600,action='none')]):result=reply(provider,p,PAYLOAD)
        self.assertIn('wordless',result['line_a']);self.assertEqual(len(result['line_b']),280)
        checks=iter([True,False])
        with patch.object(provider,'request',return_value=dict(line='Hello',action='none')) as request:
            with self.assertRaises(AIError):reply(provider,p,PAYLOAD,lambda:next(checks))
            self.assertEqual(request.call_count,1)
    def test_behavior_generation_scope_preserves_story_and_world(self):
        p=example();generated=copy.deepcopy(p);generated['story']='unrequested change';generated['npcs'][-2]['behavior']['wait_seconds']=42
        provider=Provider('unused')
        with patch.object(provider,'request',return_value=generated):result=generate(provider,p,'Make Mira wait longer','behaviors')['proposal']
        self.assertEqual(result['story'],p['story']);self.assertEqual(result['areas'],p['areas']);self.assertEqual(result['quests'],p['quests']);self.assertEqual(result['npcs'][-2]['behavior']['wait_seconds'],42)

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeAmbientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name));cls.p=example();cls.m=build_project(cls.p,cls.store,GAME,COMPILER)
        cls.r={(n,k):b for n,k,b in resources(Path(cls.m['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_patrol_and_social_hooks_compile_without_replacing_heartbeat(self):
        for name in ('aw_am_dialog','aw_am_dead','aw_beat','aw_load'):self.assertIn((name,2010),self.r)
        self.assertIn(b'AWALoad()',self.r['aw_load',2009]);self.assertIn(b'AWATick()',self.r['aw_beat',2009]);self.assertIn(b'AWSTick(GetFirstPC())',self.r['aw_beat',2009])
        native=read(self.r['mira',2027])[1][1];self.assertEqual(native['ScriptHeartbeat'][1],b'')
        self.assertIn(b'AWATouch',self.r['aw_talk',2009]);self.assertIn(b'AWATouch(npc)',self.r['sp_inc',2009])
    def test_patrols_use_real_pathfinding_no_teleport_and_bounded_retries(self):
        src=self.r['aw_ambient',2009]
        for text in (b'ActionMoveToLocation',b'ACTION_INVALID',b'AWA_SOCIAL_LOCK',b'AWA_HOLD',b'GetCommandable',b'GetMaster',b'GetIsPossessedFamiliar',b'>=120',b'+60',b'pingpong'):self.assertIn(text,src)
        self.assertNotIn(b'JumpTo',src);self.assertNotIn(b'SetEventScript(body,EVENT_SCRIPT_CREATURE_ON_HEARTBEAT',src)
        self.assertIn(b'base!="aw_cp_dialog"',src);self.assertIn(b'base!="aw_cp_dead"',src)
    def test_social_delivery_rechecks_exact_objects_and_has_no_game_actions(self):
        src=self.r['aw_social',2009]
        for text in (b'AWSFresh',b'AWS_A_ID',b'AWS_B_ID',b'AWA_EPOCH',b'AWSPlayerBusy',b'LineOfSightObject',b'social_budget',b'cooldown',b'GetLocalObject(GetModule(),"AWS_A")',b'SpeakString',b'SP_PENDING',b'AWSRemember',b'SPNow()-GetLocalInt(GetModule(),"AWS_SENT")>=90'):self.assertIn(text,src)
        self.assertNotIn(b'SP_HIST_',src);self.assertNotIn(b'AWAIAction',src);self.assertNotIn(b'CopyItem',src)
        self.assertIn(b'payload=JsonObjectSet(payload,"game",JsonObject())',src)
    def test_patrols_work_with_ai_off_and_no_campaign_transport(self):
        p=copy.deepcopy(self.p);p['ai_conversations']=False;m=build_project(p,self.store,GAME,COMPILER);r={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertNotIn(('aw_social',2009),r);self.assertIn(b'AWATick()',r['aw_beat',2009])
        for (name,kind),raw in r.items():
            if kind==2009:self.assertNotIn(b'SqlPrepareQueryCampaign',raw);self.assertNotIn(b'NWNX_',raw)

if __name__=='__main__':unittest.main()
