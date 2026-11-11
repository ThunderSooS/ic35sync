"""Isolated planner tests. Set IC35_TEST_DTSTAMP_CANDIDATE=1 to apply the patch in memory.
No transport imports, device access, writes or persistent source changes.
"""
import ast
import copy
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load_plan():
    source = (ROOT / 'dav_sync.py').read_text(encoding='utf-8-sig')
    if os.environ.get('IC35_TEST_DTSTAMP_CANDIDATE') == '1':
        patch = (ROOT / 'patches/task-delete-dtstamp.patch').read_text(encoding='utf-8')
        helper = '\n'.join(line[1:] for line in patch.splitlines()
                           if line.startswith('+') and not line.startswith('+++'))
        helper = helper[:helper.index('def build_plan(')]
        old = "r['semantic'] == binding['remote'] and r.get('content') == binding.get('remote_content', r.get('content'))"
        if source.count(old) != 1:
            raise ValueError('Unexpected source version; refusing candidate injection')
        source = source.replace(old, '_remote_unchanged_for_delete(r, binding)')
        source += '\n' + helper
    tree = ast.parse(source)
    wanted = {'build_plan', '_task_content_unchanged', '_remote_unchanged_for_delete'}
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), 'isolated-dav-sync', 'exec'), namespace)
    return namespace['build_plan']

RAW = ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VTODO\r\nUID:test-task\r\n'
       'DTSTAMP:20261111T220000Z\r\nSUMMARY:Test\r\nSTATUS:COMPLETED\r\n'
       'DUE;VALUE=DATE:20261111\r\nLAST-MODIFIED:20261111T210000Z\r\n'
       'LOCATION:Home\r\nEND:VTODO\r\nEND:VCALENDAR\r\n')

class TaskDeleteCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = staticmethod(load_plan())

    def setUp(self):
        self.remote = {'kind': 'tasks', 'uid': 'test-task',
                       'semantic': {'Betreff': 'Test', 'Erledigt': 1}, 'content': RAW}
        self.binding = {'href': '/test', 'uid': 'test-task',
                        'remote': copy.deepcopy(self.remote['semantic']), 'remote_content': RAW}

    def check(self, allowed=False):
        operations, conflicts, _ = self.plan({'tasks:15': self.binding}, {}, {'/test': self.remote})
        if allowed:
            self.assertFalse(conflicts)
            self.assertEqual([o['action'] for o in operations], ['delete_remote'])
        else:
            self.assertTrue(conflicts)
            self.assertFalse(operations)

    def test_unchanged(self):
        self.check(True)

    def test_dtstamp_only(self):
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z', 'DTSTAMP:20261111T230000Z')
        enabled = os.environ.get('IC35_TEST_DTSTAMP_CANDIDATE') == '1'
        applied = '_remote_unchanged_for_delete' in (ROOT / 'dav_sync.py').read_text(encoding='utf-8-sig')
        self.check(enabled or applied)

    def test_semantic_edit(self):
        self.remote['semantic']['Betreff'] = 'Changed'
        self.check()

    def test_uid_edit(self):
        self.remote['uid'] = 'replacement'
        self.check()

    def test_location_edit(self):
        self.remote['content'] = RAW.replace('LOCATION:Home', 'LOCATION:Work')
        self.check()

    def test_status_edit(self):
        self.remote['content'] = RAW.replace('STATUS:COMPLETED', 'STATUS:NEEDS-ACTION')
        self.check()

    def test_due_edit(self):
        self.remote['content'] = RAW.replace('DUE;VALUE=DATE:20261111', 'DUE;VALUE=DATE:20261112')
        self.check()

    def test_last_modified_edit(self):
        self.remote['content'] = RAW.replace('LAST-MODIFIED:20261111T210000Z', 'LAST-MODIFIED:20261111T230000Z')
        self.check()

    def test_added_property(self):
        self.remote['content'] = RAW.replace('END:VTODO', 'X-PRIVATE:keep me\r\nEND:VTODO')
        self.check()

    def test_invalid_dtstamp(self):
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z', 'DTSTAMP:20261399T230000Z')
        self.check()

    def test_missing_dtstamp(self):
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z\r\n', '')
        self.check()

    def test_event_remains_strict(self):
        self.remote['kind'] = 'events'
        self.remote['content'] = RAW.replace('DTSTAMP:20261111T220000Z', 'DTSTAMP:20261111T230000Z')
        self.check()

if __name__ == '__main__':
    unittest.main()
