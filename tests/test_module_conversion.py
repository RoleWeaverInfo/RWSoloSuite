import copy
import json
import re
import sqlite3
import time
import tempfile
import unittest
from collections import OrderedDict
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from test_module_analyser import archive,fixture,doc,node,ACTIONS
from rwstudio.nwn.analysis_formats import Archive,gff
from rwstudio.nwn.gff import read,write,text
from rwstudio.builder import conversation
from rwstudio.module_analysis import build_report,Resources,sha256
from rwstudio.module_conversion import build,patch_dialogues,validate_plan_for_report
from rwstudio.imported_module import plan,validate,npc_reply
from rwstudio.storage import Store
from rwstudio.content import validate_project
from rwstudio.service import adventure_document

class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.path=self.root/'original.mod';self.path.write_bytes(fixture())
        self.report,_=build_report(self.path,{},actions=ACTIONS);self.report['module']['filename']='original.mod';self.p=plan(self.report)

    def test_public_profiles_do_not_import_spoilers_or_native_ids_as_ai_ids(self):
        self.assertEqual(validate_project(self.p)['schema_version'],3)
        self.assertTrue(self.p['companions']['enabled'])
        self.assertNotIn('The seal is returned',json.dumps(self.p))
        self.assertIn('lost seal',self.p['npcs'][0]['knowledge']) # Authored examine description is public.
        self.assertNotIn('missing seal from the cave',self.p['npcs'][0]['knowledge'])
        self.assertTrue(all(n['id'].startswith('cv_n') for n in self.p['npcs']))
        self.assertEqual(len({(n['native_tag'],n['native_resref']) for n in self.p['npcs']}),len(self.p['npcs']))
        bad=copy.deepcopy(self.p);bad['npcs'][0]['native_tag']='different'
        with self.assertRaisesRegex(ValueError,'identities'):validate_plan_for_report(bad,self.report)
        bad=copy.deepcopy(self.p);bad['module_name']='original'
        with self.assertRaisesRegex(ValueError,'different filename'):validate_plan_for_report(bad,self.report)
        with self.assertRaisesRegex(ValueError,'Module Conversion'):Store(self.root/'store').save(self.p)

    def test_append_only_at_safe_farewell_not_quest_choice_or_cutscene(self):
        dlg=conversation([('Welcome',[0,1]),('Hidden later reveal',[2]),('Forced quest decision',[3])],
                         [('Goodbye.',[]),('Continue',[1],'advance'),('Farewell.',[]),('I accept',[],'accept')],[(0,''),(1,'secret_gate')])
        raw=write(b'DLG V3.2',dlg);original=copy.deepcopy(dlg)
        entries=OrderedDict({('mara_talk',2029):raw});scripts={};res=Resources(self.path,{})
        changed=patch_dialogues(entries,self.report,res,scripts)
        after=read(entries['mara_talk',2029])[1]
        self.assertEqual(changed['mara_talk']['entries'],[0,1]);self.assertEqual(len(after[1]['ReplyList'][1]),6)
        self.assertEqual(after[1]['StartingList'],original[1]['StartingList'])
        self.assertEqual(after[1]['EntryList'][1][2][1]['RepliesList'],original[1]['EntryList'][1][2][1]['RepliesList'])
        for item in changed['mara_talk']['action_wrappers']:
            self.assertEqual(scripts[item['wrapper']].count('ExecuteScript("'+item['original_action']+'",OBJECT_SELF);'),1 if item['original_action'] else 0)
            row=after[1][item['collection']][1][item['index']][1]
            row['Script']=original[1][item['collection']][1][item['index']][1]['Script']
        self.assertEqual(after[1]['ReplyList'][1][:4],original[1]['ReplyList'][1])
        self.assertEqual(after[1]['EntryList'][1][1][1]['RepliesList'][1][-1][1]['Active'][1],b'rwc_can_chat')
        # Secret text is recorded only by its own reached node, never conditions.
        self.assertNotIn('Hidden later reveal',scripts['rwc_m00000']);self.assertIn('Hidden later reveal',scripts['rwc_m00001'])
        self.assertNotIn('RWRemember',scripts['rwc_s00001']) # Selecting AI never overwrites the transcript.

    def test_roundtrip_copy_preserves_original_resources_and_registration(self):
        game=self.root/'game';(game/'data').mkdir(parents=True);compiler=self.root/'compiler';compiler.touch()
        cfg=dict(game_root=str(game),compiler=str(compiler))
        def runtime(p,digest,game,hooks):
            return {'sp_config':f'string SPProject(){{return "{p["id"]}";}}\nstring SPBuild(){{return "{digest}";}}',
                    **{n:'void main(){}' for n in ('rwc_load','rwc_enter','rwc_beat','rwc_chat')}},{}
        def compile(args,**kw):
            for f in Path(kw['cwd']).glob('*.nss'):
                if 'void main(' in f.read_text():(Path(args[args.index('-b')+1])/(f.stem+'.ncs')).write_bytes(b'NCS fixture')
            return SimpleNamespace(returncode=0,stdout='',stderr='')
        store=Store(self.root/'store');before=self.path.read_bytes()
        with patch('rwstudio.module_conversion.runtime',side_effect=runtime),patch('rwstudio.module_conversion.subprocess.run',side_effect=compile),patch('rwstudio.player_package.export_keys',return_value=[]):
            manifest=build(self.path,self.report,self.p,store,cfg)
        folder=store.root/'builds'/manifest['build_id'];output=folder/manifest['module'];converted=Archive(output);old=Archive(self.path)
        self.assertEqual(self.path.read_bytes(),before)
        for key in old.index:
            if key not in [('module',2014),('mara_talk',2029)]:self.assertEqual(old.get(*key),converted.get(*key),key)
        ifo=gff(converted.get('module',2014));self.assertEqual(ifo['Mod_OnModLoad'],'rwc_load')
        self.assertEqual(adventure_document(output)['project'],self.p)
        self.assertEqual(store.built_project(manifest['build_id']),self.p)
        self.assertTrue((folder/(self.p['module_name']+'-aurora.zip')).is_file())
        self.assertTrue(json.loads((folder/'preservation.json').read_text())['original_scripts_byte_identical'])
        self.path.write_bytes(before+b'x')
        with self.assertRaisesRegex(ValueError,'snapshot changed'):build(self.path,self.report,self.p,store,cfg)

    def test_npc_reply_never_authorizes_quest_or_recruitment_changes(self):
        provider=Mock();provider.request.return_value=dict(reply='Hello.',action='turn_in',story_action='award',merchant_action='buy',companion_action='dismiss',task_target='',task_question='',task_item='',task_quantity='')
        n=self.p['npcs'][0]
        result=npc_reply(provider,self.p,n['id'],'Complete the quest.',{'native_dialogue':'We met at the lodge.'})
        self.assertEqual(result['action'],'none');self.assertEqual(result['story_action'],'');self.assertEqual(result['companion_action'],'')
        context=provider.request.call_args.args[1]
        self.assertEqual(context['heard_dialogue'],'We met at the lodge.');self.assertNotIn('secret',context['npc']);self.assertNotIn('native_tag',context['npc'])
        n['ai_enabled']=False
        with self.assertRaisesRegex(ValueError,'not been enabled'):npc_reply(provider,self.p,n['id'],'Hello',{})

    def test_native_runtime_chains_callbacks_and_only_native_recruits(self):
        from rwstudio.conversion_runtime import runtime
        from rwstudio.server import defaults
        from rwstudio.nwn.game_assets import GameAssets
        cfg=defaults()
        if not cfg['game_root']:self.skipTest('NWN installed assets unavailable')
        game=GameAssets(cfg['game_root'])
        hooks={'Mod_OnModLoad':'old_load','Mod_OnClientEntr':'old_enter','Mod_OnHeartbeat':'old_beat','Mod_OnPlrChat':'old_chat'}
        scripts,_=runtime(self.p,'a'*20,game,hooks)
        for event,name in [('rwc_load','old_load'),('rwc_enter','old_enter'),('rwc_beat','old_beat'),('rwc_chat','old_chat')]:
            self.assertEqual(scripts[event].count('ExecuteScript("'+name+'",OBJECT_SELF);'),1)
        self.assertNotIn('SetMaxHenchmen',scripts['rwc_load']);self.assertNotIn('AQStart',scripts['rwc_enter']);self.assertNotIn('AWATick()',scripts['rwc_beat'])
        self.assertIn('GetAssociateType(body)==ASSOCIATE_TYPE_HENCHMAN && GetIsPC(AWCOwner(body))',scripts['aw_companion'])
        self.assertIn('if(!GetIsPC(AWCOwner(body)))return JsonNull()',scripts['aw_companion'])
        self.assertIn('int AWCCanRecruit(object pc,object body){return FALSE;}',scripts['aw_companion'])
        self.assertNotIn('JsonString("dismiss")',scripts['aw_companion']);self.assertIn('if(command=="recruit" || command=="dismiss")',scripts['aw_companion'])
        self.assertIn('if(count!=1)return OBJECT_INVALID',scripts['aw_config']);self.assertIn('"SP_HIST_"+GetObjectUUID(npc)',scripts['sp_inc'])
        self.assertIn('RWFindActor(pc,tag)',scripts['sp_chat']);self.assertNotIn('GetObjectByTag(tag)',scripts['sp_chat'])
        self.assertIn('!IsInConversation(npc)',scripts['sp_inc']);self.assertIn('!GetIsInCombat(npc)',scripts['sp_inc'])

    def test_native_named_dependencies_and_tlk_install_without_overwrite(self):
        from rwstudio.custom_assets import install_dependencies
        folder=self.root/'copy';user=self.root/'user'
        deps=[]
        for kind,name in [('hak','+Sen_IcyCaverns.hak'),('hak','~wildlands_w.hak'),('tlk','snow.tlk')]:
            file=folder/kind/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'content')
            deps.append(dict(kind=kind,file=name,sha256=sha256(file)))
        (folder/'dependencies.json').write_text(json.dumps(deps));install_dependencies(folder,user)
        self.assertEqual((user/'tlk/snow.tlk').read_bytes(),b'content')
        (user/'hak/+Sen_IcyCaverns.hak').write_bytes(b'different')
        with self.assertRaisesRegex(ValueError,'different content pack'):install_dependencies(folder,user)
        deps[0]['file']='../escape.hak';(folder/'dependencies.json').write_text(json.dumps(deps))
        with self.assertRaisesRegex(ValueError,'filename'):install_dependencies(folder,user)

    def test_registered_copy_handles_npc_party_familiar_and_summon_requests(self):
        from rwstudio.bridge import Bridge,DDL
        from rwstudio.provider import Provider
        from test_companions import snapshot
        store=Store(self.root/'registered');build_id='a'*20;store.register_player_build(build_id,self.p)
        provider=Provider('unused');provider.request=Mock(return_value=dict(reply='I am here.',action='none',companion_action='',task_target='',task_question='',task_item='',task_quantity=''))
        db_path=self.root/'bridge.sqlite';now=int(time.time());ident=self.p['npcs'][0]['id']
        with closing(sqlite3.connect(db_path)) as db,db:
            for sql in DDL:db.execute(sql)
            db.execute('INSERT INTO sp_sessions VALUES(?,?,?,?,?)',('session',self.p['id'],build_id,'{}',now))
            requests=[('npc',ident,{'native_dialogue':'Welcome to the lodge.'}),('npc',ident,snapshot('party',ident,1)),('companion','fam_cat',snapshot()),('companion','summon_default',snapshot('summon','summon_default',1))]
            for i,(kind,tag,game) in enumerate(requests):db.execute('INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(?,?,?,?,?,?,?)',(str(i),'session',kind,tag,json.dumps(dict(game=game,message='Hello',history='')),now,now))
        bridge=Bridge(db_path,store,provider);bridge.enabled=True
        for _ in requests:bridge.process_one()
        with closing(sqlite3.connect(db_path)) as db,db:
            rows=db.execute('SELECT state,response FROM sp_requests').fetchall()
            self.assertTrue(all(state=='ready' for state,response in rows),rows)
            self.assertTrue(all(json.loads(response)['action']=='none' for state,response in rows))
        self.assertEqual(provider.request.call_count,4)
        # The party profile cannot offer recruitment/dismissal even if a forged
        # snapshot claims those native actions are available.
        party_schema=provider.request.call_args_list[1].args[2]
        self.assertNotIn('dismiss',party_schema['properties']['companion_action']['enum'])
        self.assertNotIn('recruit',party_schema['properties']['companion_action']['enum'])
        with self.assertRaisesRegex(ValueError,'original encounters'):bridge.command('session','spawn','fake')

if __name__=='__main__':unittest.main()
