import json
from pathlib import Path
import tempfile
import unittest
from google_app_setup import credentials_path, require_client


class AppSetupTests(unittest.TestCase):
    def test_new_install_uses_bundled_client(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(credentials_path(tmp, Path(tmp)/'data'), Path(tmp)/'google_oauth_client.json')

    def test_existing_client_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = Path(tmp)/'google_credentials.json'
            previous.write_text('{}')
            self.assertEqual(credentials_path('app', tmp), previous)

    def test_missing_configuration_is_actionable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'Herausgeber'):
                require_client(Path(tmp)/'missing.json')

    def test_desktop_only_and_google_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'client.json'
            client = dict(client_id='test', client_secret='test', auth_uri='https://accounts.google.com/o/oauth2/auth', token_uri='https://oauth2.googleapis.com/token')
            path.write_text(json.dumps({'installed': client}))
            self.assertEqual(require_client(path), path)
            path.write_text(json.dumps({'web': client}))
            with self.assertRaises(ValueError):
                require_client(path)
            client['token_uri'] = 'https://example.com/token'
            path.write_text(json.dumps({'installed': client}))
            with self.assertRaises(ValueError):
                require_client(path)
