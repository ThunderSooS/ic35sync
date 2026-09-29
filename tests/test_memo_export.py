import tempfile
import unittest
from pathlib import Path

import memo_export as m


def rec(rid, subject, body):
    return {'record_id': rid, 'file_id': 6, 'fields': {
        'Betreff': {'value': subject}, 'Notizen': {'value': body}}}


class MemoExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_safe_names(self):
        self.assertEqual(m.safe_subject('a/b:c?'), 'a_b_c_')
        self.assertEqual(m.safe_subject(''), 'Notiz')
        self.assertEqual(m.safe_subject('CON'), 'Notiz CON')
        self.assertEqual(m.file_name(rec(12, 'Einkauf.', 'x')), 'Einkauf [IC35-000012].txt')

    def test_create_update_rename_keep(self):
        stray = self.dir / 'eigene.txt'; stray.write_text('bleibt')
        s = m.write_memos([rec(1, 'A', 'eins\nzwei')], self.dir, lambda *_: None)
        self.assertEqual(s['created'], 1)
        path = self.dir / 'A [IC35-000001].txt'
        self.assertEqual(path.read_bytes(), '\ufeffeins\r\nzwei'.encode('utf-8'))
        s = m.write_memos([rec(1, 'A', 'eins\nzwei')], self.dir, lambda *_: None)
        self.assertEqual(s['unchanged'], 1)
        s = m.write_memos([rec(1, 'A', 'neu')], self.dir, lambda *_: None)
        self.assertEqual(s['updated'], 1)
        s = m.write_memos([rec(1, 'B', 'neu')], self.dir, lambda *_: None)
        self.assertEqual(s['renamed'], 1)
        self.assertFalse(path.exists())
        self.assertTrue((self.dir / 'B [IC35-000001].txt').exists())
        m.write_memos([], self.dir, lambda *_: None)
        self.assertTrue((self.dir / 'B [IC35-000001].txt').exists())
        self.assertEqual(stray.read_text(), 'bleibt')


if __name__ == '__main__':
    unittest.main()
