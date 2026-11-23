import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from rwstudio.managed_missions import SNOW_SHA, draft, empty, validate, active, ai_context, catalog, update_memory, SCRIPT_HASHES
from rwstudio.managed_mission_runtime import apply
from rwstudio.nwn.analysis_formats import Archive
from rwstudio.nwn.gff import read
from rwstudio.builder import ROOT
from rwstudio.module_conversion import build
from rwstudio.module_analyser import ModuleAnalyser
from rwstudio.storage import Store
from rwstudio.server import defaults


def report():
    return dict(module=dict(sha256=SNOW_SHA),quests=[dict(tag='j_ogre')])


class ManagedMissions(unittest.TestCase):
    def setUp(self):
        self.m=draft(report(),'j_ogre');self.value=dict(version=1,missions=[self.m])

    def test_default_is_native_and_takeover_requires_explicit_acknowledgement(self):
        self.assertEqual(self.m['mode'],'original');self.assertIsNone(active({'mission_control':self.value}))
        self.m['mode']='studio'
        with self.assertRaisesRegex(ValueError,'Acknowledge'):validate(self.value,report())
        self.m['risk_acknowledged']=True;validate(self.value,report())
        changed=report();changed['module']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'match'):validate(self.value,changed)
        with self.assertRaises(ValueError):draft(report(),'j_ring')

    def test_objectives_rewards_targets_and_native_handin_are_validated(self):
        self.m['quest']['gold']=9876;self.m['quest']['xp']=4321
        self.m['quest']['steps'].pop(0);validate(self.value,report())
        targets=dict(retrieve=[dict(id='ogrehead001')],talk=[dict(id='oberagh001')],visit=[],defeat=[])
        validate(self.value,report(),targets)
        for mutate in [lambda m:m['quest'].update(xp=True),lambda m:m['quest']['steps'][0].update(target='missing'),
                       lambda m:m['quest']['steps'][0].update(next=m['quest']['steps'][0]['id']),
                       lambda m:m['quest']['steps'][-1].update(target='other_npc'),
                       lambda m:m['rewards'].update(treasure_chest='yes')]:
            invalid=copy.deepcopy(self.value);mutate(invalid['missions'][0])
            with self.assertRaises(ValueError):validate(invalid,report(),targets)

    def test_native_mode_does_not_patch_or_export_executable_actions(self):
        entries={('untouched',2010):b'original'};before=copy.deepcopy(entries);scripts={}
        result=apply(entries,report(),{'mission_control':self.value},scripts)
        self.assertEqual(entries,before);self.assertEqual(scripts,{});self.assertEqual(result['scripts'],[])

    def test_unknown_bytecode_is_never_replaced_even_with_optin(self):
        self.m.update(mode='studio',risk_acknowledged=True)
        with self.assertRaisesRegex(ValueError,'audited native script'):
            apply({},report(),{'mission_control':self.value},{})

    def test_ai_receives_observed_current_objective_and_only_revalidated_actions(self):
        self.m.update(mode='studio',risk_acknowledged=True);self.m['quest']['steps'][1]['description']='UNREACHED_SECRET'
        p=dict(mission_control=self.value);owner=dict(native_tag='oberagh001');other=dict(native_tag='other')
        ctx,actions=ai_context(p,owner,dict(managed_mission=dict(state=1,ready=0)))
        self.assertNotIn('UNREACHED_SECRET',json.dumps(ctx));self.assertEqual(actions,[])
        _,actions=ai_context(p,owner,dict(managed_mission=dict(state=0,ready=0)));self.assertEqual(actions,['rwm_start'])
        _,actions=ai_context(p,owner,dict(managed_mission=dict(state=3,ready=1)));self.assertEqual(actions,['rwm_claim'])
        _,actions=ai_context(p,other,dict(managed_mission=dict(state=3,ready=1)));self.assertEqual(actions,[])
        self.assertEqual(ai_context(p,owner,dict(managed_mission=dict(state=999,ready=1))),(None,[]))
        self.m['mode']='original';self.assertEqual(ai_context(p,owner,dict(managed_mission=dict(state=3,ready=1))),(None,[]))

    def test_changed_dialogue_is_the_memory_library_for_future_recall(self):
        self.m.update(mode='studio',risk_acknowledged=True);self.m['quest']['description']='An edited agreement'
        p=dict(mission_control=self.value,npcs=[dict(native_tag='oberagh001',native_lines=[dict(id='cl_oberagh001:e:3',text='Old agreement'),dict(id='cl_oberagh001:e:6',text='Unrelated bounty clue')])])
        update_memory(p);self.assertIn('An edited agreement',p['npcs'][0]['native_lines'][0]['text'])
        self.assertEqual(p['npcs'][0]['native_lines'][1]['text'],'Unrelated bounty clue')

    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_visual_objective_edits_roundtrip(self):
        result=subprocess.run(['node','tests/managed_mission_checks.js'],input=json.dumps(self.m),text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        self.value['missions'][0]=json.loads(result.stdout);validate(self.value,report())
        self.assertEqual(self.value['missions'][0]['quest']['gold'],321)


SOURCE=ROOT/'data/module-analysis/c8e36445abc54fd184fe3837c8f588b8/input.mod'
@unittest.skipUnless(SOURCE.is_file() and (ROOT/'vendor/nwnsc/nwnsc.exe').is_file(),'Local authorized Snow Hunt fixture/compiler required')
class SnowHuntMissionBuild(unittest.TestCase):
    def test_edited_objectives_and_rewards_compile_without_touching_other_maps_quests_or_scripts(self):
        manager=ModuleAnalyser(SOURCE.parent.parent);ident=SOURCE.parent.name;r=manager.report(ident)
        p=manager.conversion_plan(ident)['project'];p['module_name']='rw_ogre_check';p['mission_control']=dict(version=1,missions=[draft(r,'j_ogre')]);m=p['mission_control']['missions'][0]
        m.update(mode='studio',risk_acknowledged=True);m['quest'].update(gold=321,xp=654)
        m['quest']['steps'].pop(0) # A real objective change: head possession + return, no explicit kill requirement.
        m['rewards'].update(treasure_chest=False,negotiation=False,defeat_xp=0)
        cfg=defaults();cfg.update(json.loads((ROOT/'data/settings.json').read_text(encoding='utf-8')))
        cfg['analysis_bundle_root']=json.loads((SOURCE.parent/'dependency-location.json').read_text())['folder']
        original=Archive(SOURCE);before=SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            built=build(SOURCE,r,p,Store(Path(temp)),cfg);result=Archive(Path(built['path']));folder=Path(built['path']).parent
            for name,kind in original.index:
                if kind in (2012,2023,2027,2040,2025):self.assertEqual(result.get(name,kind),original.get(name,kind),(name,kind))
                if kind in (2009,2010) and name not in SCRIPT_HASHES:self.assertEqual(result.get(name,kind),original.get(name,kind),name)
            old=read(original.get('module',2056))[1];new=read(result.get('module',2056))[1]
            self.assertEqual(old[1]['Categories'][1][:2],new[1]['Categories'][1][:2])
            self.assertEqual(len(new[1]['Categories'][1][2][1]['EntryList'][1]),3)
            config=result.get('aw_config',2009).decode();self.assertIn('321',config);self.assertIn('654',config)
            self.assertIn('RWMClaim',result.get('sca_oberagh001',2009).decode())
            self.assertNotIn('AddJournalQuestEntry',result.get('sk_dthobzul001',2009).decode())
            self.assertIn('craft_drop_items',result.get('sk_dthobzul001',2009).decode())
            self.assertIn(('rwm_start',2010),result.index);self.assertIn(('rwm_ready',2010),result.index)
            dlg=read(result.get('cl_oberagh001',2029))[1][1]
            post=dlg['EntryList'][1][16][1]['RepliesList'][1]
            self.assertTrue(any(link[1]['Index'][1]==21 and link[1]['Active']==(11,b'rwm_bonus') for link in post))
            self.assertEqual(dlg['ReplyList'][1][21][1]['EntriesList'][1][0][1]['Active'],(11,b'scc_chkper002'))
            pres=json.loads((folder/'preservation.json').read_text());self.assertFalse(pres['original_scripts_byte_identical'])
            self.assertTrue(pres['maps_byte_identical']);self.assertTrue(pres['mission_takeover']['unmanaged_quests_unchanged'])
            for name in SCRIPT_HASHES:self.assertEqual((folder/'original-scripts'/(name+'.ncs')).read_bytes(),original.get(name,2010))
        self.assertEqual(SOURCE.read_bytes(),before)


if __name__=='__main__':unittest.main()
