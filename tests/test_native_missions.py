import copy
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from test_module_analyser import fixture, archive, ACTIONS
from rwstudio.builder import ROOT
from rwstudio.conversion_missions import workspace, validate, review, evidence, patch_journals
from rwstudio.imported_module import plan, npc_reply
from rwstudio.module_analysis import build_report, sha256
from rwstudio.module_conversion import build, validate_plan_for_report
from rwstudio.module_analyser import ModuleAnalyser
from rwstudio.nwn.analysis_formats import Archive, gff
from rwstudio.nwn.gff import read, write, text
from rwstudio.storage import Store, write_json


class NativeMissions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.path = self.root / 'original.mod'
        self.path.write_bytes(fixture()); self.report, _ = build_report(self.path, {}, actions=ACTIONS)
        self.report['module']['filename'] = 'original.mod'
        self.p = plan(self.report); self.p['mission_editor'] = workspace(self.report)

    def test_old_profile_upgrades_without_discarding_creators_fields_and_saves(self):
        manager = ModuleAnalyser(self.root / 'analysis'); ident = manager.begin('original.mod')
        (manager.folder(ident) / 'input.mod').write_bytes(self.path.read_bytes())
        write_json(manager.folder(ident) / 'report.json', self.report); manager.update(ident, status='complete')
        old = plan(self.report); old['npcs'][0]['personality'] = 'Creator edited personality'
        write_json(manager.folder(ident) / 'conversion-plan.json', old)
        loaded = manager.conversion_plan(ident)
        self.assertEqual(loaded['project']['npcs'][0]['personality'], old['npcs'][0]['personality'])
        edited = loaded['project']; edited['mission_editor']['storyline'] = 'Private plot outline'
        edited['mission_editor']['quests'][0]['stages'][0]['text'] = 'A reviewed instruction.'
        manager.save_conversion(ident, edited, {})
        self.assertEqual(manager.conversion_plan(ident)['project'], edited)
        self.assertEqual(len(manager.review_missions(ident, edited)['journal_changes']), 1)
        self.assertEqual(self.path.read_bytes(), fixture())

    def test_ids_completion_flags_and_unknown_fields_are_not_editable(self):
        wrong_version = copy.deepcopy(self.p['mission_editor']); wrong_version['version'] = True
        with self.assertRaises(ValueError): validate(wrong_version)
        for field, value in [('tag', 'different'), ('source', '../../other.jrl/Categories[0]'), ('id', 'nq_4')]:
            p = copy.deepcopy(self.p); p['mission_editor']['quests'][0][field] = value
            with self.assertRaises(ValueError): validate_plan_for_report(p, self.report)
        for field, value in [('native_id', 99), ('end', True), ('id', 's_9')]:
            p = copy.deepcopy(self.p); p['mission_editor']['quests'][0]['stages'][0][field] = value
            with self.assertRaises(ValueError): validate_plan_for_report(p, self.report)
        p = copy.deepcopy(self.p); p['mission_editor']['quests'][0]['xp'] = 99999
        with self.assertRaises(ValueError): validate_plan_for_report(p, self.report)
        p = copy.deepcopy(self.p); p['mission_editor']['quests'][0]['stages'].reverse()
        with self.assertRaises(ValueError): validate_plan_for_report(p, self.report)

    def test_no_guessed_sequence_and_compiled_evidence_is_separated_from_string_match(self):
        w = self.p['mission_editor']; self.assertEqual(w['links'], [])
        sources = evidence(self.report, self.path)['nq_0']
        self.assertTrue(any(e['confidence'] == 'string association' for e in sources['sources']))
        self.assertEqual([e['script'] for e in sources['stages']['s_0']], ['quest_start'])
        self.assertEqual(sources['stages']['s_1'], [])
        w['links'] = [dict(**{'from': 'nq_0:s_0', 'to': 'nq_0:s_1'}, label='Reviewed route')]
        self.assertEqual(review(w, self.report)['journal_changes'], [])
        w['links'][0]['to'] = 'nq_0:missing'
        with self.assertRaises(ValueError): validate(w, self.report)

    def test_old_saved_reports_recover_native_dialogue_journal_fields(self):
        source = Archive(self.path); entries = [(n, k, source.get(n, k)) for n, k in source.index]
        kind, dialogue = read(source.get('mara_talk', 2029))
        reply = dialogue[1]['ReplyList'][1][0][1]
        reply['Quest'] = (10, b'seal'); reply['QuestEntry'] = (4, 20)
        self.path.write_bytes(archive([(n, k, write(kind, dialogue) if (n, k) == ('mara_talk', 2029) else data) for n, k, data in entries]))
        new, _ = build_report(self.path, {}, actions=ACTIONS)
        old = copy.deepcopy(new)
        for d in old['dialogues']:
            for line in d['lines']:
                line.pop('quest', None); line.pop('quest_entry', None)
        recovered = evidence(old, self.path)
        self.assertEqual(recovered, evidence(new, self.path))
        self.assertTrue(any(e['confidence'] == 'journal field' for e in recovered['nq_0']['stages']['s_1']))

    def test_journal_patch_preserves_all_unedited_fields_and_language_variants(self):
        archive = Archive(self.path); entries = OrderedDict((key, archive.get(*key)) for key in archive.index)
        kind, root = read(entries['module', 2056])
        category = root[1]['Categories'][1][0]; category[1]['XP'] = (8, 123.5)
        original = b'Original French'; category[1]['Name'] = (12, struct.pack('<II', 0xffffffff, 2)+struct.pack('<II', 0, 9)+b'Lost Seal'+struct.pack('<II', 2, len(original))+original)
        entries['module', 2056] = write(kind, root); before = copy.deepcopy(entries)
        w = self.p['mission_editor']; w['quests'][0]['name'] = 'A new quest title'; w['quests'][0]['stages'][0]['text'] = 'Changed instructions.'
        edits = patch_journals(entries, self.report, w)
        self.assertEqual(len(edits['module']), 2)
        for key in entries:
            if key != ('module', 2056): self.assertEqual(entries[key], before[key])
        changed = read(entries['module', 2056])[1][1]['Categories'][1][0]
        self.assertIn(original, changed[1]['Name'][1]); self.assertEqual(changed[1]['XP'], category[1]['XP'])
        self.assertEqual(changed[1]['EntryList'][1][1], category[1]['EntryList'][1][1])
        self.assertEqual(changed[1]['EntryList'][1][0][1]['ID'], (4, 10))
        self.assertEqual(changed[1]['EntryList'][1][0][1]['End'], (0, 0))

    def test_unchanged_and_notes_only_preserve_journal_bytes(self):
        archive = Archive(self.path); entries = OrderedDict((key, archive.get(*key)) for key in archive.index)
        before = copy.deepcopy(entries); w = self.p['mission_editor']; w['storyline'] = 'Private outline'
        w['quests'][0]['stages'][0]['notes'] = 'A private possibility'
        self.assertEqual(patch_journals(entries, self.report, w), {})
        self.assertEqual(entries, before)

    def test_private_story_and_journal_endings_are_not_given_to_gameplay_ai(self):
        self.p['mission_editor']['storyline'] = 'SECRET_PRIVATE_STORY'
        self.p['mission_editor']['quests'][0]['stages'][1]['text'] = 'SECRET_JOURNAL_ENDING'
        provider = Mock(); provider.request.return_value = dict(reply='Hello.', action='none', companion_action='', task_target='', task_question='', task_item='', task_quantity='')
        npc_reply(provider, self.p, self.p['npcs'][0]['id'], 'What is happening?', {})
        prompt = json.dumps(provider.request.call_args.args[1])
        self.assertNotIn('SECRET_', prompt); self.assertNotIn('mission_editor', prompt)
        from rwstudio.companions import context
        from test_companions import snapshot
        ctx = context(self.p, snapshot('party', self.p['npcs'][0]['id'], 1), self.p['npcs'][0]['id'])
        self.assertNotIn('SECRET_', json.dumps(ctx))

    def test_copy_exports_requested_journal_edits_with_truthful_preservation_report(self):
        self.p['mission_editor']['quests'][0]['stages'][0]['text'] = 'Edited native journal text.'
        game = self.root / 'game'; (game / 'data').mkdir(parents=True); compiler = self.root / 'compiler'; compiler.touch()
        cfg = dict(game_root=str(game), compiler=str(compiler))
        def runtime(p, digest, game, hooks):
            return {'sp_config': f'string SPBuild(){{return "{digest}";}}', **{n: 'void main(){}' for n in ('rwc_load', 'rwc_enter', 'rwc_beat', 'rwc_chat')}}, {}
        def compile(args, **kw):
            for f in Path(kw['cwd']).glob('*.nss'):
                if 'void main(' in f.read_text(): (Path(args[args.index('-b')+1]) / (f.stem+'.ncs')).write_bytes(b'NCS fixture')
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        before = sha256(self.path); store = Store(self.root / 'store')
        with patch('rwstudio.module_conversion.runtime', side_effect=runtime), patch('rwstudio.module_conversion.subprocess.run', side_effect=compile), patch('rwstudio.player_package.export_keys', return_value=[]):
            built = build(self.path, self.report, self.p, store, cfg)
        folder = Path(built['path']).parent; converted = Archive(Path(built['path'])); original = Archive(self.path)
        for key in original.index:
            if key not in {('module', 2014), ('module', 2056), ('mara_talk', 2029)}: self.assertEqual(converted.get(*key), original.get(*key))
        self.assertIn(b'Edited native journal text.', converted.get('module', 2056))
        result = json.loads((folder / 'preservation.json').read_text())
        self.assertFalse(result['quests_byte_identical']); self.assertTrue(result['journal_structure_preserved']); self.assertTrue(result['original_scripts_byte_identical'])
        self.assertEqual(result['journal_text_edits']['module'][0]['entry'], 10); self.assertEqual(sha256(self.path), before)

    @unittest.skipUnless(shutil.which('node'), 'Node required')
    def test_browser_graph_edits_roundtrip_to_native_journal(self):
        payload = dict(project=self.p, baseline=workspace(self.report), evidence=evidence(self.report, self.path))
        result = subprocess.run(['node', 'tests/native_mission_checks.js'], input=json.dumps(payload), cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        edited = validate_plan_for_report(json.loads(result.stdout), self.report)
        self.assertEqual(len(review(edited['mission_editor'], self.report)['journal_changes']), 2)


if __name__ == '__main__': unittest.main()
