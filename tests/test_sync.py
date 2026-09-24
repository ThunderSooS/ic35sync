import copy
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bridge
import dav_model as m
import dav_sync as s


def fields(kind, title='Test'):
    if kind == 'contacts':
        return bridge.contact_semantic_to_ic35_fields({'first': title, 'last': 'Müller', 'notes': 'Zwei\nZeilen'})
    if kind == 'events':
        return {'Betreff': title, 'Notizen': 'Test', 'Start(Datum)': '20260923', 'Ende(Datum)': '20260923',
                'Start(Zeit)': '120000', 'Ende(Zeit)': '130000', 'AlrmBef': 0, 'AlrmRep': 192, 'RepAlln': 0, 'EndRepeat': ''}
    return {'Betreff': title, 'Notizen': 'Test', 'Start': '', 'Ende': '', 'Erledigt': 0,
            'Prioritaet': 1, 'category-id': 18, 'category': 'Unfiled'}


def device(kind='tasks', title='Test', rid=1):
    f = fields(kind, title)
    return {'kind': kind, 'rid': rid, 'fields': f, 'semantic': m.semantic(kind, f)}


def remote(kind='tasks', title='Test', uid='one'):
    raw = m.render(kind, fields(kind, title), uid)
    return dict(kind=kind, content=raw, etag='"1"', **m.parse(kind, raw, 'Europe/Berlin'))


def export(items):
    return {'databases': {name: {'count': len(records), 'records': records}
            for kind, name in m.DB.items()
            for records in [[m.record(kind, d['fields'], d['rid']) for d in items.values() if d['kind'] == kind]]}}


class Mapping(unittest.TestCase):
    def test_roundtrip_all_kinds(self):
        for kind in m.DB:
            f = fields(kind)
            self.assertEqual(m.semantic(kind, f), m.parse(kind, m.render(kind, f, 'u'), 'Europe/Berlin')['semantic'])

    def test_low_priority_and_completion(self):
        f = fields('tasks'); f.update(Prioritaet=0, Erledigt=1)
        actual = m.parse('tasks', m.render('tasks', f, 'u'), 'Europe/Berlin')
        self.assertEqual(actual['semantic'], m.semantic('tasks', f))

    def test_undated_firmware_defaults(self):
        f = fields('tasks'); f.update(Start='20000101', Ende='20001231')
        self.assertEqual(m.parse('tasks', m.render('tasks', f, 'u'), 'Europe/Berlin')['semantic'], m.semantic('tasks', f))

    def test_due_only_firmware_default(self):
        f = fields('tasks'); f.update(Ende='20260924')
        actual = dict(f, Start='20260924')
        self.assertEqual(m.semantic('tasks', actual), m.semantic('tasks', f))

    def test_timezone(self):
        raw = m.render('events', fields('events'), 'u').replace('20260923T120000', '20260923T100000Z').replace('20260923T130000', '20260923T110000Z')
        self.assertEqual(m.parse('events', raw, 'Europe/Berlin')['fields']['Start(Zeit)'], '120000')

    def test_unsupported_no_truncation(self):
        f = fields('tasks'); f['Betreff'] = 'x' * 61
        with self.assertRaises(ValueError): m.validate('tasks', f)
        f['Betreff'] = 'Emoji 😀'
        with self.assertRaises(ValueError): m.validate('tasks', f)

    def test_recurring_and_allday_rejected(self):
        raw = m.render('events', fields('events'), 'u')
        for bad in (raw.replace('END:VEVENT', 'RRULE:FREQ=DAILY\r\nEND:VEVENT'),
                    raw.replace('DTSTART:20260923T120000', 'DTSTART;VALUE=DATE:20260923')):
            with self.assertRaises(ValueError): m.parse('events', bad, 'Europe/Berlin')

    def test_unknown_properties_preserved(self):
        raw = m.render('events', fields('events'), 'u').replace('END:VEVENT', 'LOCATION:Büro\r\nEND:VEVENT')
        changed = fields('events', 'Changed')
        self.assertIn('LOCATION:Büro', m.render('events', changed, 'u', raw))

    def test_complex_contact_rejected(self):
        raw = m.render('contacts', fields('contacts'), 'u')
        raw = raw.replace('END:VCARD', 'TEL;TYPE=HOME:123\r\nTEL;TYPE=HOME:456\r\nEND:VCARD')
        with self.assertRaises(ValueError): m.parse('contacts', raw, 'Europe/Berlin')

    def test_contact_escaped_fields(self):
        f = fields('contacts'); f.update(Firma='A;B', Strasse='Weg; 1', **{'E-Mail1': 'test@example.invalid'})
        self.assertEqual(m.parse('contacts', m.render('contacts', f, 'u'), 'Europe/Berlin')['semantic'], m.semantic('contacts', f))


