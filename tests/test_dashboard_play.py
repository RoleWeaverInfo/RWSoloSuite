import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rwstudio import dashboard_launch as play
from rwstudio.authoring import seed
from rwstudio.storage import Store, write_json
from rwstudio.builder import ROOT
from rwstudio.nwn.area_tools import pack_module

BUILD = 'a'*20
FIND_EXECUTABLE = play.executable


class DashboardPlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name);self.user = self.root/'NWN user';self.user.mkdir()
        self.game = self.root/'Game';self.exe = self.game/'bin/win32/nwmain.exe'
        self.exe.parent.mkdir(parents=True);self.exe.write_bytes(b'not executable')
        self.store = Store(self.root/'workspace');self.project = seed();self.project['ai_conversations'] = True
        self.store.register_player_build(BUILD, self.project)
        self.folder = self.store.root/'builds'/BUILD
        self.raw = pack_module((ROOT/'assets/base.mod').read_bytes(), {('sp_config',2009):('string SPProject(){return "silent_bell";} string SPBuild(){return "'+BUILD+'";}').encode()})
        (self.folder/'rw_silent_bell.mod').write_bytes(self.raw)
        write_json(self.folder/'manifest.json', dict(module='rw_silent_bell.mod', sha256=hashlib.sha256(self.raw).hexdigest()))
        write_json(self.folder/'rw_silent_bell.rwproject.json', dict(build_id=BUILD, project=self.project))
        self.app = SimpleNamespace(store=self.store, config=dict(game_root=str(self.game),user_dir=str(self.user),provider='openai'), credentials=Mock(), bridge=SimpleNamespace(enabled=False))
        for target, value in [('rwstudio.dashboard_launch.launcher.game_running',False),('rwstudio.dashboard_launch.executable',self.exe),('rwstudio.dashboard_launch.time.sleep',None)]:
            self.addCleanup(patch.stopall);patch(target,return_value=value).start()
        self.spawn = patch('rwstudio.dashboard_launch.subprocess.Popen').start();self.spawn.return_value.poll.return_value = None;self.spawn.return_value.pid = 100

    def test_installs_exact_build_then_starts_character_selection(self):
        result = play.launch_build(self.app, BUILD)
        self.assertTrue(result['started']);self.assertTrue(self.app.bridge.enabled)
        self.assertEqual((self.user/'modules/rw_silent_bell.mod').read_bytes(),self.raw)
        self.assertEqual(self.spawn.call_args.args[0], [str(self.exe),'-userdirectory',str(self.user.resolve()),'+LoadNewModule','rw_silent_bell'])
        self.assertEqual(self.spawn.call_args.kwargs['cwd'],self.exe.parent)

    def test_does_not_replace_module_or_launch_when_game_is_open(self):
        with patch('rwstudio.dashboard_launch.launcher.game_running',return_value=True),self.assertRaisesRegex(ValueError,'already running'):play.launch_build(self.app,BUILD)
        self.spawn.assert_not_called();self.assertFalse((self.user/'modules').exists())

    def test_rejects_missing_credentials_and_mismatched_sidecar(self):
        self.app.credentials.get.return_value = None
        with self.assertRaisesRegex(ValueError,'API key'):play.launch_build(self.app,BUILD)
        self.app.credentials.get.return_value = 'test-only'
        write_json(self.folder/'rw_silent_bell.rwproject.json',dict(build_id='b'*20,project=self.project))
        with self.assertRaisesRegex(ValueError,'different'):play.launch_build(self.app,BUILD)
        self.spawn.assert_not_called()

    def test_rejects_tampered_build(self):
        write_json(self.folder/'manifest.json',dict(module='rw_silent_bell.mod',sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'checksum'):play.launch_build(self.app,BUILD)
        self.spawn.assert_not_called()

    def test_early_crash_is_reported_and_no_game_process_is_claimed(self):
        self.spawn.return_value.poll.return_value = 3221225477;self.spawn.return_value.returncode = 3221225477
        with self.assertRaisesRegex(ValueError,'3221225477'):play.launch_build(self.app,BUILD)

    def test_native_platform_executable_candidates(self):
        for system, name in [('win32','bin/win32/nwmain.exe'),('linux','bin/linux-x86/nwmain-linux'),('darwin','bin/macos/nwmain.app/Contents/MacOS/nwmain')]:
            exe = self.game/name;exe.parent.mkdir(parents=True,exist_ok=True);exe.touch()
            self.assertEqual(FIND_EXECUTABLE(self.game,system),exe.resolve())
