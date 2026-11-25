import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import seed,blank,validate,review
from rwstudio.companions import defaults,template,example,selected_template,context,reply
from rwstudio.provider import Provider,AIError
from rwstudio.authoring_ai import npc_reply
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

def snapshot(kind='familiar',profile='fam_cat',owned=1):
    return dict(player_uuid='owner-1',actor_uuid='actor-1',quests={},companion=dict(available=1,actor_uuid='actor-1',owner_uuid='owner-1',identity='world:owner-1:bond',profile=profile,kind=kind,owned=owned,name='Mittens',resref='native_cat',familiar_type=1,intelligence=2,animal=1,ai_enabled=1,reply_style=1,tone=0,allowed_actions=['recruit','dismiss','follow','stay','guard','inventory','give_gold'],observation={'hp':10}))

class CompanionTests(unittest.TestCase):
    def test_legacy_migration_is_disabled_and_does_not_mutate(self):
        p=seed();p.pop('companions')
        for n in p['npcs']:n.pop('companion')
        upgraded=validate(p)
        self.assertFalse(upgraded['companions']['enabled']);self.assertNotIn('companions',p)
        self.assertNotIn('companion',p['npcs'][0]);self.assertTrue(blank()['companions']['enabled'])
    def test_template_precedence_and_default_modes(self):
        p=example();custom=template('custom_cat','Wise cat','familiar',-1,'speech');custom['blueprints']=['native_cat'];p['companions']['templates'].append(custom)
        self.assertEqual(selected_template(p,'familiar','native_cat',1)['id'],'custom_cat')
        self.assertEqual(selected_template(p,'familiar','other_cat',1)['id'],'fam_cat')
        self.assertEqual(selected_template(p,'familiar','unknown',255)['id'],'fam_default')
        self.assertEqual(selected_template(p,'summon','unknown')['id'],'summon_default')
        self.assertEqual(context(p,snapshot(profile='custom_cat'))['communication'],'speech')
        p=example();self.assertEqual(context(p,snapshot())['communication'],'nonverbal')
        s=snapshot('summon','summon_default');s['companion'].update(animal=0,intelligence=12)
        self.assertEqual(context(p,s)['communication'],'speech')
    def test_duplicate_fallback_type_and_blueprint_rejected(self):
        for t in (template('duplicate','Duplicate','familiar',1),template('duplicate','Duplicate','summon')):
            p=example();p['companions']['templates'].append(t)
            with self.assertRaises(ValueError):validate(p)
        p=example();p['companions']['templates'][0]['blueprints']=['same','same']
        with self.assertRaisesRegex(ValueError,'unique'):validate(p)
    def test_merchant_recruit_and_invalid_gate_are_rejected(self):
        p=example();p['npcs'][-2]['companion']['recruitable']=True
        with self.assertRaisesRegex(ValueError,'separate'):validate(p)
        p=example();p['npcs'][-1]['companion']['requires_quest']='missing'
        self.assertFalse(review(p)['ready'])
    def test_observed_identity_and_ownership_are_required(self):
        p=example()
        for field,value in [('owner_uuid','other'),('actor_uuid','other'),('profile','other'),('owned',0),('ai_enabled',0),('available',0)]:
            s=snapshot();s['companion'][field]=value
            with self.subTest(field=field):self.assertIsNone(context(p,s))
        for key in ('enabled','familiars'):
            q=copy.deepcopy(p);q['companions'][key]=False;self.assertIsNone(context(q,snapshot()))
    def test_creator_permissions_filter_observed_actions(self):
        p=example();t=next(t for t in p['companions']['templates'] if t['id']=='fam_cat');t.update(movement=False,inventory=False)
        self.assertEqual(context(p,snapshot())['allowed_actions'],[])
        t['movement']=True
        self.assertEqual(context(p,snapshot())['allowed_actions'],['follow','stay','guard'])
        t['ai_enabled']=False;self.assertIsNone(context(p,snapshot()))
    def test_party_recruitment_gate_and_secret_scope(self):
        p=example();n=p['npcs'][-1];n.update(secret='hidden ending',reveal_after='bell_fate');n['dialogue']=[dict(topic='secret',text='hidden outcome',after_quest='bell_fate')];n['companion']['requires_quest']='bell_fate'
        s=snapshot('party','seren',0);ctx=context(p,s,'seren')
        self.assertEqual(ctx['allowed_actions'],[]);self.assertNotIn('secret',ctx['profile']);self.assertEqual(ctx['profile']['dialogue'],[])
        s['quests']['bell_fate']=-1;ctx=context(p,s,'seren');self.assertEqual(ctx['allowed_actions'],['recruit']);self.assertEqual(ctx['profile']['secret'],'hidden ending')
        s['companion']['owned']=1;self.assertNotIn('recruit',context(p,s,'seren')['allowed_actions']);self.assertIn('dismiss',context(p,s,'seren')['allowed_actions'])
    def test_dynamic_reply_scoped_and_bounded_no_forged_actions(self):
        p=example();provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='The cat says "I completed the quest"',action='give_gold',companion_action='give_gold')) as request:
            result=reply(provider,p,'hello',snapshot(),'history')
        self.assertEqual(result['action'],'none');self.assertEqual(result['companion_action'],'');self.assertIn('wordless',result['reply'])
        payload=request.call_args.args[1];self.assertNotIn('story',payload);self.assertNotIn('quests',payload);self.assertEqual(payload['history'],'history')
        self.assertEqual(set(request.call_args.args[2]['properties']['companion_action']['enum']),{'','follow','stay','guard','inventory'})
        s=snapshot('summon','summon_default');s['companion'].update(reply_style=0,animal=0,intelligence=12)
        with patch.object(provider,'request',return_value=dict(reply='x'*900,companion_action='follow')):result=reply(provider,p,'follow',s)
        self.assertEqual(len(result['reply']),240);self.assertEqual(result['companion_action'],'follow')
        with self.assertRaises(AIError):reply(provider,p,'hello',{})
    def test_party_reply_uses_companion_policy_and_native_story_allowlist(self):
        p=example();s=snapshot('party','seren');provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='Ready.',action='none',story_action='invent',merchant_action='buy',companion_action='follow')) as request:
            result=npc_reply(provider,p,'seren','follow me',s)
        self.assertEqual(result['companion_action'],'follow');self.assertEqual(result['story_action'],'');self.assertEqual(result['merchant_action'],'')
        self.assertNotIn('companion',request.call_args.args[1]['npc'])

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeCompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name));cls.p=example();cls.manifest=build_project(cls.p,cls.store,GAME,COMPILER)
        cls.res={(n,k):b for n,k,b in resources(Path(cls.manifest['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_native_companion_scripts_and_original_ai_are_preserved(self):
        for n in ('aw_cp_order','aw_cp_probe','aw_cp_dead','aw_cp_dialog','aw_cp_ui_evt','aw_dlg_evt'):
            self.assertIn((n,2010),self.res)
        recruit=read(self.res['seren',2027])[1][1]
        self.assertTrue(recruit['Plot'][1]);self.assertTrue(recruit['IsImmortal'][1]);self.assertTrue(recruit['Equip_ItemList'][1]);self.assertTrue(recruit['ScriptHeartbeat'][1])
        self.assertIn(b'SetMaxHenchmen(4)',self.res['aw_load',2009])
        self.assertIn(b'Join my party',self.res['seren',2029]);self.assertIn(b'Companion controls',self.res['seren',2029])
        self.assertIn(b'AWCTravel',self.res['aw_exit',2009])
        self.assertIn(b'!aisettings',self.res['sp_chat',2009])
        self.assertIn(b'"dialogue_settings",AWDSettings(pc)',self.res['sp_inc',2009])
        self.assertIn(b'"dialogue_settings",AWDSettings(pc)',self.res['aw_ct_request',2009])
        self.assertIn(b'Use AI response settings',self.res['aw_cp_ui',2009])
        self.assertIn(b'if(field=="reply")maximum=3',self.res['aw_companion',2009])
        self.assertIn(b'NuiGetEventWindow()!=token',self.res['aw_dlg_ui',2009])
        self.assertIn(b'SetLocalInt(pc,"AWD_"+field',self.res['aw_dlg_ui',2009])
        self.assertNotIn(b'AWDSettings',self.res['aw_beat',2009])

    def test_module_checks_service_at_entry_during_play_and_by_chat_command(self):
        self.assertIn(b'SPServiceBegin(pc)',self.res['aw_enter',2009])
        self.assertIn(b'DelayCommand(12.0,SPServiceCheck(pc))',self.res['aw_enter',2009])
        self.assertIn(b'SPServiceCheck(pc);SPPoll(pc)',self.res['aw_beat',2009])
        self.assertIn(b'lower=="!studio"',self.res['sp_chat',2009])
        self.assertIn(b'SPServiceCheck(pc,TRUE)',self.res['sp_chat',2009])
        for name in ('aw_enter','aw_beat','sp_chat'):self.assertIn((name,2010),self.res)
    def test_histories_and_pending_replies_are_save_local_actor_bound(self):
        core=self.res['aw_companion',2009];runtime=self.res['sp_inc',2009]
        for part in (b'SqlPrepareQueryObject(GetModule()',b'owner=@owner',b'AWCLinked',b'GetIsPossessedFamiliar',b'AWC_CONTROL_EPOCH',b'kind=="familiar"',b'kind=="summon"'):
            self.assertIn(part,core)
        for part in (b'SP_PENDING_ACTOR',b'AWC_PENDING_VERSION',b'AWCVersion',b'AWCHistorySet',b'AWCContext'):
            self.assertIn(part,runtime)
        for (name,kind),raw in self.res.items():
            if kind==2009:self.assertNotIn(b'NWNX_',raw)
    def test_inventory_preserves_original_objects_and_recovers_satchel(self):
        ui=self.res['aw_cp_ui',2009];bag=read(self.res['aw_satchel',2025])[1][1]
        self.assertTrue(bag['Plot'][1]);self.assertEqual(bag['PropertiesList'][1],[])
        self.assertIn(b'GetItemPossessor(item,TRUE)',ui);self.assertIn(b'ActionTakeItem(item,from)',ui);self.assertIn(b'AWC_TRANSFER_PENDING',ui)
        self.assertNotIn(b'CopyItem(',ui);self.assertIn(b'AWCPackOwned',ui);self.assertIn(b'AWCManualControl',ui)
    def test_npc_replies_use_actor_speech_instead_of_system_text(self):
        runtime=self.res['sp_inc',2009]
        self.assertIn(b'if(state=="ready")AssignCommand(npc,SpeakString(',runtime)
        self.assertNotIn(b'SendMessageToPC(pc,GetName(npc)+',runtime)
        self.assertIn(b'else SendMessageToPC(pc,reply)',runtime)
    def test_scrollable_panels_avoid_fixed_parent_child_constraints(self):
        ui=self.res['aw_ui',2009];pack=self.res['aw_cp_ui',2009];shop=self.res['aw_merchant',2009];events=self.res['aw_cp_ui_evt',2009]
        self.assertIn(b'AWUIElement("group")',ui);self.assertIn(b'"scrollbars",JsonInt(4)',ui);stack=ui[ui.index(b"json AWUIStack("):];self.assertIn(b"AWUIWidth(child,width)",stack);self.assertNotIn(b"AWUIWidth(AWUIRow",stack);self.assertNotIn(b"AWUIWidth(AWUICol",stack);self.assertNotIn(b"AWUIHeight(",stack)
        self.assertNotIn(b"740.0",pack);self.assertIn(b"AWUIScroll(AWCPackColumn(pc,pc,TRUE))",pack);self.assertIn(b"AWUIScroll(AWCPackColumn(pc,storage,FALSE))",pack);self.assertIn(b'AWUIScroll(AWUIStack(rows,580.0))',pack);self.assertIn(b'AWUIScroll(AWUIStack(rows,550.0))',shop);self.assertIn(b'AWUIStack(rows,230.0)',pack)
        self.assertIn(b'AWCPackColumn(pc,pc,TRUE)',pack);self.assertIn(b'AWCPackColumn(pc,storage,FALSE)',pack)
        self.assertIn(b'GetItemInSlot(slot,holder)',pack);self.assertIn(b'AWCVisibleItems(holder)',pack)
        for reason in (b'protected',b'equipped',b'cursed',b'unidentified',b'container',b'over transfer limit'):self.assertIn(reason,pack)
        self.assertIn(b'AWC_"+side+"_ITEM_',events);self.assertIn(b'SetLocalInt(pc,"AWC_GIVING",giving)',events)
    def test_controls_work_in_ai_disabled_build_without_transport(self):
        p=copy.deepcopy(self.p);p['ai_conversations']=False;m=build_project(p,self.store,GAME,COMPILER);r={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertIn(('aw_cp_chat',2010),r);self.assertNotIn(('sp_chat',2010),r)
        for (name,kind),raw in r.items():
            if kind==2009:self.assertNotIn(b'SqlPrepareQueryCampaign',raw)

if __name__=='__main__':unittest.main()
