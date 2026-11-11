import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'scripts' / 'prepare_task_metadata_fix.py'
spec = importlib.util.spec_from_file_location('metadata_build_integration', path)
integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)

SOURCE = ("import private_storage as storage\n"
          "def unchanged(r, binding):\n"
          "    return r['semantic'] == binding['remote'] and r.get('content') == binding.get('remote_content', r.get('content'))\n").encode()

class BuildIntegrationTests(unittest.TestCase):
    def prepare(self, tracked, working):
        with patch.object(integration, 'EXPECTED_BLOB', integration.git_blob(tracked)):
            return integration.validated_source(tracked, working)

    def test_identical_lf(self):
        result = self.prepare(SOURCE, SOURCE)
        self.assertIn('return _remote_unchanged_for_delete(r, binding)', result)
        self.assertIn('from task_delete_metadata import', result)

    def test_windows_checkout_crlf(self):
        self.assertEqual(self.prepare(SOURCE, SOURCE.replace(b'\n', b'\r\n')),
                         self.prepare(SOURCE, SOURCE))

    def test_committed_crlf(self):
        tracked = SOURCE.replace(b'\n', b'\r\n')
        self.assertEqual(self.prepare(tracked, SOURCE), self.prepare(SOURCE, SOURCE))

    def test_actual_working_edit_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'beyond line endings'):
            self.prepare(SOURCE, SOURCE + b'# real edit\n')

    def test_wrong_committed_revision_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'committed'):
            integration.validated_source(SOURCE, SOURCE)

    def test_missing_guard_rejected(self):
        tracked = b'import private_storage as storage\n'
        with self.assertRaisesRegex(RuntimeError, 'guard'):
            self.prepare(tracked, tracked)

    def test_ambiguous_guard_rejected(self):
        tracked = SOURCE + SOURCE
        with self.assertRaisesRegex(RuntimeError, 'guard'):
            self.prepare(tracked, tracked)

    def test_non_newline_byte_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'beyond line endings'):
            self.prepare(SOURCE, b'\xef\xbb\xbf' + SOURCE)

if __name__ == '__main__':
    unittest.main()