class Plan(unittest.TestCase):
    def setUp(self):
        self.d = device(); self.r = remote()
        self.h = '/ic35/calendar/a.ics'
        self.binding = {'tasks:1': {'href': self.h, 'uid': self.r['uid'], 'device': self.d['semantic'], 'remote': self.r['semantic']}}

    def plan(self, d, r, bindings=None):
        return s.build_plan(self.binding if bindings is None else bindings, d, r)

    def test_initial_match(self):
        ops, conflicts, _ = self.plan({'tasks:1': self.d}, {self.h: self.r}, {})
        self.assertEqual([op['action'] for op in ops], ['bind']); self.assertFalse(conflicts)

    def test_independent_creates(self):
        ops, _, _ = self.plan({'tasks:1': self.d}, {self.h: remote(title='Other')}, {})
        self.assertEqual([op['action'] for op in ops], ['write_remote', 'write_device'])

    def test_updates_both_directions(self):
        for d, r, action in [(device(title='Changed'), self.r, 'write_remote'), (self.d, remote(title='Changed'), 'write_device')]:
            ops, conflicts, _ = self.plan({'tasks:1': d}, {self.h: r})
            self.assertFalse(conflicts); self.assertEqual(ops[0]['action'], action)

    def test_delete_both_directions(self):
        for d, r, action in [({}, {self.h: self.r}, 'delete_remote'), ({'tasks:1': self.d}, {}, 'delete_device')]:
            ops, conflicts, _ = self.plan(d, r)
            self.assertFalse(conflicts); self.assertEqual(ops[0]['action'], action)

    def test_conflicts(self):
        for d, r in [({'tasks:1': device(title='A')}, {self.h: remote(title='B')}),
                     ({}, {self.h: remote(title='Changed')}), ({'tasks:1': device(title='Changed')}, {}),
                     ({}, {self.h: remote(uid='replaced')})]:
            _, conflicts, _ = self.plan(d, r)
            self.assertTrue(conflicts)

    def test_unsupported_protects_bound_resource(self):
        bad = dict(self.r, error='series')
        ops, conflicts, skipped = self.plan({}, {self.h: bad})
        self.assertFalse(ops); self.assertFalse(conflicts); self.assertTrue(skipped)

    def test_ambiguous_duplicate_conflict(self):
        _, conflicts, _ = self.plan({'tasks:1': self.d}, {self.h: self.r, '/ic35/calendar/b.ics': self.r}, {})
        self.assertTrue(conflicts)

    def test_incomplete_read_blocks_deletions(self):
        dump = export({}); dump['databases']['Schedule']['count'] = 1
        with self.assertRaises(ValueError): s.device_snapshot(dump)

    def test_unmapped_remote_edit_blocks_deletion(self):
        self.binding['tasks:1']['remote_content'] = self.r['content']
        edited = dict(self.r, content=self.r['content'].replace('END:VTODO', 'LOCATION:Other\r\nEND:VTODO'))
        _, conflicts, _ = self.plan({}, {self.h: edited})
        self.assertTrue(conflicts)

    def test_category_edit_blocks_device_deletion(self):
        self.binding['tasks:1']['device_fields'] = dict(self.d['fields'])
        self.d['fields']['category'] = 'Business'
        _, conflicts, _ = self.plan({'tasks:1': self.d}, {})
        self.assertTrue(conflicts)


class TransportGuard(unittest.TestCase):
    def test_changed_device_source_blocks_remote_write(self):
        adapter = s.Device(None)
        before = device()
        op = {'key': 'tasks:1', 'device': before, 'remote': remote()}
        with patch.object(s.p, 'open_database', return_value=b'fd'), patch.object(s.p, 'close_database'), \
             patch.object(adapter, 'read', return_value=m.record('tasks', fields('tasks', 'Changed'))):
            with self.assertRaises(RuntimeError): adapter.confirm(op)

    def test_reappearing_device_blocks_remote_delete(self):
        adapter = s.Device(None)
        op = {'key': 'tasks:1', 'device': None, 'remote': remote()}
        with patch.object(s.p, 'open_database', return_value=b'fd'), patch.object(s.p, 'close_database'), \
             patch.object(s.p, 'read_database_count', return_value=1), \
             patch.object(s.p, 'read_record_raw_by_index', return_value=b'record'), \
             patch.object(s.p, 'decode_record', return_value=m.record('tasks', fields('tasks'))):
            with self.assertRaises(RuntimeError): adapter.confirm(op)


class FakeDAV:
    zone = 'Europe/Berlin'
    def __init__(self): self.items = {}; self.fail_after_write = False
    def snapshot(self): return copy.deepcopy(self.items)
    def check(self, href, expected):
        if self.items.get(href) != expected: raise RuntimeError('concurrent remote edit')
    def write(self, href, content, before):
        self.check(href, before)
        kind = 'contacts' if 'BEGIN:VCARD' in content else 'tasks' if 'BEGIN:VTODO' in content else 'events'
        self.items[href] = dict(kind=kind, content=content, etag='"new"', **m.parse(kind, content, self.zone))
        if self.fail_after_write: raise RuntimeError('lost acknowledgement')
    def delete(self, href, before): self.check(href, before); del self.items[href]


