import ast
import copy
from pathlib import Path
import os
import unittest
from task_delete_metadata import remote_unchanged_for_delete

RAW = ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VTODO\r\nUID:test-task\r\n'
       'DTSTAMP:20261111T220000Z\r\nLAST-MODIFIED:20261111T210000Z\r\n'
       'SUMMARY:Test\r\nSTATUS:COMPLETED\r\nDUE;VALUE=DATE:20261111\r\n'
       'LOCATION:Home\r\nEND:VTODO\r\nEND:VCALENDAR\r\n')

class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.remote = {'kind': 'tasks', 'uid': 'test-task',
                       'semantic': {'title': 'Test', 'done': 1}, 'content': RAW}
        self.binding = {'href': '/test', 'uid': 'test-task',
                        'remote': copy.deepcopy(self.remote['semantic']), 'remote_content': RAW}

    def check(self, expected):
        self.assertEqual(remote_unchanged_for_delete(self.remote, self.binding), expected)

    def test_identical(self):
        self.check(True)

    def test_dtstamp(self):
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z', 'DTSTAMP:20261111T230000Z')
        self.check(True)

    def test_last_modified(self):
        self.remote['content'] = RAW.replace('LAST-MODIFIED:20261111T210000Z', 'LAST-MODIFIED:20261111T230000Z')
        self.check(True)

    def test_both_timestamps(self):
        self.remote['content'] = RAW.replace('T220000Z', 'T230000Z').replace('T210000Z', 'T230001Z')
        self.check(True)

    def test_semantic_change(self):
        self.remote['semantic']['title'] = 'Changed'
        self.check(False)

    def test_uid(self):
        self.remote['uid'] = 'replacement'
        self.check(False)

    def test_other_properties(self):
        for before, after in [('SUMMARY:Test', 'SUMMARY:Changed'), ('STATUS:COMPLETED', 'STATUS:NEEDS-ACTION'),
                              ('DUE;VALUE=DATE:20261111', 'DUE;VALUE=DATE:20261112'),
                              ('LOCATION:Home', 'LOCATION:Work'), ('END:VTODO', 'X-PRIVATE:new\r\nEND:VTODO')]:
            with self.subTest(before=before):
                self.remote['content'] = RAW.replace('T220000Z', 'T230000Z').replace(before, after)
                self.check(False)

    def test_event_strict(self):
        self.remote['kind'] = 'events'
        self.remote['content'] = RAW.replace('T220000Z', 'T230000Z')
        self.check(False)

    def test_contact_strict(self):
        self.remote['kind'] = 'contacts'
        self.remote['content'] = RAW.replace('T220000Z', 'T230000Z')
        self.check(False)

    def test_invalid_timestamp(self):
        for value in ('20261399T230000Z', '20261111T250000Z', '20261111', '20261111T230000'):
            with self.subTest(value=value):
                self.remote['content'] = RAW.replace('20261111T220000Z', value)
                self.check(False)

    def test_missing_timestamp(self):
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z\r\n', '')
        self.check(False)

    def test_duplicate_timestamp(self):
        for name in ('DTSTAMP', 'LAST-MODIFIED'):
            with self.subTest(name=name):
                self.remote['content'] = RAW.replace('END:VTODO', name + ':20261111T230000Z\r\nEND:VTODO')
                self.check(False)

    def test_removed_last_modified(self):
        self.remote['content'] = RAW.replace('LAST-MODIFIED:20261111T210000Z\r\n', '')
        self.check(False)

    def test_added_last_modified(self):
        self.binding['remote_content'] = RAW.replace('LAST-MODIFIED:20261111T210000Z\r\n', '')
        self.check(False)

    def test_nested_alarm_timestamp(self):
        alarm = 'BEGIN:VALARM\r\nDTSTAMP:20261111T220000Z\r\nEND:VALARM\r\n'
        self.binding['remote_content'] = RAW.replace('END:VTODO', alarm + 'END:VTODO')
        self.remote['content'] = self.binding['remote_content'].replace('T220000Z', 'T230000Z')
        self.check(False)

    def test_folded_timestamp(self):
        self.remote['content'] = RAW.replace('T220000Z\r\n', 'T230000Z\r\n extra\r\n')
        self.check(False)

    def test_line_endings_strict(self):
        self.remote['content'] = RAW.replace('\r\n', '\n')
        self.check(False)

    def test_multiple_tasks(self):
        self.remote['content'] = RAW.replace('T220000Z', 'T230000Z').replace('END:VCALENDAR', 'BEGIN:VTODO\r\nEND:VTODO\r\nEND:VCALENDAR')
        self.check(False)

    def test_missing_baseline_not_normalized(self):
        self.binding['remote_content'] = None
        self.check(False)

    def test_planner_integration(self):
        source_path = Path(__file__).resolve().parents[1] / 'dav_sync.py'
        if not source_path.exists():
            self.skipTest('Repository planner not present in isolated helper test')
        source = source_path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'build_plan')
        enabled = '_remote_unchanged_for_delete(r, binding)' in source
        if os.environ.get('IC35_EXPECT_TASK_METADATA_FIX') == '1':
            self.assertTrue(enabled, 'Fix must be integrated before packaging')
        namespace = {'_remote_unchanged_for_delete': remote_unchanged_for_delete}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'planner', 'exec'), namespace)
        self.remote['content'] = RAW.replace('T220000Z', 'T230000Z').replace('T210000Z', 'T230001Z')
        ops, conflicts, _ = namespace['build_plan']({'tasks:15': self.binding}, {}, {'/test': self.remote})
        self.assertEqual(bool(conflicts), not enabled)
        self.assertEqual([op['action'] for op in ops], ['delete_remote'] if enabled else [])
        self.remote['content'] += 'X-UNKNOWN:changed\r\n'
        ops, conflicts, _ = namespace['build_plan']({'tasks:15': self.binding}, {}, {'/test': self.remote})
        self.assertTrue(conflicts)
        self.assertFalse(ops)

if __name__ == '__main__':
    unittest.main()
