import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rwstudio.authoring import seed, validate, review
from rwstudio.authoring_ai import generate
from rwstudio.builder import ROOT, build_project
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources
from rwstudio.provider import Provider
from rwstudio.storage import Store

GAME = Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER = ROOT / 'vendor/nwnsc/nwnsc.exe'


def edited_project():
    project = seed()
    # Generation is stubbed at the provider boundary: no paid API call or key.
    response = copy.deepcopy(project)
    response['quests'][1]['name'] = 'A generated mission'
    with patch.object(Provider, 'request', return_value=response):
        proposal = generate(Provider('unused'), project, 'Revise the missions', 'quests')['proposal']
    result = subprocess.run(['node', 'tests/mission_editor_checks.js'], input=json.dumps(proposal),
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


@unittest.skipUnless(shutil.which('node'), 'Node required for browser adapter checks')
class MissionEditorTests(unittest.TestCase):
    def test_controller_history_confirmations_and_save_object_replacement(self):
        result = subprocess.run(['node', 'tests/mission_controller_checks.js'], input=json.dumps(seed()),
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_generated_missions_remain_valid_after_visual_edits_and_save(self):
        project = edited_project()
        self.assertEqual(validate(project, True), project)
        self.assertEqual(review(project)['errors'], [])
        with tempfile.TemporaryDirectory() as root:
            store = Store(Path(root))
            store.save(project)
            saved = store.get(project['id'])
        self.assertEqual(saved, project)
        self.assertEqual(saved['quests'][1]['gold'], 321)
        self.assertEqual(saved['quests'][1]['name'], 'A generated mission')
        self.assertEqual(saved['quests'][1]['steps'][-1]['name'], 'Tell Ilyra the outcome')
        self.assertNotIn('mission_graph', saved)

    def test_applied_ai_missions_open_editor_and_retain_undo_draft(self):
        script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert'),els={};
const ctx={console,window:{},document:{querySelector:s=>els[s]??={close(){}},querySelectorAll:()=>[]}};
vm.createContext(ctx);const source=fs.readFileSync('web/editor.js','utf8');
vm.runInContext(source.slice(0,source.indexOf("$('#saveProject').onclick")),ctx);
ctx.fixture=JSON.parse(process.argv[1]);
ctx.render=()=>{};ctx.scrollWorkspaceTop=()=>{};ctx.notify=()=>{};
vm.runInContext(source.slice(source.indexOf("$('#applyProposal').onclick="),source.indexOf("$('#newProject').onclick=")),ctx);
for(const scope of ['quests','adventure','story']){
  vm.runInContext("project=clone(fixture);page='brief';proposal={scope:'"+scope+"',proposal:clone(fixture),review:{}};proposal.proposal.quests[0].name='Generated mission';",ctx);
  els['#applyProposal'].onclick();
  assert.equal(vm.runInContext('page',ctx),scope==='story'?'brief':'quests');
  assert.equal(vm.runInContext('project.quests[0].name',ctx),'Generated mission');
  assert.notEqual(vm.runInContext('previousDraft.quests[0].name',ctx),'Generated mission');
  assert(vm.runInContext('dirty',ctx));
}
"""
        result = subprocess.run(['node', '-e', script, json.dumps(seed())], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(shutil.which('node') and GAME.is_dir() and COMPILER.is_file(), 'NWN/compiler/Node required')
class NativeMissionEditorTests(unittest.TestCase):
    def test_visual_branch_and_reward_edits_compile_into_native_module(self):
        project = edited_project()
        with tempfile.TemporaryDirectory() as root:
            manifest = build_project(project, Store(Path(root)), GAME, COMPILER)
            native = {(n, k): b for n, k, b in resources(Path(manifest['path']).read_bytes())}
        self.assertIn(b'seal_bell', native['aqa_1_2_0', 2009])
        self.assertIn(b'restore_bell', native['aqa_1_2_1', 2009])
        self.assertIn(b'Tell Ilyra the outcome', native['aw_config', 2009])
        self.assertIn(b'321', native['aw_config', 2009])
        self.assertIn(b'654', native['aw_config', 2009])
        self.assertIn(b'The valley remembers your choice.', native['aw_config', 2009])
        dialogue = read(native['ilyra', 2029])[1]
        self.assertIn(b'Choose the sealed path', native['ilyra', 2029])
        self.assertTrue(dialogue[1]['ReplyList'][1])
        self.assertIn(('aqa_1_2_0', 2010), native)
        self.assertIn(('aw_quest', 2009), native)
