import copy
import json
import tempfile
import time
import threading
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
        (manager.folder(ident)/'input.mod').write_bytes(self.path.read_bytes())
        write_json(manager.folder(ident)/'report.json',self.report);manager.update(ident,status='complete')
        def wait(expected='complete'):
            until=time.monotonic()+3
            while manager.status(ident)['status'] in ACTIVE and time.monotonic()<until:time.sleep(.01)
            self.assertEqual(manager.status(ident)['status'],expected)
        with patch('rwstudio.conversion_profiles.generate',side_effect=ValueError('Provider unavailable')):
            manager.generate_profiles(ident,self.p,Mock(),{});wait('profile_failed')
        self.assertEqual(manager.status(ident)['profile_error'],'Provider unavailable')
        saved=manager.conversion_plan(ident)['project'];self.assertIn('mission_editor',saved);saved.pop('mission_editor')
        self.assertEqual(saved,self.p)
        expected=copy.deepcopy(self.p);expected['npcs'][0]['background']='Keeps a notebook.'
        with patch('rwstudio.conversion_profiles.generate',return_value=expected):
            manager.generate_profiles(ident,self.p,Mock(),{});wait()
        self.assertEqual(manager.status(ident)['profile_error'],'')
        saved=manager.conversion_plan(ident)['project'];saved.pop('mission_editor')
        self.assertEqual(saved,expected)

    def larger_report(self,count=13):
        report=copy.deepcopy(self.report)
        source=report['characters'][0]
        report['characters']=[]
        for i in range(count):
            row=copy.deepcopy(source);row.update(tag='keeper_'+str(i),resref='keeper_'+str(i),name='Keeper '+str(i))
            report['characters'].append(row)
        return report,plan(report)

    def manager(self,report):
        from rwstudio.module_analyser import ModuleAnalyser
        from rwstudio.storage import write_json
        report['module']['filename']='original.mod'
        manager=ModuleAnalyser(Path(self.temp.name)/'batch-analysis');ident=manager.begin('original.mod')
        (manager.folder(ident)/'input.mod').write_bytes(self.path.read_bytes())
        write_json(manager.folder(ident)/'report.json',report);manager.update(ident,status='complete')
        return manager,ident

    def wait_for_profiles(self,manager,ident):
        from rwstudio.module_analyser import ACTIVE
        end=time.monotonic()+5
        while manager.status(ident)['status'] in ACTIVE and time.monotonic()<end:time.sleep(.01)
        self.assertNotIn(manager.status(ident)['status'],ACTIVE)
        return manager.status(ident)

    @staticmethod
    def generated_response(system,context,schema,**kw):
        return {'characters':[dict(id=n['id'],role='Keeper',personality='Patient.',background='Keeps careful records.',motivation='Protect the keep.') for n in context['characters']]}

    def test_failure_checkpoints_and_service_restart_resumes_only_unfinished_profiles(self):
        from rwstudio.module_analyser import ModuleAnalyser
        report,p=self.larger_report();manager,ident=self.manager(report)
        provider=Mock(model='test',provider='openai');calls=[]
        def request(*args,**kwargs):
            calls.append(args[1]['characters'])
            if len(calls)==2:raise ValueError('Provider temporarily limited the rate')
            return self.generated_response(*args,**kwargs)
        provider.request.side_effect=request
        manager.generate_profiles(ident,p,provider,{})
        status=self.wait_for_profiles(manager,ident)
        self.assertEqual(status['status'],'profile_failed');self.assertEqual(status['profile_progress']['completed'],6)
        self.assertEqual(status['profile_progress']['total'],13)
        saved=manager.conversion_plan(ident)
        self.assertEqual(saved['profile_generation']['remaining_requests'],2)
        self.assertTrue(saved['profile_generation']['resumable'])
        self.assertEqual(saved['project']['npcs'][0]['background'],'Keeps careful records.')
        self.assertNotEqual(saved['project']['npcs'][6]['background'],'Keeps careful records.')
        # A creator can edit a completed profile; resume preserves that edit.
        saved['project']['npcs'][0]['background']='Creator-edited background.'
        manager=ModuleAnalyser(manager.root)
        provider.request.reset_mock();provider.request.side_effect=self.generated_response
        manager.generate_profiles(ident,saved['project'],provider,{})
        status=self.wait_for_profiles(manager,ident)
        self.assertEqual(status['status'],'complete');self.assertEqual(status['profile_progress']['completed'],13)
        self.assertEqual(provider.request.call_count,2)
        called=[n['id'] for c in provider.request.call_args_list for n in c.args[1]['characters']]
        self.assertEqual(called,[n['id'] for n in p['npcs'][6:]])
        self.assertEqual(manager.conversion_plan(ident)['project']['npcs'][0]['background'],'Creator-edited background.')

    def test_pause_finishes_inflight_batch_and_resume_skips_it(self):
        report,p=self.larger_report();manager,ident=self.manager(report)
        entered=threading.Event();release=threading.Event()
        self.addCleanup(release.set)
        provider=Mock(model='test',provider='openai')
        def request(*args,**kw):
            entered.set();release.wait(3);return self.generated_response(*args,**kw)
        provider.request.side_effect=request
        manager.generate_profiles(ident,p,provider,{})
        self.assertTrue(entered.wait(3));status=manager.pause_profiles(ident)
        self.assertTrue(status['pause_requested']);release.set()
        status=self.wait_for_profiles(manager,ident)
        self.assertEqual(status['status'],'profile_paused');self.assertEqual(status['profile_progress']['completed'],6)
        self.assertEqual(provider.request.call_count,1)
        with self.assertRaisesRegex(ValueError,'not running'):manager.pause_profiles(ident)
        saved=manager.conversion_plan(ident)['project'];provider.request.reset_mock()
        manager.generate_profiles(ident,saved,provider,{})
        self.assertEqual(self.wait_for_profiles(manager,ident)['status'],'complete')
        self.assertEqual(provider.request.call_count,2)

    def test_restart_interruption_restores_paused_state_and_regenerate_all_is_explicit(self):
        from rwstudio.module_analyser import ModuleAnalyser
        report,p=self.larger_report(7);manager,ident=self.manager(report)
        provider=Mock(model='test',provider='openai');provider.request.side_effect=self.generated_response
        manager.generate_profiles(ident,p,provider,{});self.wait_for_profiles(manager,ident)
        saved=manager.conversion_plan(ident)['project'];provider.request.reset_mock()
        manager.generate_profiles(ident,saved,provider,{});self.wait_for_profiles(manager,ident)
        provider.request.assert_not_called()
        manager.generate_profiles(ident,saved,provider,{},restart=True);self.wait_for_profiles(manager,ident)
        self.assertEqual(provider.request.call_count,2)
        manager.update(ident,status='profiling',profile_completed_ids=[n['id'] for n in p['npcs'][:6]],
                       profile_progress={'completed':6,'total':7,'started_at':time.time()})
        restored=ModuleAnalyser(manager.root)
        self.assertEqual(restored.status(ident)['status'],'profile_paused')
        self.assertEqual(restored.conversion_plan(ident)['profile_generation']['remaining_requests'],1)

    def test_invalid_batch_never_partially_saves_and_large_modules_report_all_batches(self):
        report,p=self.larger_report(371);provider=Mock();provider.request.side_effect=self.generated_response
        checkpoints=[];progress=[]
        result=generate(provider,p,report,progress.append,checkpoint=lambda p,ids:checkpoints.append(len(ids)))
        self.assertEqual(provider.request.call_count,62);self.assertEqual(checkpoints[-1],371)
        self.assertEqual(progress[-1]['batch'],62);self.assertEqual(progress[-1]['batches'],62)
        report,p=self.larger_report(7)
        def invalid(*args,**kw):
            data=self.generated_response(*args,**kw);data['characters'][-1]['background']='';return data
        provider.request.side_effect=invalid;checkpoint=Mock()
        with self.assertRaisesRegex(ValueError,'invalid background'):
            generate(provider,p,report,checkpoint=checkpoint)
        checkpoint.assert_not_called()

    def test_legacy_limit_failure_is_not_labelled_complete_or_told_to_wait(self):
        from rwstudio.module_analyser import ModuleAnalyser
        manager,ident=self.manager(self.report)
        manager.update(ident,status='complete',message='Saved profiles retained; generation did not finish',
                       profile_error='Studio has reached its 60-request hourly limit. Try again later.')
        restored=ModuleAnalyser(manager.root);status=restored.status(ident)
        self.assertEqual(status['status'],'profile_failed')
        self.assertIn('cap has been removed',status['profile_error'])
        self.assertNotIn('Try again later',status['profile_error'])


if __name__=='__main__':unittest.main()
