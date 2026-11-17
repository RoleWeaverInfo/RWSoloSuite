import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rwstudio import launcher
from rwstudio.authoring import seed,validate
from rwstudio.storage import Store,write_json
from rwstudio.nwn.area_tools import pack_module
from rwstudio.builder import ROOT
from rwstudio.player_package import refresh_share_zip,package_build_files
import zipfile

BUILD='a'*20
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.game=self.root/'Game with spaces';self.user=self.root/'User with spaces';self.runtime=self.root/'Runtime';self.runtime.mkdir();(self.game/'bin/win32').mkdir(parents=True);(self.game/'bin/win32/nwmain.exe').write_bytes(b'not executed');(self.user/'modules').mkdir(parents=True)
        self.project=seed();self.project['ai_conversations']=True;self.module=self.user/'modules/rw_silent_bell.mod'
        raw=('string SPProject(){return "silent_bell";} string SPBuild(){return "'+BUILD+'";}').encode()
        self.module.write_bytes(pack_module((ROOT/'assets/base.mod').read_bytes(),{('sp_config',2009):raw}))
        self.sidecar=self.module.with_suffix('.rwproject.json');write_json(self.sidecar,dict(build_id=BUILD,project=self.project))
    def tearDown(self):self.temp.cleanup()
    def plan(self,**kwargs):return launcher.plan(module='rw_silent_bell',game_root=self.game,user_dir=self.user,root=self.runtime,**kwargs)
    def state(self):return dict(key_available=True,settings=dict(user_dir=str(self.user)),csrf='local-test-token',bridge=dict(enabled=True),version='0.10.2')
    def test_native_launch_keeps_character_selection_and_explicit_user_folder(self):
        p=self.plan();self.assertEqual(p['game_arguments'],['-userdirectory',str(self.user.resolve()),'+LoadNewModule','rw_silent_bell']);self.assertTrue(p['ai']);self.assertEqual(p['document']['build_id'],BUILD)
        self.assertNotIn('+TestNewModule',p['game_arguments'])
    def test_single_launcher_choice_supports_new_and_saved_games(self):
        self.assertFalse(launcher.saved_game_choice(''));self.assertFalse(launcher.saved_game_choice('1'));self.assertTrue(launcher.saved_game_choice('2'))
        with self.assertRaises(launcher.LaunchError):launcher.saved_game_choice('unrecognized')
    def test_resume_opens_game_menu_without_forcing_new_module(self):
        self.assertEqual(self.plan(resume=True)['game_arguments'],['-userdirectory',str(self.user.resolve())])
    def test_rejects_mismatched_or_missing_sidecar_before_startup(self):
        write_json(self.sidecar,dict(build_id='b'*20,project=self.project))
        with self.assertRaisesRegex(launcher.LaunchError,'does not match'):self.plan()
        self.sidecar.unlink()
        with self.assertRaisesRegex(launcher.LaunchError,'missing'):self.plan()
    def test_module_ids_are_safe_and_known_build_context_can_be_reused(self):
        with self.assertRaises(launcher.LaunchError):launcher.plan(module='../unsafe',game_root=self.game,user_dir=self.user,root=self.runtime)
        self.sidecar.unlink();write_json(self.runtime/'data/builds'/BUILD/'project.json',self.project)
        self.assertEqual(self.plan()['document']['build_id'],BUILD)
    def test_full_tool_package_can_install_its_bundled_module(self):
        module_bytes=self.module.read_bytes();self.module.unlink();self.sidecar.unlink();folder=self.runtime/'data/builds'/BUILD;folder.mkdir(parents=True)
        (folder/'rw_silent_bell.mod').write_bytes(module_bytes);write_json(folder/'rw_silent_bell.rwproject.json',dict(build_id=BUILD,project=self.project))
        p=self.plan();self.assertEqual(Path(p['source']),folder/'rw_silent_bell.mod');launcher.install(p);self.assertEqual(self.module.read_bytes(),module_bytes)
    def test_missing_game_or_module_errors_are_actionable(self):
        self.module.unlink()
        with self.assertRaisesRegex(launcher.LaunchError,'module is missing'):self.plan()
        (self.game/'bin/win32/nwmain.exe').unlink()
        with self.assertRaisesRegex(launcher.LaunchError,'not found'):self.plan()
    def test_offline_does_not_need_a_key_or_matching_sidecar(self):
        self.sidecar.unlink();p=self.plan(offline=True);self.assertFalse(p['ai']);self.assertIsNone(p['document'])
    def test_install_backs_up_different_version_without_changing_saves(self):
        source=self.root/'rw_silent_bell.mod';source.write_bytes(self.module.read_bytes());self.module.write_bytes(b'previous module');p=self.plan(module_file=source,sidecar=self.sidecar)
        launcher.install(p);self.assertEqual(self.module.read_bytes(),source.read_bytes());self.assertEqual(len(list((self.user/'modules/RoleWeaverBackups').glob('*.mod'))),1)
    def test_running_bridge_registers_context_before_starting_game_and_is_not_stopped(self):
        p=self.plan();game=FakeProcess([0]);spawn=[];events=[]
        def popen(args,**kw):spawn.append(args);events.append('game');return game
        with patch.object(launcher,'http',side_effect=lambda path,*args:events.append(path)):
            launcher.run(p,popen=popen,check_state=self.state,check_game=lambda:False,sleep=lambda t:None)
        self.assertEqual(events,['/api/player/register','/api/bridge','game']);self.assertEqual(spawn[0],[p['executable'],*p['game_arguments']]);self.assertFalse(game.terminated)
    def test_new_and_saved_games_launch_from_the_binary_directory(self):
        for resume in (False,True):
            p=self.plan(resume=resume);calls=[]
            def popen(args,**kwargs):calls.append((args,kwargs));return FakeProcess([0])
            with patch.object(launcher,'http',return_value={}):
                launcher.run(p,popen=popen,check_state=self.state,check_game=lambda:False,sleep=lambda t:None)
            cwd=Path(calls[0][1]['cwd'])
            self.assertEqual(cwd,Path(p['executable']).parent)
            self.assertNotEqual(cwd,Path(p['game_root']))
            self.assertEqual((cwd/'../../data').resolve(),self.game/'data')
    def test_access_violation_reports_hex_code_and_local_log_location(self):
        for code in (3221225477,-1073741819):
            with patch.object(launcher,'http',return_value={}):
                with self.assertRaisesRegex(launcher.LaunchError,'0xC0000005.*access violation.*nwengineLog.txt'):
                    launcher.run(self.plan(),popen=lambda *a,**k:FakeProcess([code]),check_state=self.state,check_game=lambda:False,sleep=lambda t:None)
    def test_bridge_startup_timeout_does_not_launch_game_and_cleans_up_owned_worker(self):
        p=self.plan();worker=FakeProcess([None]);spawn=[]
        def popen(args,**kw):spawn.append(args);return worker
        with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_SECRET_NOT_IN_ARGUMENTS'}):
            with self.assertRaisesRegex(launcher.LaunchError,'ready'):
                launcher.run(p,popen=popen,check_state=lambda:None,check_game=lambda:False,sleep=lambda t:None)
        self.assertEqual(len(spawn),1);self.assertNotIn('TEST_SECRET_NOT_IN_ARGUMENTS',json.dumps(spawn));self.assertTrue(worker.terminated)
    def test_owned_bridge_survives_until_game_exit_then_is_stopped(self):
        p=self.plan();worker=FakeProcess([None]);game=FakeProcess([None,0]);spawn=[];states=iter([None,self.state()])
        def popen(args,**kw):spawn.append(args);return worker if len(spawn)==1 else game
        with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_SECRET_NOT_IN_ARGUMENTS'}),patch.object(launcher,'http',return_value={}):launcher.run(p,popen=popen,check_state=lambda:next(states),check_game=lambda:False,sleep=lambda t:None)
        self.assertEqual(len(spawn),2);self.assertTrue(worker.terminated);self.assertFalse(game.terminated)
    def test_already_running_game_is_not_duplicated(self):
        p=self.plan();checks=iter([True,False])
        with patch.object(launcher,'http',return_value={}),patch.object(launcher,'install') as install:
            launcher.run(p,popen=lambda *a,**k:self.fail('duplicate game'),check_state=self.state,check_game=lambda:next(checks),sleep=lambda t:None)
            install.assert_called_once()
    def test_registration_failure_prevents_game_start(self):
        with patch.object(launcher,'http',side_effect=launcher.LaunchError('context mismatch')):
            with self.assertRaisesRegex(launcher.LaunchError,'mismatch'):launcher.run(self.plan(),popen=lambda *a,**k:self.fail('game must not launch'),check_state=self.state,check_game=lambda:False)
    def test_old_bridge_version_is_rejected_before_launch(self):
        old=dict(self.state(),version='0.6.0')
        with self.assertRaisesRegex(launcher.LaunchError,'0.10'):
            launcher.run(self.plan(),popen=lambda *a,**k:self.fail('game must not launch'),check_state=lambda:old,check_game=lambda:False)
    def test_reused_bridge_is_restarted_if_it_stops_during_play(self):
        worker=FakeProcess([None]);game=FakeProcess([None,0]);spawn=[];states=iter([self.state(),None,self.state()])
        def popen(args,**kw):spawn.append(args);return game if len(spawn)==1 else worker
        with patch.dict(os.environ,{'OPENAI_API_KEY':'TEST_SECRET_NOT_IN_ARGUMENTS'}),patch.object(launcher,'http',return_value={}):
            launcher.run(self.plan(),popen=popen,check_state=lambda:next(states),check_game=lambda:False,sleep=lambda t:None)
        self.assertEqual(len(spawn),2);self.assertTrue(worker.terminated)
    def test_explicit_offline_mode_pauses_existing_ai_bridge(self):
        with patch.object(launcher,'http',return_value={}) as http:
            launcher.run(self.plan(offline=True),popen=lambda *a,**kw:FakeProcess([0]),check_state=self.state,check_game=lambda:False,sleep=lambda t:None)
        self.assertEqual(http.call_args.args[0],'/api/bridge');self.assertEqual(http.call_args.args[1],{'enabled':False})
    def test_missing_service_key_and_wrong_user_folder_prevent_launch(self):
        for s in [dict(self.state(),key_available=False),dict(self.state(),settings=dict(user_dir=str(self.root/'Other user')))]:
            with self.assertRaises(launcher.LaunchError):launcher.run(self.plan(),popen=lambda *a,**k:self.fail('game must not launch'),check_state=lambda:s,check_game=lambda:False)

