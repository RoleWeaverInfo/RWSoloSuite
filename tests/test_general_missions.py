import copy
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_module_analyser import archive, doc, node, ncs, integer, string, action
from rwstudio.builder import ROOT
from rwstudio.module_analysis import build_report, Resources
from rwstudio.imported_module import plan, validate as validate_profile
from rwstudio.managed_missions import catalog, draft, validate, active_all, ai_context
from rwstudio.general_missions import inspect
from rwstudio.general_mission_runtime import apply
from rwstudio.module_conversion import build
from rwstudio.nwn.analysis_formats import Archive, gff
from rwstudio.nwn.gff import write, text
from rwstudio.nwn.script_analysis import analyse, prototypes
from rwstudio.nwn.mission_bytecode import suppress
from rwstudio.server import defaults
from rwstudio.storage import Store

ACTIONS={
 0:dict(name='AddJournalQuestEntry',return_type='void',types=['string','int'],params=['tag','state']),
 1:dict(name='GiveGoldToCreature',return_type='void',types=['object','int'],params=['pc','gold']),
 2:dict(name='GiveXPToCreature',return_type='void',types=['object','int'],params=['pc','xp']),
 3:dict(name='SetLocalInt',return_type='void',types=['object','string','int'],params=['obj','name','value']),
 4:dict(name='ExecuteScript',return_type='void',types=['string','object'],params=['name','obj']),
}
for spec in ACTIONS.values():spec['return']=spec.pop('return_type')


def synthetic(scripts=None):
    def creature(name,tag,dlg):return node(FirstName=(12,text(name)),Tag=(10,tag.encode()),TemplateResRef=(11,tag.encode()),Conversation=(11,dlg.encode()))
    mara=creature('Mara','mara','mara_talk');oren=creature('Oren','oren','oren_talk')
    def dialogue(actor,quest,script):return (actor+'_talk',2029,doc('DLG',StartingList=(15,[node(Index=(4,0),Active=(11,b''))]),EntryList=(15,[node(Text=(12,text('Please help with '+quest)),Script=(11,script.encode()),RepliesList=(15,[node(Index=(4,0),Active=(11,b''))]))]),ReplyList=(15,[node(Text=(12,text('Farewell.')),EntriesList=(15,[]))])))
    def quest(tag,name,instruction):return node(Tag=(10,tag.encode()),Name=(12,text(name)),XP=(8,50.0),EntryList=(15,[node(ID=(4,10),Text=(12,text(instruction)),End=(0,0)),node(ID=(4,90),Text=(12,text('Thank you for completing '+name+'.')),End=(0,1))]))
    records=[('module',2014,doc('IFO',Mod_Name=(12,text('Two Native Missions')),Mod_Description=(12,text('Help Mara and Oren.')))),
      ('keep',2012,doc('ARE',Name=(12,text('Old Keep')),Tag=(10,b'keep'),Tileset=(11,b'tin01'),Width=(5,4),Height=(5,3))),
      ('keep',2023,write(b'GIT V3.2',node(**{'Creature List':(15,[mara,oren])}))),
      ('mara',2027,write(b'UTC V3.2',mara)),('oren',2027,write(b'UTC V3.2',oren)),
      ('seal_item',2025,doc('UTI',Tag=(10,b'seal_item'),LocalizedName=(12,text('Royal Seal')))),
      ('module',2056,doc('JRL',Categories=(15,[quest('seal','Royal Seal','Recover the Royal Seal.'),quest('patrol','A Quiet Patrol','Visit Old Keep.')]))),
      dialogue('mara','the Royal Seal','seal_action'),dialogue('oren','the patrol','patrol_action')]
    if scripts is None:
        records += [('seal_action',2010,ncs(integer(10)+string('seal')+action(0,2)+integer(40)+integer(0)+action(1,2)+integer(75)+integer(0)+action(2,2)+b'\x20\x00')),
                    ('patrol_action',2010,ncs(integer(10)+string('patrol')+action(0,2)+integer(10)+integer(0)+action(1,2)+b'\x20\x00'))]
    else:records+=scripts
    return archive(records)


def enable(m):
    m.update(mode='studio',risk_acknowledged=True,objectives_reviewed=True,rewards_reviewed=True)