class FakeDevice:
    def __init__(self): self.items = {}; self.fail_after_write = False
    def confirm(self, op):
        if self.items.get(op['key']) != op['device']: raise RuntimeError('concurrent device edit')
    def execute(self, op):
        self.confirm(op)
        if op['action'] == 'delete_device': del self.items[op['key']]; return
        r = op['remote']; rid = op['device']['rid'] if op['device'] else 1 + max([x['rid'] for x in self.items.values()] or [0])
        d = dict(kind=r['kind'], rid=rid, fields=copy.deepcopy(r['fields']), semantic=copy.deepcopy(r['semantic']))
        self.items[f'{r["kind"]}:{rid}'] = d
        if self.fail_after_write: raise RuntimeError('lost acknowledgement')
        return d


class Engine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        # Reconciliation tests isolate disk crypto; separate Windows smoke checks real DPAPI.
        def write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
        self.pw = patch.object(s.storage, 'write_json', write); self.pr = patch.object(s.storage, 'read_json', lambda path: json.loads(path.read_text()))
        self.pw.start(); self.pr.start()
        self.d, self.r = FakeDevice(), FakeDAV()
    def tearDown(self): self.pw.stop(); self.pr.stop(); self.tmp.cleanup()
    def run_sync(self): return s.Sync(self.root, 'test', self.r, self.d, lambda x: None).run(export(self.d.items))

    def test_end_to_end_all_kinds(self):
        for kind in m.DB:
            self.d.items[f'{kind}:1'] = device(kind)
        self.run_sync(); self.assertEqual(len(self.r.items), 3)
        result = self.run_sync(); self.assertEqual(result['stats']['write_device'], 0)
        for href, r in list(self.r.items.items()): self.r.items[href] = remote(r['kind'], 'Changed', r['uid'])
        self.run_sync(); self.assertTrue(all('Changed' in str(x['semantic']) for x in self.d.items.values()))
        self.r.items.clear(); self.run_sync(); self.assertFalse(self.d.items)

    def test_device_deletion_propagates(self):
        self.d.items['tasks:1'] = device(); self.run_sync()
        self.d.items.clear(); self.run_sync(); self.assertFalse(self.r.items)

    def test_recover_remote_create_after_lost_ack(self):
        self.d.items['tasks:1'] = device(); self.r.fail_after_write = True
        with self.assertRaises(RuntimeError): self.run_sync()
        self.assertTrue((self.root / 'pending.dpapi').exists())
        self.r.fail_after_write = False; self.run_sync()
        self.assertEqual(len(self.r.items), 1); self.assertFalse((self.root / 'pending.dpapi').exists())

    def test_recover_device_create_after_lost_ack(self):
        self.r.items['/ic35/calendar/a.ics'] = remote(); self.d.fail_after_write = True
        with self.assertRaises(RuntimeError): self.run_sync()
        self.d.fail_after_write = False; self.run_sync()
        self.assertEqual(len(self.d.items), 1); self.assertFalse((self.root / 'pending.dpapi').exists())

    def test_conflict_no_writes(self):
        self.d.items['tasks:1'] = device(); self.run_sync()
        href = next(iter(self.r.items)); self.r.items[href] = remote(title='R', uid=self.r.items[href]['uid'])
        self.d.items['tasks:1'] = device(title='D')
        before = copy.deepcopy((self.d.items, self.r.items))
        with self.assertRaises(RuntimeError): self.run_sync()
        self.assertEqual(before, (self.d.items, self.r.items))


class RealDAV(unittest.TestCase):
    def test_local_server_and_etags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); bridge.ensure_radicale_storage(root / 'dav')
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
            command = [sys.executable, str(Path(bridge.__file__).with_name('radicale_windows_launcher.py')),
                       '--config', '', '--storage-filesystem-folder', str(root / 'dav'), '--storage-type', 'multifilesystem',
                       '--auth-type', 'none', '--server-hosts', f'127.0.0.1:{port}']
            with (root / 'server.log').open('w') as log:
                proc = subprocess.Popen(command, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    dav = s.DAV(f'http://127.0.0.1:{port}', 'Europe/Berlin')
                    for _ in range(100):
                        try: self.assertEqual(dav.snapshot(), {}); break
                        except OSError: time.sleep(.1)
                    else: self.fail((root / 'server.log').read_text())
                    for kind in m.DB:
                        href = f'/ic35/{"addressbook" if kind == "contacts" else "calendar"}/{kind}.{"vcf" if kind == "contacts" else "ics"}'
                        dav.write(href, m.render(kind, fields(kind), kind), None)
                        before = dav.snapshot()[href]
                        dav.write(href, m.render(kind, fields(kind, 'Changed'), kind, before['content']), before)
                        with self.assertRaises(RuntimeError): dav.delete(href, before)
                        dav.delete(href, dav.snapshot()[href]); dav.check(href, None)
                finally:
                    proc.terminate(); proc.wait(timeout=10)


if __name__ == '__main__': unittest.main()
