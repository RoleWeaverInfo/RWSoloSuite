import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from rwstudio.paths import default_data,compiler_path,nwn_user_dir
from rwstudio.credentials import Credentials

class CrossPlatformTests(unittest.TestCase):
    def test_native_paths_keep_workspace_outside_application(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{},clear=True):
            root=Path(tmp);app=root/'application';app.mkdir();(app/'installation.json').write_text('{}')
            with patch('pathlib.Path.home',return_value=root/'home'):
                with patch('sys.platform','darwin'):
                    self.assertEqual(default_data(app),root/'home/Library/Application Support/RoleWeaver/ModuleStudio')
                    self.assertEqual(nwn_user_dir(),root/'home/Documents/Neverwinter Nights')
                with patch('sys.platform','linux'),patch.dict(os.environ,{'XDG_DATA_HOME':str(root/'xdg')}):
                    self.assertEqual(default_data(app),root/'xdg/RoleWeaver/ModuleStudio')
                    self.assertEqual(nwn_user_dir(),root/'xdg/Neverwinter Nights')
                    self.assertEqual(compiler_path(app),app/'vendor/nwnsc/nwnsc')

    def test_keyring_metadata_contains_no_secret_and_removal_clears_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            credentials=Credentials(tmp);backend=Mock();backend.get_password.return_value='fake-test-secret'
            with patch('rwstudio.credentials.sys.platform','linux'),patch('rwstudio.credentials.system_keyring',return_value=backend):
                credentials.update('gemini','fake-test-secret')
                self.assertNotIn('fake-test-secret',credentials.path.read_text())
                self.assertEqual(credentials.get('gemini'),'fake-test-secret')
                self.assertEqual(json.loads(credentials.path.read_text()),{'gemini':{'storage':'keyring'}})
                credentials.update('gemini',remove=True)
                backend.delete_password.assert_called_once_with('RoleWeaver.ModuleStudio',credentials.keyring_account('gemini'))

    def test_unavailable_keyring_does_not_write_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            credentials=Credentials(tmp)
            with patch('rwstudio.credentials.sys.platform','linux'),patch('rwstudio.credentials.system_keyring',side_effect=RuntimeError('secret must not leak')):
                with self.assertRaisesRegex(ValueError,'Secure key storage') as error:credentials.update('openai','fake-test-secret')
            self.assertNotIn('secret must not leak',str(error.exception))
            self.assertFalse(credentials.path.exists())