class FakeProcess:
    def __init__(self,values):self.values=list(values);self.returncode=None;self.terminated=False
    def poll(self):
        value=self.values.pop(0) if len(self.values)>1 else self.values[0]
        self.returncode=value;return value
    def terminate(self):self.terminated=True;self.values=[0];self.returncode=0
    def wait(self,timeout=None):return self.returncode
    def kill(self):self.terminate()

class PlayerContextTests(unittest.TestCase):
    def test_registration_does_not_overwrite_author_draft_and_accepts_legacy_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(Path(temp));built=seed();draft=copy.deepcopy(built);draft['story']='New unsaved authoring direction';store.save(draft)
            old=copy.deepcopy(built);old.pop('ambient');old.pop('companions')
            for n in old['npcs']:n.pop('behavior');n.pop('companion')
            write_json(store.root/'builds'/BUILD/'project.json',old)
            store.register_player_build(BUILD,validate(old));self.assertEqual(store.get(built['id'])['story'],draft['story'])
            other=copy.deepcopy(built);other['title']='Conflicting build'
            with self.assertRaises(ValueError):store.register_player_build(BUILD,other)
            with self.assertRaises(ValueError):store.register_player_build('../unsafe',built)
    def test_share_bundle_excludes_player_data_logs_settings_and_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'source').mkdir();manifest=dict(module='sample.mod')
            for name in ('sample.mod','PLAY.txt','ROLE-WEAVER-LICENSE.txt','manifest.json','validation.json','layout.json','sample.rwproject.json'):(folder/name).write_text('{}')
            (folder/'source/test.nss').write_text('void main(){}')
            (folder/'AI Player/data').mkdir(parents=True);(folder/'AI Player/data/settings.json').write_text('PRIVATE_SETTINGS_SENTINEL');(folder/'AI Player/data/.env').write_text('PRIVATE_CREDENTIAL_SENTINEL')
            archive=refresh_share_zip(folder,manifest)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip());self.assertIn('Start Role Weaver.cmd',z.namelist());self.assertIn('AI Player/service.py',z.namelist());self.assertIn('AI Player/rwstudio/service.py',z.namelist());self.assertFalse(any('/data/' in n for n in z.namelist()))
                self.assertIn(b'-AdventurePath "%~dp0sample.mod"',z.read('Start Role Weaver.cmd'))
                self.assertIn('AI Player/web/branding/splash.png',z.namelist());self.assertNotIn('Play Adventure.cmd',z.namelist());self.assertNotIn('Start-Adventure.ps1',z.namelist());self.assertNotIn('AI Player/play.py',z.namelist())
            self.assertFalse(any('AI Player/data' in str(f) for f in package_build_files(folder,manifest)))

if __name__=='__main__':unittest.main()
