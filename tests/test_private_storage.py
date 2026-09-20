import json
import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import private_storage as s


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI integration tests')
class StorageTests(unittest.TestCase):
    def test_real_dpapi_roundtrip_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'secret'
            payload = b'private-token-and-calendar-data' * 50
            s.write_bytes(p, payload)
            raw = p.read_bytes()
            self.assertNotIn(payload[:25], raw)
            self.assertEqual(s.decode(raw), payload)
            raw = raw[:-10] + bytes([raw[-10] ^ 1]) + raw[-9:]
            with self.assertRaises(OSError):
                s.decode(raw)

    def test_legacy_migration_and_failed_replace_preserves_original(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'token.json'
            original = json.dumps({'refresh_token': 'test-only', 'scopes': ['test']}).encode()
            p.write_bytes(original)
            with patch.object(s.os, 'replace', side_effect=OSError('test failure')):
                with self.assertRaises(OSError):
                    s.read_json(p, migrate=True)
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual(len(list(Path(td).iterdir())), 1)
            data = s.read_json(p, migrate=True)
            self.assertTrue(p.read_bytes().startswith(s.MAGIC))
            self.assertEqual(s.read_json(p), data)
            self.assertEqual(data['refresh_token'], 'test-only')

    def test_encrypt_failure_has_no_plaintext_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'new'
            with patch.object(s, '_crypt', side_effect=OSError('unavailable')):
                with self.assertRaises(OSError):
                    s.write_json(p, {'secret': 'test'})
            self.assertFalse(p.exists())

    def test_log_roundtrip_and_truncated_record(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'log'
            log = s.Log(p)
            log.append('one ä')
            log.append('two')
            self.assertEqual(s.decode(p.read_bytes()).decode(), 'one ä\ntwo\n')
            with self.assertRaises(ValueError):
                s.decode(p.read_bytes()[:-1])
            with self.assertRaises(FileExistsError):
                s.Log(p)

    def test_calendar_token_load_and_refresh_stays_encrypted(self):
        # Run the real auth function without network/dependency imports.
        tree = ast.parse(Path('google_calendar_bridge.py').read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'get_credentials')
        class Credentials:
            expired = True
            refresh_token = 'test-only'
            valid = True
            @classmethod
            def from_authorized_user_info(cls, info):
                assert info['refresh_token'] == 'test-only'
                return cls()
            def has_scopes(self, scopes):
                return True
            def refresh(self, request):
                self.expired = False
            def to_json(self):
                return json.dumps({'refresh_token': self.refresh_token, 'refreshed': not self.expired})
        ns = dict(Path=Path, private_storage=s, json=json, Credentials=Credentials,
                  Request=lambda: object(), SCOPES=['test'])
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'auth', 'exec'), ns)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'google_token.json'
            path.write_text(json.dumps({'refresh_token': 'test-only'}))
            (Path(td)/'google_oauth_scope_version.txt').write_text('2')
            creds = ns['get_credentials'](Path(td)/'missing-client', path, interactive=False)
            self.assertTrue(creds.valid)
            self.assertTrue(path.read_bytes().startswith(s.MAGIC))
            self.assertTrue(s.read_json(path)['refreshed'])

    def test_full_backup_preserves_exact_device_bytes(self):
        import manager_protocol as manager
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'database.org.dpapi'
            with patch.object(manager, '_cmd_rsp', return_value=True), \
                 patch.object(manager, '_receive_fixed_block', side_effect=lambda ser, size, *args: b'A'*size), \
                 patch.object(manager, '_read_backup_info', return_value=b'1234'):
                result = manager.backup_database(None, path, lambda *a: None, protected=True)
            payload = s.decode(path.read_bytes())
            self.assertEqual(len(payload), manager.BACKUP_TOTAL_SIZE)
            self.assertEqual(payload[-8:], b'12341234')
            self.assertEqual(result['size'], len(payload))
