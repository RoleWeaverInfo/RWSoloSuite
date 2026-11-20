import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rwstudio.paths import default_data
from rwstudio.installation import service_lock
from rwstudio import service
from build_installer import extract
import zipfile


class InstallerTests(unittest.TestCase):
    def test_source_workspace_stays_local_and_installed_workspace_survives_versions(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True),patch('rwstudio.paths.sys.platform','win32'):
            root=Path(tmp);program=root/'program';program.mkdir();local=root/'user';local.mkdir()
            with patch.dict(os.environ,{'LOCALAPPDATA':str(local)}):
                self.assertEqual(default_data(program),program/'data')
                for version in ('0.20.0-rc2','0.21.0'):
                    (program/'installation.json').write_text(json.dumps({'version':version}))
                    self.assertEqual(default_data(program),local/'RoleWeaver/ModuleStudio')
                    self.assertFalse(default_data(program).is_relative_to(program))

    def test_explicit_workspace_override_is_used_without_install_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);override=root/'custom'
            with patch.dict(os.environ,{'ROLEWEAVER_DATA_DIR':str(override)}):
                self.assertEqual(default_data(root),override.resolve())
            self.assertFalse(override.exists())

    def test_runtime_probe_does_not_contact_running_service_or_open_browser(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(service.launcher,'state') as state,patch.object(service.webbrowser,'open') as browser,contextlib.redirect_stdout(io.StringIO()) as output:
            service.main(['--runtime-info','--data',tmp])
            self.assertEqual(json.loads(output.getvalue())['data'],tmp)
        state.assert_not_called();browser.assert_not_called()

    @unittest.skipUnless(os.name=='nt','Windows mutex required')
    def test_installation_lock_rejects_duplicate_and_releases_its_handle(self):
        with service_lock(28766):
            with self.assertRaisesRegex(ValueError,'already running'):
                with service_lock(28766):pass
            with service_lock(28767):pass
        with service_lock(28766):pass

    def test_archive_cannot_escape_installer_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);archive=folder/'bad.zip'
            with zipfile.ZipFile(archive,'w') as out:out.writestr('../escaped','bad')
            with self.assertRaisesRegex(ValueError,'escapes'):extract(archive,folder/'stage')
            self.assertFalse((folder/'escaped').exists())

    def test_export_scanner_uses_installed_user_credentials(self):
        from rwstudio import player_package
        with patch('rwstudio.paths.default_data',return_value=Path('installed-user-data')),patch('rwstudio.credentials.Credentials') as credentials:
            credentials.return_value.get.return_value='fake-installed-key'
            self.assertIn(b'fake-installed-key',player_package.export_keys())
            credentials.assert_called_once_with(Path('installed-user-data'))
