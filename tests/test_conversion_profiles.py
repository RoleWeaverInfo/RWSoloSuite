import copy
import json
import tempfile
import time
import unittest
from collections import OrderedDict
from pathlib import Path
from unittest.mock import Mock,patch
from test_module_analyser import fixture, ACTIONS
from rwstudio.module_analysis import build_report, Resources
from rwstudio.imported_module import plan, npc_reply
from rwstudio.conversion_profiles import evidence, generate, learned, refresh
from rwstudio.module_conversion import patch_dialogues
from rwstudio.nwn.gff import read, write
from rwstudio.builder import conversation


class Profiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'original.mod';self.path.write_bytes(fixture())
        self.report,_=build_report(self.path,{},actions=ACTIONS)
        self.p=plan(self.report);self.n=self.p['npcs'][0]

    def test_generation_has_public_evidence_and_creative_background_but_no_gated_spoilers(self):
        self.assertIn('cautious keeper',evidence(self.report,self.n)['description'])
        self.assertEqual(evidence(self.report,self.n)['opening_voice'],[]) # Gated opening.
        provider=Mock()
        def request(system,context,schema,**kw):
            self.assertNotIn('missing seal from the cave',json.dumps(context))
            self.assertNotIn('The seal is returned',json.dumps(context))
            return {'characters':[dict(id=n['id'],role='Keeper',personality='Patient and methodical.',background='She keeps careful records and prefers an orderly household.',motivation='Preserve the keep.') for n in context['characters']]}
        provider.request.side_effect=request
        p=generate(provider,self.p,self.report)
        self.assertIn('careful records',p['npcs'][0]['background'])
        self.assertEqual(p['npcs'][0]['knowledge'],self.n['knowledge'])
        self.assertEqual(self.n['background'],'A cautious keeper who knows the lost seal.')
        self.assertIn('creative elaboration',p['npcs'][0]['profile_origin'])

    def test_invalid_generation_preserves_input_and_creator_edits_survive_refresh(self):
        before=copy.deepcopy(self.p);provider=Mock();provider.request.return_value={'characters':[]}
        with self.assertRaisesRegex(ValueError,'mismatched'):generate(provider,self.p,self.report)
        self.assertEqual(before,self.p)
        self.n['knowledge']='A reviewed fact from the creator.';self.n['personality']='Bold.'
        upgraded=refresh(self.p,self.report)
        self.assertEqual(upgraded['npcs'][0]['knowledge'],self.n['knowledge'])
        self.assertEqual(upgraded['npcs'][0]['personality'],'Bold.')

    def test_reached_dialogue_only_in_prompt_and_old_quest_conversation_is_recalled(self):
        provider=Mock();provider.request.return_value=dict(reply='Yes.',action='none',companion_action='',task_target='',task_question='',task_item='',task_quantity='')
        npc_reply(provider,self.p,self.n['id'],'Where is the seal?',{})
        before=provider.request.call_args.args[1]
        self.assertNotIn('missing seal from the cave',json.dumps(before))
        snapshot={'native_seen':['mara_talk:e:0','mara_talk:r:0'], 'native_dialogue':'Mara: Welcome back.\nPlayer: I remember.', 'native_shared':'Someone else disclosed a secret.'}
        npc_reply(provider,self.p,self.n['id'],'Where is the seal?',snapshot)
        after=provider.request.call_args.args[1]
        self.assertIn('missing seal from the cave',json.dumps(after['remembered_dialogue']))
        self.assertIn('I will help.',json.dumps(after['remembered_dialogue']))
        self.assertEqual(after['heard_dialogue'],snapshot['native_dialogue'])
        self.assertEqual(after['shared_conversations'],'')
        self.assertNotIn('The seal is returned',json.dumps(after))
        self.assertEqual(learned(self.n,{'native_seen':['other:e:0']},'seal'),[])

    def test_party_context_never_leaks_unvisited_native_lines(self):
        from test_companions import snapshot
        from rwstudio.companions import context
        snap=snapshot('party',self.n['id'],1);snap['native_shared']='The owner met a keeper.'
        ctx=context(self.p,snap,self.n['id'])
        self.assertNotIn('native_lines',ctx['profile'])
        self.assertNotIn('missing seal from the cave',json.dumps(ctx))
        self.assertEqual(ctx['shared_conversations'],'The owner met a keeper.')

    def test_terminal_greetings_have_ai_on_first_visit_and_every_spoken_node_is_wrapped(self):
        dlg=conversation([('First greeting.',[0]),('Later greeting.',[])],[('Player asks a question.',[1],'old_action')])
        entries=OrderedDict({('mara_talk',2029):write(b'DLG V3.2',dlg)});scripts={}
        changes=patch_dialogues(entries,self.report,Resources(self.path,{}),scripts)['mara_talk']
        result=read(entries['mara_talk',2029])[1]
        self.assertEqual(changes['entries'],[1]) # Mandatory first response stays intact.
        self.assertEqual(changes['added_replies'],2)
        self.assertEqual(changes['memory_nodes'],3)
        self.assertEqual(result[1]['StartingList'],dlg[1]['StartingList'])
        actions='\n'.join(scripts.values())
        self.assertEqual(actions.count('ExecuteScript("old_action",OBJECT_SELF);'),1)
        self.assertIn('"mara_talk:r:0","Player"',actions)
        self.assertNotIn('SetLocalString(pc,"RWC_HEARD_',actions) # No last-line overwrite.

    def test_profile_job_saves_success_and_retains_draft_on_provider_failure(self):
        from rwstudio.module_analyser import ModuleAnalyser,ACTIVE
        from rwstudio.storage import write_json
        manager=ModuleAnalyser(Path(self.temp.name)/'analysis');ident=manager.begin('original.mod')
        self.report['module']['filename']='original.mod'
        write_json(manager.folder(ident)/'report.json',self.report);manager.update(ident,status='complete')
        def wait():
            until=time.monotonic()+3
            while manager.status(ident)['status'] in ACTIVE and time.monotonic()<until:time.sleep(.01)
            self.assertEqual(manager.status(ident)['status'],'complete')
        with patch('rwstudio.conversion_profiles.generate',side_effect=ValueError('Provider unavailable')):
            manager.generate_profiles(ident,self.p,Mock(),{});wait()
        self.assertEqual(manager.status(ident)['profile_error'],'Provider unavailable')
        self.assertEqual(manager.conversion_plan(ident)['project'],self.p)
        expected=copy.deepcopy(self.p);expected['npcs'][0]['background']='Keeps a notebook.'
        with patch('rwstudio.conversion_profiles.generate',return_value=expected):
            manager.generate_profiles(ident,self.p,Mock(),{});wait()
        self.assertEqual(manager.status(ident)['profile_error'],'')
        self.assertEqual(manager.conversion_plan(ident)['project'],expected)


if __name__=='__main__':unittest.main()
