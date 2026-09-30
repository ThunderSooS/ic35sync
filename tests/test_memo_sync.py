import tempfile
import unittest
from pathlib import Path

import memo_sync as m


class FakeDevice:
    def __init__(self, memos=()):
        self.memos = {x.rid: x for x in memos}
        self.next = 100
        self.writes = self.deletes = 0

    def read_all(self):
        return [m.Memo(x.rid, x.subject, x.body, x.category_id, x.category) for x in self.memos.values()]

    def write(self, subject, body, category_id, category, rid=None):
        m.check_device_text(subject, body)
        self.writes += 1
        if rid is None:
            self.next += 1
            rid = self.next
        self.memos[rid] = m.Memo(rid, subject, m.norm(body), category_id, category)
        return self.memos[rid]

    def delete(self, rid):
        self.deletes += 1
        del self.memos[rid]


class MemoSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / 'Notizen'
        self.state = None
        self.dev = FakeDevice([m.Memo(1, 'Einkauf', 'Milch\nBrot', 0x0F, 'Unfiled'),
                               m.Memo(2, 'a:b', 'x', 0x0D, 'Business'),
                               m.Memo(3, 'Ideen', '', 0x0F, 'Unfiled')])
        self.logs = []

    def tearDown(self):
        self.tmp.cleanup()

    def sync(self):
        def save(state):
            import json
            self.state = json.loads(json.dumps(state))
        return m.MemoSync(self.dir, self.dev, lambda: self.state, save, self.logs.append).run()

    def f(self, rid, subject):
        return self.dir / m.tagged_name(subject, rid)

    def test_initial_export_and_idempotent(self):
        s = self.sync()
        self.assertEqual(s['to_folder'], 3)
        self.assertEqual(self.f(1, 'Einkauf').read_bytes(), '\ufeffMilch\r\nBrot'.encode())
        self.assertTrue((self.dir / 'a_b [IC35-000002].txt').exists())
        s = self.sync()
        self.assertEqual(sum(s.values()), 0)
        self.assertEqual(self.dev.writes, 0)

    def test_file_edit_goes_to_device_keeping_unsafe_subject(self):
        self.sync()
        (self.dir / 'a_b [IC35-000002].txt').write_text('neu', encoding='utf-8')
        s = self.sync()
        self.assertEqual(s['to_device'], 1)
        self.assertEqual((self.dev.memos[2].subject, self.dev.memos[2].body, self.dev.memos[2].category), ('a:b', 'neu', 'Business'))

    def test_rename_changes_subject(self):
        self.sync()
        self.f(1, 'Einkauf').rename(self.dir / 'Wocheneinkauf [IC35-000001].txt')
        self.sync()
        self.assertEqual(self.dev.memos[1].subject, 'Wocheneinkauf')
        self.assertEqual(self.dev.memos[1].body, 'Milch\nBrot')

    def test_device_edit_updates_and_renames_file(self):
        self.sync()
        self.dev.memos[1] = m.Memo(1, 'Markt', 'Käse', 0x0F, 'Unfiled')
        s = self.sync()
        self.assertEqual(s['to_folder'], 1)
        self.assertFalse(self.f(1, 'Einkauf').exists())
        self.assertEqual(m.read_text(self.f(1, 'Markt')), 'Käse')

    def test_delete_file_deletes_on_device(self):
        self.sync()
        self.f(3, 'Ideen').unlink()
        s = self.sync()
        self.assertEqual(s['deleted_device'], 1)
        self.assertNotIn(3, self.dev.memos)
        self.assertEqual(sum(self.sync().values()), 0)

    def test_delete_on_device_deletes_file(self):
        self.sync()
        del self.dev.memos[1]
        s = self.sync()
        self.assertEqual(s['deleted_folder'], 1)
        self.assertFalse(self.f(1, 'Einkauf').exists())

    def test_new_file_created_on_device(self):
        self.sync()
        (self.dir / 'Telefon.txt').write_text('0123\n456', encoding='utf-8')
        s = self.sync()
        self.assertEqual(s['to_device'], 1)
        self.assertEqual((self.dev.memos[101].subject, self.dev.memos[101].body, self.dev.memos[101].category_id), ('Telefon', '0123\n456', 0x0F))
        self.assertFalse((self.dir / 'Telefon.txt').exists())
        self.assertTrue(self.f(101, 'Telefon').exists())
        self.assertEqual(sum(self.sync().values()), 0)

    def test_conflicts_write_nothing(self):
        self.sync()
        self.f(1, 'Einkauf').write_text('Datei', encoding='utf-8')
        self.dev.memos[1] = m.Memo(1, 'Einkauf', 'Gerät', 0x0F, 'Unfiled')
        self.f(3, 'Ideen').write_text('geändert', encoding='utf-8')
        del self.dev.memos[3]
        s = self.sync()
        self.assertEqual(s['conflicts'], 2)
        self.assertEqual(self.dev.writes, 0)
        self.assertEqual(m.read_text(self.f(1, 'Einkauf')), 'Datei')
        self.assertTrue(self.f(3, 'Ideen').exists())

    def test_same_change_on_both_sides_is_not_a_conflict(self):
        self.sync()
        self.f(1, 'Einkauf').write_text('gleich', encoding='utf-8')
        self.dev.memos[1] = m.Memo(1, 'Einkauf', 'gleich', 0x0F, 'Unfiled')
        s = self.sync()
        self.assertEqual((s['conflicts'], self.dev.writes), (0, 0))

    def test_too_long_or_unsupported_text_is_skipped_not_truncated(self):
        self.sync()
        (self.dir / 'Lang.txt').write_text('x' * 300, encoding='utf-8')
        (self.dir / 'Emoji.txt').write_text('Hallo 😀', encoding='utf-8')
        s = self.sync()
        self.assertEqual((s['skipped'], self.dev.writes), (2, 0))
        self.assertTrue((self.dir / 'Lang.txt').exists())

    def test_crlf_counts_towards_limit(self):
        with self.assertRaises(ValueError):
            m.check_device_text('a', 'x\n' * 128)
        m.check_device_text('a', 'x\n' * 84)

    def test_safety_all_files_missing(self):
        self.sync()
        for p in self.dir.glob('*.txt'):
            p.unlink()
        with self.assertRaises(m.Stop):
            self.sync()
        self.assertEqual(self.dev.deletes, 0)

    def test_safety_missing_folder_and_empty_device(self):
        self.sync()
        self.dev.memos.clear()
        with self.assertRaises(m.Stop):
            self.sync()
        self.assertEqual(len(list(self.dir.glob('*.txt'))), 3)
        for p in self.dir.glob('*.txt'):
            p.unlink()
        self.dir.rmdir()
        with self.assertRaises(m.Stop):
            self.sync()

    def test_interrupted_create_is_resumed_without_duplicate(self):
        self.sync()
        (self.dir / 'Neu.txt').write_text('abc', encoding='utf-8')
        original = self.dev.write

        def crash(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError('Verbindung verloren')
        self.dev.write = crash
        s = self.sync()
        self.assertEqual(s['skipped'], 1)
        self.dev.write = original
        s = self.sync()
        self.assertEqual(self.dev.writes, 1)
        self.assertEqual(len(self.dev.memos), 4)
        self.assertTrue(self.f(101, 'Neu').exists())

    def test_first_run_with_existing_matching_files_binds(self):
        self.dir.mkdir()
        m.atomic_write(self.f(1, 'Einkauf'), 'Milch\nBrot')
        m.atomic_write(self.f(3, 'Ideen'), 'anders')
        s = self.sync()
        self.assertEqual((s['to_folder'], s['conflicts']), (1, 1))
        self.assertIn('1', self.state['bindings'])
        self.assertNotIn('3', self.state['bindings'])

    def test_encode_memo_layout(self):
        data = m.encode_memo('Ab', 'x\ny', 0x0F, 'Unfiled')
        self.assertEqual(data, bytes([2, 4, 1, 7]) + b'Abx\r\ny\x0fUnfiled')

class DeviceFrames(unittest.TestCase):
    def test_create_update_delete_frames(self):
        import ic35_protocol as proto
        sent, store = [], {}
        saved = {n: getattr(proto, n) for n in ('open_database', 'close_database', 'l1_transaction',
                 'read_record_raw_by_id', 'command_transaction', 'read_database_count', 'read_record_raw_by_index')}
        def l1(ser, request, label, **kw):
            sent.append(request)
            if request[0] == 0x02:
                return b'\x90\x03\x00'
            rid = 7
            return b'\xA0\x0A\x00\x49\x07\x00' + rid.to_bytes(3, 'little') + b'\x06'
        def raw_by_id(ser, db, fd, rid):
            data = store['data']
            return rid.to_bytes(3, 'little') + b'\x06\x00' + data
        try:
            proto.open_database = lambda ser, db: b'\x03\x00'
            proto.close_database = lambda *a: True
            proto.l1_transaction = l1
            proto.read_record_raw_by_id = raw_by_id
            proto.log = lambda *a: None
            dev = m.Device(None, lambda *a: None)
            store['data'] = m.encode_memo('Titel', 'a\nb', 15, 'Unfiled')
            memo = dev.write('Titel', 'a\nb', 15, 'Unfiled')
            self.assertEqual((memo.rid, memo.subject, memo.body), (7, 'Titel', 'a\nb'))
            first = sent[0]
            l4 = first[6:]
            self.assertEqual(l4[:2], b'\x01\x08')
            self.assertEqual(l4[2:4], b'\x03\x00')
            self.assertEqual(l4[4:8], bytes(4))
            self.assertEqual(l4[8:11], m.MAGIC)
            self.assertEqual(l4[13:17], len(store['data']).to_bytes(4, 'little'))
            sent.clear()
            dev.write('Titel', 'a\nb', 15, 'Unfiled', rid=7)
            self.assertEqual(sent[0][6:][:8], b'\x01\x09\x03\x00\x07\x00\x00\x06')
            store['data'] = m.encode_memo('X' * 60, 'y' * 200, 15, 'Unfiled')
            sent.clear()
            dev.write('X' * 60, 'y' * 200, 15, 'Unfiled')
            self.assertEqual([r[0] for r in sent], [0x02, 0x02, 0x02, 0x82])
            cmds = []
            proto.command_transaction = lambda ser, l2, l4, label, **kw: cmds.append(l4) or b''
            proto.read_database_count = lambda *a: 0
            dev.delete(7)
            self.assertEqual(cmds, [b'\x01\x02\x03\x00\x07\x00\x00\x06'])
        finally:
            for n, v in saved.items():
                setattr(proto, n, v)


if __name__ == '__main__':
    unittest.main()
