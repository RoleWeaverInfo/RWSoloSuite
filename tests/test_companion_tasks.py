import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import validate
from rwstudio.companion_tasks import example,reply
from rwstudio.provider import Provider,AIError
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.module_copy import resources

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'
def payload():return dict(source=dict(kind='party',profile='seren',name='Seren',resref='seren',familiar_type=-1,communication='speech'),target='cael',actor_uuid='seren-instance',target_uuid='cael-instance',owner_uuid='hero-instance',question='Why is the bell silent?',quests={},game={})

class CompanionTaskTests(unittest.TestCase):
    def test_missing_policies_use_enabled_defaults_without_mutation(self):
        p=example()
        for n in p['npcs']:
            n['companion'].pop('inspect_containers');n['companion'].pop('social_visits');n['behavior'].pop('accept_visits')
        for t in p['companions']['templates']:t.pop('inspect_containers');t.pop('social_visits')
        q=validate(p)
        self.assertNotIn('social_visits',p['npcs'][-1]['companion'])
        self.assertTrue(q['npcs'][-1]['companion']['social_visits']);self.assertTrue(q['npcs'][0]['behavior']['accept_visits']);self.assertTrue(q['companions']['templates'][0]['inspect_containers'])
    def test_recipient_only_receives_unlocked_knowledge_and_no_mechanics(self):
        p=example();provider=Provider('unused');request_payload=payload()
        with patch.object(provider,'request',return_value=dict(reply='I was afraid.',action='grant_gold')) as request:result=reply(provider,p,request_payload)
        ctx=request.call_args.args[1];self.assertNotIn('secret',ctx['npc']);self.assertNotIn('story',ctx);self.assertNotIn('source',ctx);self.assertEqual(result['action'],'none')
        self.assertEqual(request.call_args.args[2]['properties']['action']['enum'],['none'])
        request_payload['quests']['road_safe']=-1
        with patch.object(provider,'request',return_value=dict(reply='I feared the voice.',action='none')) as request:reply(provider,p,request_payload)
        self.assertEqual(request.call_args.args[1]['npc']['secret'],p['npcs'][2]['secret'])
    def test_creator_and_recipient_permissions_block_provider(self):
        for field in ('social_visits','movement'):
            p=example();p['npcs'][4]['companion'][field]=False
            provider=Provider('unused')
            with patch.object(provider,'request') as request:
                with self.assertRaises(AIError):reply(provider,p,payload())
                request.assert_not_called()
        p=example();p['npcs'][2]['behavior']['accept_visits']=False
        with self.assertRaises(AIError):reply(Provider('unused'),p,payload())
        p=example();p['ai_conversations']=False
        with self.assertRaises(AIError):reply(Provider('unused'),p,payload())
    def test_distinct_actual_actor_identities_required(self):
        for field in ('actor_uuid','target_uuid','owner_uuid'):
            data=payload();data[field]=''
            with self.assertRaises(AIError):reply(Provider('unused'),example(),data)
        data=payload();data['target_uuid']=data['actor_uuid']
        with self.assertRaises(AIError):reply(Provider('unused'),example(),data)
    def test_familiars_and_summons_use_matching_profile(self):
        p=example();provider=Provider('unused')
        for kind,profile,ref,number in [('familiar','fam_imp','native_imp',3),('summon','summon_default','native_summon',-1)]:
            data=payload();data['source'].update(kind=kind,profile=profile,resref=ref,familiar_type=number)
            with patch.object(provider,'request',return_value=dict(reply='A useful clue.',action='none')):self.assertEqual(reply(provider,p,data)['reply'],'A useful clue.')
            data['source']['profile']='wrong'
            with self.assertRaises(AIError):reply(provider,p,data)
    def test_nonverbal_profiles_cannot_make_verbal_visits(self):
        p=example();data=payload();data['source'].update(kind='familiar',profile='fam_cat',resref='native_cat',familiar_type=1,communication='speech')
        with self.assertRaises(AIError):reply(Provider('unused'),p,data)
        data=payload();data['source']['communication']='nonverbal'
        with self.assertRaises(AIError):reply(Provider('unused'),p,data)
    def test_answers_are_bounded_and_do_not_share_private_history(self):
        provider=Provider('unused');data=payload();data.update(history='PRIVATE_PLAYER_TRANSCRIPT',full_story='HIDDEN_FULL_PLOT')
        with patch.object(provider,'request',return_value=dict(reply='x'*900,action='none')) as request:result=reply(provider,example(),data)
        self.assertEqual(len(result['reply']),240);self.assertNotIn('PRIVATE_PLAYER_TRANSCRIPT',json.dumps(request.call_args.args[1]));self.assertNotIn('HIDDEN_FULL_PLOT',json.dumps(request.call_args.args[1]))

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeCompanionTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name));cls.p=example();cls.m=build_project(cls.p,cls.store,GAME,COMPILER);cls.r={(n,k):b for n,k,b in resources(Path(cls.m['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_task_entries_compile_and_shared_tick_runs(self):
        for name in ('aw_ct_move','aw_ct_request','aw_ct_poll','aw_ct_cancel'):self.assertIn((name,2010),self.r)
        self.assertIn(b'AWTTick(pc)',self.r['aw_beat',2009]);self.assertIn(b'AWTParse(pc,GetLocalObject(pc,"SP_FOCUS"),message)',self.r['sp_inc',2009])
    def test_containers_do_not_use_creature_only_perception(self):
        core=self.r['aw_cp_tasks',2009];chest=core[core.index(b'int AWTChest('):core.index(b'int AWTRecipient(')]
        self.assertNotIn(b'GetObjectSeen',chest)
        for text in (b'LineOfSightObject(body,target)',b'GetHasInventory(target)',b'!GetLocked(target)',b'!GetIsTrapped(target)',b'AQDone('):self.assertIn(text,chest)
        recipient=core[core.index(b'int AWTRecipient('):core.index(b'json AWTCandidates(')]
        self.assertIn(b'GetObjectSeen(target,body)',recipient)
    def test_natural_task_dispatch_rechecks_native_offer_and_permissions(self):
        core=self.r['aw_cp_tasks',2009];runtime=self.r['sp_inc',2009]
        for text in (b'AWT_PENDING_OPTIONS',b'choice==kind+":"+AWText(entry,"uuid")',b'GetObjectByUUID(AWText(entry,"uuid"))',b'AWTStart(pc,body,kind,target,question)'):self.assertIn(text,core)
        self.assertIn(b'JsonDump(taskOptions)',runtime);self.assertIn(b'AWTApplyAI(pc,npc,result)',runtime)
    def test_inspection_reads_only_after_confirmed_open_and_does_not_take_items(self):
        core=self.r['aw_cp_tasks',2009]
        for text in (b'AWT_ACCESS',b'!GetLocked(target)',b'!GetIsTrapped(target)',b'GetItemPossessor(item,TRUE)==target',b'AWTMove(body,"open",target)',b'additional items not listed',b'GetObjectUUID(target)!=GetLocalString(body,"AWT_TARGET_UUID")'):self.assertIn(text,core)
        for text in (b'CopyItem(',b'ActionTakeItem(',b'GiveGoldToCreature(',b'AWAIAction('):self.assertNotIn(text,core)
    def test_native_order_and_permission_changes_cancel_without_restore_overwrite(self):
        core=self.r['aw_cp_tasks',2009];move=self.r['aw_ct_move',2009]
        for text in (b'AWT_SAVE_EPOCH',b'AWT_NATIVE',b'GetLastAssociateCommand',b'AWT_ACTOR_UUID',b'The tasked companion disappeared',b'AWT_RESTORE'):self.assertIn(text,core)
        self.assertIn(b'GetLocalInt(OBJECT_SELF,"AWT_NATIVE")!=GetLastAssociateCommand()',move)
        self.assertIn(b'NW_ASC_MODE_STAND_GROUND',move);self.assertIn(b'GetIsPossessedFamiliar',move)
    def test_visit_answer_only_delivered_to_current_objects_and_report_after_return(self):
        core=self.r['aw_cp_tasks',2009];poll=self.r['aw_ct_poll',2009]
        for text in (b'AWT_TARGET_EPOCH',b'GetDistanceBetween(OBJECT_SELF,target)>6.0',b'AWT_SESSION',b'>=90',b'AssignCommand(target,SpeakString(',b'AWT_RESULT'):self.assertIn(text,poll)
        self.assertIn(b'if(phase==4)',core);self.assertIn(b'GetDistanceBetween(pc,body)>5.0',core);self.assertIn(b'AWCHistorySet',core)
        self.assertNotIn(b'AWAIAction',poll);self.assertNotIn(b'SP_HIST_',self.r['aw_ct_request',2009]);self.assertIn(b'GetDistanceBetween(OBJECT_SELF,target)<=6.0',self.r['aw_ct_request',2009])
    def test_ai_off_build_keeps_native_inspection_and_excludes_visit_transport(self):
        p=copy.deepcopy(self.p);p['ai_conversations']=False;m=build_project(p,self.store,GAME,COMPILER);r={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertIn(('aw_ct_move',2010),r);self.assertNotIn(('aw_ct_request',2010),r)
        for (name,kind),raw in r.items():
            if kind==2009:self.assertNotIn(b'SqlPrepareQueryCampaign',raw)

if __name__=='__main__':unittest.main()