class GeneralMissions(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'two.mod';self.path.write_bytes(synthetic())
        self.report,_=build_report(self.path,{},actions=ACTIONS);self.report['module']['filename']='two.mod'
        self.p=plan(self.report);self.p['mission_control']=dict(version=1,missions=[draft(self.report,t,self.path) for t in ('seal','patrol')])

    def test_arbitrary_journals_copy_to_independent_inactive_drafts(self):
        a,b=self.p['mission_control']['missions']
        self.assertEqual(active_all(self.p),[]);self.assertEqual(a['quest']['giver'],'mara');self.assertEqual(b['quest']['giver'],'oren')
        self.assertEqual(a['quest']['steps'][0]['kind'],'retrieve');self.assertEqual(a['quest']['steps'][0]['target'],'seal_item')
        self.assertEqual(b['quest']['steps'][0]['kind'],'visit');self.assertEqual(a['quest']['gold'],40);self.assertEqual(a['quest']['xp'],75)
        self.assertFalse(a['objectives_reviewed']);validate_profile(self.p)
        enable(a);validate(self.p['mission_control'],self.report,catalog(self.report,self.path)['targets'])
        self.assertEqual([m['source_tag'] for m in active_all(self.p)],['seal']);self.assertEqual(b['mode'],'original')

    def test_unknown_objectives_and_ambiguous_rewards_require_review(self):
        r=copy.deepcopy(self.report);r['quests'][0]['entries'][0]['text']='Discover what happened on the night of the eclipse.'
        s=next(s for s in r['scripts'] if s['id']=='seal_action');s['calls'].append(dict(s['calls'][1],offset=999));s['calls_total']+=1
        m=draft(r,'seal',self.path);self.assertEqual(m['quest']['steps'][0]['kind'],'review');self.assertEqual(m['quest']['gold'],0)
        value=dict(version=1,missions=[m]);validate(value,r)
        enable(m)
        with self.assertRaisesRegex(ValueError,'choose an objective'):validate(value,r)

    def test_validation_rejects_unreviewed_wrong_source_duplicate_targets_and_forgery(self):
        m=self.p['mission_control']['missions'][0];m['mode']='studio'
        with self.assertRaisesRegex(ValueError,'Acknowledge'):validate(self.p['mission_control'],self.report)
        m['risk_acknowledged']=True
        with self.assertRaisesRegex(ValueError,'review'):validate(self.p['mission_control'],self.report)
        enable(m);targets=catalog(self.report,self.path)['targets']
        for mutate in [lambda v:v['missions'].append(copy.deepcopy(v['missions'][0])),lambda v:v['missions'][0].update(source_sha256='0'*64),lambda v:v['missions'][0]['quest'].update(gold=True),lambda v:v['missions'][0]['quest']['steps'][0].update(target='missing'),lambda v:v['missions'][0].update(offsets=[1]),lambda v:v['missions'][0]['quest'].update(giver='oren')]:
            v=copy.deepcopy(self.p['mission_control']);mutate(v)
            with self.assertRaises(ValueError):validate(v,self.report,targets)

    def test_shared_and_dynamic_scripts_stay_native_but_can_be_drafted(self):
        r=copy.deepcopy(self.report);s=next(s for s in r['scripts'] if s['id']=='seal_action')
        s['calls'][0]['arguments'][0]=None
        info=inspect(r,'seal',self.path);self.assertFalse(info['controllable']);self.assertTrue(info['supported'])
        r=copy.deepcopy(self.report);a=next(s for s in r['scripts'] if s['id']=='seal_action');b=next(s for s in r['scripts'] if s['id']=='patrol_action')
        a['calls'].append(dict(name='ExecuteScript',arguments=['common_reward',None],offset=999));b['calls'].append(dict(name='ExecuteScript',arguments=['common_reward',None],offset=999))
        r['scripts'].append(dict(id='common_reward',status='decoded',calls=[dict(name='GiveGoldToCreature',arguments=[None,10],offset=30)],functions={}))
        self.assertTrue(any('shared' in reason for reason in inspect(r,'seal')['blockers']))

    def test_inactive_general_drafts_never_patch_resources_or_inject_runtime(self):
        archive=Archive(self.path);entries={key:archive.get(*key) for key in archive.index};original=copy.deepcopy(entries);scripts={}
        audit=apply(entries,self.report,self.p,scripts,ACTIONS,self.path)
        self.assertEqual(entries,original);self.assertEqual(scripts,{});self.assertEqual(audit['missions'],[])

    def test_duplicate_placed_targets_require_a_manual_unambiguous_giver(self):
        report=copy.deepcopy(self.report);report['characters'].append(copy.deepcopy(next(c for c in report['characters'] if c['tag']=='mara' and c['kind']=='placed')))
        m=draft(report,'seal',self.path);self.assertEqual(m['quest']['giver'],'');enable(m)
        with self.assertRaisesRegex(ValueError,'quest giver'):validate(dict(version=1,missions=[m]),report)

    def test_ai_context_is_per_mission_observed_state_and_does_not_leak_future_steps(self):
        a,b=self.p['mission_control']['missions'];enable(a);enable(b);a['quest']['steps'][-1]['description']='SECRET_FUTURE'
        snapshot=dict(imported_missions={a['quest']['id']:dict(state=0,ready=0),b['quest']['id']:dict(state=1,ready=0)})
        ctx,verbs=ai_context(self.p,dict(native_tag='mara'),snapshot)
        self.assertEqual(verbs,[a['quest']['id']+':start']);self.assertNotIn('SECRET_FUTURE',json.dumps(ctx))
        snapshot['imported_missions'][a['quest']['id']]=dict(state=2,ready=1)
        self.assertEqual(ai_context(self.p,dict(native_tag='mara'),snapshot)[1],[a['quest']['id']+':claim'])
        self.assertEqual(ai_context(self.p,dict(native_tag='oren'),snapshot)[1],[])
        snapshot['imported_missions'][a['quest']['id']]=dict(state=True,ready=1)
        self.assertEqual(ai_context(self.p,dict(native_tag='mara'),snapshot)[1],[])

    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_visual_draft_edits_roundtrip(self):
        result=subprocess.run(['node','tests/general_mission_fixture.js'],input=json.dumps(dict(project=self.p,metadata=catalog(self.report,self.path))),text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr);p=json.loads(result.stdout);validate_profile(p)
        self.assertEqual(p['mission_control']['missions'][0]['quest']['gold'],123)


class BytecodeEdits(unittest.TestCase):
    def test_shared_script_retains_other_quests_journal_calls(self):
        raw=ncs(integer(10)+string('seal')+action(0,2)+integer(20)+string('patrol')+action(0,2)+b'\x20\x00')
        offset=analyse(raw,ACTIONS)['calls'][0]['offset'];result=analyse(suppress(raw,ACTIONS,{offset:'AddJournalQuestEntry'}),ACTIONS)
        self.assertEqual([c['arguments'] for c in result['calls']],[['patrol',20]])

    def test_scoped_void_calls_keep_argument_evaluation_and_relocate_branches(self):
        # Forward branch over a call and backwards branch to its first argument.
        args=integer(10)+string('seal');call_at=19+len(args)
        raw=ncs(b'\x1d\x00'+struct.pack('>i',6)+args+action(0,2)+b'\x1d\x00'+struct.pack('>i',-(len(args)+5))+b'\x20\x00')
        original=analyse(raw,ACTIONS,True);patched=suppress(raw,ACTIONS,{call_at:'AddJournalQuestEntry'});result=analyse(patched,ACTIONS,True)
        self.assertEqual(result['status'],'decoded');self.assertEqual(result['calls'],[])
        self.assertEqual([r['operand'] for r in result['bytecode'] if r['op']=='MOVSP'],[-8])
        self.assertEqual([r['target'] for r in result['bytecode'] if 'target' in r],[19,19])
        self.assertEqual(result['strings'],original['strings'])

    def test_fail_closed_on_partial_wrong_call_deferred_and_nonvoid_signatures(self):
        raw=ncs(integer(10)+string('seal')+action(0,2)+b'\x20\x00');offset=analyse(raw,ACTIONS)['calls'][0]['offset']
        with self.assertRaises(ValueError):suppress(raw,ACTIONS,{offset:'GiveGoldToCreature'})
        with self.assertRaises(ValueError):suppress(ncs(b'\xff\x00'),ACTIONS,{13:'AddJournalQuestEntry'})
        with self.assertRaisesRegex(ValueError,'Deferred'):suppress(ncs(b'\x2c\x10'+b'\0'*8+b'\x20\x00'),ACTIONS,{})
        actions=copy.deepcopy(ACTIONS);actions[0]['return']='int'
        with self.assertRaisesRegex(ValueError,'signature'):suppress(raw,actions,{offset:'AddJournalQuestEntry'})


class GeneralBuild(unittest.TestCase):
    def test_actual_compiler_multi_mission_copy_preserves_other_quest_and_original(self):
        cfg=defaults()
        game=cfg.get('game_root','')
        if not Path(cfg.get('compiler','')).is_file() or not game or not any((Path(game)/'data'/name).is_file() for name in ('nwn_base.key','nwn_retail.key')):
            self.skipTest('Installed NWN game archives and compiler required')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'src';src.mkdir();out=root/'ncs';out.mkdir()
            for name,tag,gold in [('seal_action','seal',40),('patrol_action','patrol',10)]:
                (src/(name+'.nss')).write_text('void main(){object pc=GetPCSpeaker();AddJournalQuestEntry("'+tag+'",10,pc,TRUE,FALSE,TRUE);GiveGoldToCreature(pc,'+str(gold)+');GiveXPToCreature(pc,75);SetLocalInt(pc,"NATIVE_SIDE_EFFECT",1);}')
            result=subprocess.run([cfg['compiler'],'-n',cfg['game_root'],'-b',str(out),*[f.name for f in src.glob('*.nss')]],cwd=src,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            records=[(f.stem,2009,f.read_bytes()) for f in src.glob('*.nss')]+[(f.stem,2010,f.read_bytes()) for f in out.glob('*.ncs')]+[('seal_action',2064,b'original debug data')]
            path=root/'original.mod';path.write_bytes(synthetic(records));original=path.read_bytes();before=Archive(path)
            r,_=build_report(path,cfg);r['module']['filename']=path.name
            p=plan(r);p['mission_control']=dict(version=1,missions=[draft(r,t,path) for t in ('seal','patrol')]);a,b=p['mission_control']['missions'];enable(a)
            a['quest'].update(gold=321,xp=654);a['quest']['steps'][0]['consume']=True
            result=build(path,r,p,Store(root/'store'),cfg);built=Archive(Path(result['path']));folder=Path(result['path']).parent
            for key in before.index:
                if key[1] in (2012,2023,2027,2025) or key[0]=='patrol_action':self.assertEqual(built.get(*key),before.get(*key),key)
            original_jrl=gff(before.get('module',2056));new_jrl=gff(built.get('module',2056))
            self.assertEqual(original_jrl['Categories'][1],new_jrl['Categories'][1])
            self.assertEqual(path.read_bytes(),original);self.assertNotIn(('seal_action',2009),built.index)
            self.assertEqual((folder/'original-scripts/seal_action.nss').read_bytes(),before.get('seal_action',2009))
            self.assertNotIn(('seal_action',2064),built.index);self.assertEqual((folder/'original-scripts/seal_action.ndb').read_bytes(),b'original debug data')
            actions=prototypes(Resources(path,cfg).get('nwscript',2009)[0]);native=analyse(built.get('seal_action',2010),actions)
            self.assertNotIn('GiveGoldToCreature',native['functions']);self.assertIn('SetLocalInt',native['functions'])
            self.assertIn(('rwg_death',2010),built.index);self.assertIn(('rwg_menu',2029),built.index)
            audit=json.loads((folder/'preservation.json').read_text());self.assertTrue(audit['maps_byte_identical']);self.assertEqual(len(audit['mission_takeover']['general']['missions']),1)
            # A second build manages both missions, with distinct state keys and
            # no Snow Hunt resources or test module data added to the application.
            enable(b);p['module_name']='both_missions'
            second=build(path,r,p,Store(root/'both'),cfg);both=Archive(Path(second['path']))
            config=both.get('aw_config',2009).decode();self.assertIn(a['quest']['id'],config);self.assertIn(b['quest']['id'],config)


if __name__=='__main__':unittest.main()
