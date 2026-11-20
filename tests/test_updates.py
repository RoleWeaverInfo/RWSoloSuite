import hashlib
import io
import os
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import zipfile

from rwstudio import updates
from rwstudio.server import Application


def release(version='0.22.0', suffix='Setup-x64.exe', raw=b'installer'):
    return dict(tag_name='v'+version, prerelease='-' in version, draft=False, assets=[dict(name='Role-Weaver-Module-Studio-'+version+'-'+suffix,id=123,size=len(raw),digest='sha256:'+hashlib.sha256(raw).hexdigest())])


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root = Path(self.temp.name)

    def test_platform_architecture_mapping(self):
        for system, machine, suffix in [('win32','AMD64','Setup-x64.exe'),('darwin','x86_64','macOS-x64.zip'),('darwin','arm64','macOS-arm64.zip'),('linux','x86_64','Linux-x64.tar.gz'),('linux','aarch64','Linux-arm64.tar.gz')]:
            self.assertEqual(updates.package_suffix(system,machine),suffix)
        with self.assertRaises(ValueError):updates.package_suffix('win32','arm64')

    def test_version_order_and_stable_prerelease_channels(self):
        releases = [release('0.9.0'),release('0.10.0'),release('1.0.0-rc2')]
        self.assertEqual(updates.select_release(releases,'0.8.0','Setup-x64.exe')['version'],'0.10.0')
        self.assertEqual(updates.select_release(releases,'0.10.0-rc1','Setup-x64.exe')['version'],'1.0.0-rc2')
        self.assertIsNone(updates.select_release([release('0.10.0-rc1')],'0.10.0-rc1','Setup-x64.exe'))
        self.assertGreater(updates.version_key('0.10.0'),updates.version_key('0.10.0-rc12'))

    def test_invalid_release_metadata_and_missing_assets_are_rejected(self):
        for field, value in [('digest',''),('id','123'),('size',0),('size',updates.MAX_PACKAGE+1)]:
            r = release();r['assets'][0][field] = value
            with self.assertRaises(ValueError):updates.select_release([r],'0.21.0','Setup-x64.exe')
        with self.assertRaisesRegex(ValueError,'no package'):updates.select_release([release()],'0.21.0','Linux-arm64.tar.gz')
        r = release();r['tag_name']='../../unsafe'
        self.assertIsNone(updates.select_release([r],'0.21.0','Setup-x64.exe'))

    def test_size_and_checksum_are_verified(self):
        candidate = updates.select_release([release()],'0.21.0','Setup-x64.exe');file = self.root/'package.exe';file.write_bytes(b'installer')
        updates.verify_download(candidate,file)
        file.write_bytes(b'tampered!')
        with self.assertRaisesRegex(ValueError,'checksum'):updates.verify_download(candidate,file)
        file.write_bytes(b'short')
        with self.assertRaisesRegex(ValueError,'Incomplete'):updates.verify_download(candidate,file)

    def test_private_release_uses_cli_without_exposing_its_token(self):
        denied = urllib.error.HTTPError(updates.API,404,'private',{},None)
        with patch.object(updates.urllib.request,'urlopen',side_effect=denied),patch.object(updates.shutil,'which',return_value='gh'),patch.object(updates.subprocess,'run',return_value=Mock(returncode=0,stdout=b'[]')) as run:
            self.assertEqual(updates.release_list(),([],True));self.assertIn('api',run.call_args.args[0]);self.assertNotIn('token',' '.join(run.call_args.args[0]))
        with patch.object(updates.urllib.request,'urlopen',side_effect=denied),patch.object(updates.shutil,'which',return_value=None):
            with self.assertRaisesRegex(ValueError,'repository requires GitHub access'):updates.release_list()

    def test_source_checkout_cannot_download_or_install_over_local_changes(self):
        with patch.object(updates,'install_location',return_value=None):
            updater = updates.Updater(self.root)
            updater.candidate = updates.select_release([release()],'0.21.0','Setup-x64.exe')
            with self.assertRaisesRegex(ValueError,'Source checkouts'):updater.start('download')
            updater.result['state']='ready'
            with patch('rwstudio.launcher.game_running',return_value=False),self.assertRaisesRegex(ValueError,'installed version'):updater.apply()

    def test_background_check_and_failure_states_are_reviewable(self):
        updater = updates.Updater(self.root)
        with patch.object(updates,'release_list',return_value=([release()],False)),patch.object(updates,'package_suffix',return_value='Setup-x64.exe'):
            updater._run('check');self.assertEqual(updater.status()['state'],'available');self.assertEqual(updater.status()['release']['version'],'0.22.0')
        with patch.object(updates,'release_list',side_effect=ValueError('No access')):
            updater._run('check');self.assertEqual(updater.status()['state'],'error');self.assertEqual(updater.status()['error'],'No access')

    def test_install_requires_ready_confirmation_and_closed_game(self):
        app = Mock();app.updater = updates.Updater(self.root)
        with self.assertRaisesRegex(ValueError,'Confirm'):Application.post(app,'/api/updates/install',{})
        with self.assertRaisesRegex(ValueError,'Download'):app.updater.apply()
        app.updater.result['state']='ready'
        with patch('rwstudio.launcher.game_running',return_value=True),self.assertRaisesRegex(ValueError,'exit NWN'):app.updater.apply()

    def test_helpers_quote_paths_wait_and_keep_backup_without_deleting_workspace(self):
        install = self.root/"app with ' quotes";data = self.root/'my data';work = self.root/'update-123'
        win = updates.helper_script(install,work/'update.exe',None,data,1234,work,'win32')
        self.assertIn('Get-Process -Id 1234',win);self.assertIn("app with '' quotes",win);self.assertIn('/NORESTART',win);self.assertIn('-WindowStyle Hidden',win)
        unix = updates.helper_script(install,work/'update.tar.gz',work/'staged',data,1234,work,'linux')
        self.assertIn('kill -0 1234',unix);self.assertIn('.before-update-',unix);self.assertIn('ROLEWEAVER_DATA_DIR=',unix)
        for script in (win,unix):self.assertNotIn('Remove-Item',script);self.assertNotIn('rm -',script)

    def test_unpack_linux_preserves_executable_and_rejects_path_escape(self):
        package = self.root/'test.tar.gz'
        with tarfile.open(package,'w:gz') as archive:
            info = tarfile.TarInfo('RoleWeaverModuleStudio/RoleWeaverModuleStudio');info.size=3;info.mode=0o755
            archive.addfile(info,io.BytesIO(b'app'))
        bundle = updates.unpack(package,self.root/'ok','linux');self.assertEqual((bundle/'RoleWeaverModuleStudio').read_bytes(),b'app')
        with tarfile.open(package,'w:gz') as archive:
            info = tarfile.TarInfo('RoleWeaverModuleStudio/../../escape');info.size=3;archive.addfile(info,io.BytesIO(b'bad'))
        with self.assertRaisesRegex(ValueError,'Unsafe'):updates.unpack(package,self.root/'bad','linux')
        self.assertFalse((self.root/'escape').exists())

    def test_mac_zip_rejects_paths_outside_bundle_before_install(self):
        package = self.root/'test.zip'
        with zipfile.ZipFile(package,'w') as archive:archive.writestr('../escape','bad')
        with self.assertRaisesRegex(ValueError,'Unsafe'):updates.unpack(package,self.root/'badmac','darwin')
        self.assertFalse((self.root/'escape').exists())

    @unittest.skipUnless(os.name=='nt', 'Windows updater helper')
    def test_helper_spawn_leaves_service_running_until_server_shuts_it_down(self):
        install = self.root/'installed';install.mkdir();data=self.root/'data';data.mkdir()
        with patch.object(updates,'install_location',return_value=install),patch('rwstudio.launcher.game_running',return_value=False),patch.object(updates.subprocess,'Popen') as spawn:
            updater = updates.Updater(data);updater.result['state']='ready';updater.work=data/'updates/test';updater.work.mkdir(parents=True)
            updater.candidate = updates.select_release([release()],'0.21.0','Setup-x64.exe');updater.package=updater.work/'setup.exe';updater.package.write_bytes(b'installer')
            spawn.return_value.pid=123
            self.assertEqual(updater.apply()['state'],'installing');self.assertEqual(updater.status()['helper_pid'],123)
            self.assertTrue((updater.work/'apply.ps1').is_file())
            self.assertFalse((data/'settings.json').exists())

    def test_windows_helper_parses_with_literal_paths(self):
        if os.name != 'nt':self.skipTest('Windows PowerShell parser')
        import subprocess
        work = self.root/"path with ' and $ special";work.mkdir()
        script = work/'apply.ps1'
        script.write_text(updates.helper_script(work/'app',work/'setup.exe',None,work/'data',999999,work,'win32'),encoding='utf-8-sig')
        command = '$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$tokens,[ref]$errors) | Out-Null; if ($errors.Count) { exit 1 }'
        # Script path is an argument, never interpolated into shell code.
        harness = self.root/'parse.ps1';harness.write_text(command)
        result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(harness),str(script)],capture_output=True,creationflags=updates.NO_WINDOW)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))

    @unittest.skipIf(os.name=='nt', 'Native Unix bundle replacement')
    def test_unix_helper_replaces_only_application_and_preserves_workspace(self):
        import subprocess
        import time
        app = self.root/"installed app's folder";app.mkdir();(app/'old').write_text('old version')
        staged = self.root/'staged';staged.mkdir();data = self.root/'workspace';data.mkdir();(data/'project.json').write_text('keep me')
        work = data/'updates/op';work.mkdir(parents=True)
        exe = staged/'RoleWeaverModuleStudio';exe.write_text('#!/bin/sh\nprintf started > "$ROLEWEAVER_DATA_DIR/started"\n');exe.chmod(0o755)
        script = work/'apply.sh';script.write_text(updates.helper_script(app,work/'package',staged,data,99999999,work,'linux'))
        result = subprocess.run(['/bin/sh',str(script)],capture_output=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr.decode())
        for _ in range(20):
            if (data/'started').exists():break
            time.sleep(.05)
        self.assertTrue((data/'started').exists());self.assertTrue((app/'RoleWeaverModuleStudio').exists())
        self.assertTrue((app.with_name(app.name+'.before-update-op')/'old').exists())
        self.assertEqual((data/'project.json').read_text(),'keep me')
