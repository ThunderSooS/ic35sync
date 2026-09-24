import copy
import unittest
import dav_model as m
import dav_sync as s
import test_sync as base


def series():
    raw = m.render('events', base.fields('events'), 'series').replace('END:VEVENT', 'RRULE:FREQ=WEEKLY\r\nEND:VEVENT')
    return dict(kind='events', content=raw, etag='series', error='series unsupported')


class SeriesGuard(unittest.TestCase):
    def test_matching_occurrence_not_uploaded(self):
        d = base.device('events')
        d['fields']['AlrmBef'] = 4
        d['semantic'] = m.semantic('events', d['fields'])
        ops, conflicts, skipped = s.build_plan({}, {'events:1': d}, {'series': series()})
        self.assertEqual(ops, [])
        self.assertFalse(conflicts)
        self.assertTrue(skipped)

    def test_different_day_is_not_suppressed(self):
        d = base.device('events')
        d['fields'].update({'Start(Datum)': '20260924', 'Ende(Datum)': '20260924'})
        d['semantic'] = m.semantic('events', d['fields'])
        ops, _, _ = s.build_plan({}, {'events:1': d}, {'series': series()})
        self.assertEqual([o['action'] for o in ops], ['write_remote'])

    def test_excluded_occurrence_not_matched(self):
        r = series(); r['content'] = r['content'].replace('END:VEVENT', 'EXDATE:20260923T120000\r\nEND:VEVENT')
        self.assertFalse(m.series_protects(base.fields('events'), {'series': r}, 'Europe/Berlin'))

    def test_other_data_types_unchanged(self):
        ops, _, _ = s.build_plan({}, {'tasks:1': base.device()}, {'series': series()})
        self.assertEqual([o['action'] for o in ops], ['write_remote'])

    def test_conservative_guard_never_authorizes_cleanup(self):
        r = series(); r['content'] = r['content'].replace('FREQ=WEEKLY', 'FREQ=SECONDLY')
        self.assertTrue(m.series_protects(base.fields('events'), {'series': r}, 'Europe/Berlin'))
        self.assertFalse(m.series_protects(base.fields('events'), {'series': r}, 'Europe/Berlin', exact=True))

    def test_weekly_count_is_respected(self):
        r = series(); r['content'] = r['content'].replace('FREQ=WEEKLY', 'FREQ=WEEKLY;COUNT=1')
        f = base.fields('events'); f.update({'Start(Datum)': '20260930', 'Ende(Datum)': '20260930'})
        self.assertFalse(m.series_protects(f, {'series': r}, 'Europe/Berlin', exact=True))

    def test_weekly_interval_is_respected(self):
        r = series(); r['content'] = r['content'].replace('FREQ=WEEKLY', 'FREQ=WEEKLY;INTERVAL=2')
        f = base.fields('events'); f.update({'Start(Datum)': '20260930', 'Ende(Datum)': '20260930'})
        self.assertFalse(m.series_protects(f, {'series': r}, 'Europe/Berlin', exact=True))


class Recovery(unittest.TestCase):
    setUp = base.Engine.setUp
    tearDown = base.Engine.tearDown
    run_sync = base.Engine.run_sync

    def prepare(self):
        d = base.device('events'); self.d.items['events:1'] = d
        uid = 'ic35-events-1@local'
        r = base.remote('events', uid=uid)
        self.href = '/ic35/calendar/ic35-events-1.ics'
        op = dict(id='repair', action='write_remote', key='events:1', href=self.href,
                  device=copy.deepcopy(d), remote=None, uid=uid, content=r['content'])
        s.storage.write_json(self.root / 'pending.dpapi', op)
        f = dict(d['fields'], AlrmBef=4)
        raw = m.render('events', f, uid)
        r = dict(kind='events', etag='new', content=raw, **m.parse('events', raw, self.r.zone))
        self.r.items = {self.href: r, 'series': series()}

    def test_remove_only_journal_duplicate_and_do_not_recreate(self):
        self.prepare()
        before = copy.deepcopy(self.d.items)
        self.run_sync()
        self.assertEqual(set(self.r.items), {'series'})
        self.assertEqual(self.d.items, before)
        self.assertFalse((self.root / 'pending.dpapi').exists())
        self.assertTrue((self.root / 'backups/repair-duplicate.dpapi').exists())
        self.run_sync()
        self.assertEqual(set(self.r.items), {'series'})

    def test_changed_duplicate_is_not_deleted(self):
        self.prepare()
        self.r.items[self.href]['semantic']['Notizen'] = 'user edit'
        with self.assertRaises(RuntimeError): self.run_sync()
        self.assertIn(self.href, self.r.items)
        self.assertTrue((self.root / 'pending.dpapi').exists())

    def test_location_is_not_discarded(self):
        self.prepare()
        r = self.r.items[self.href]
        r['content'] = r['content'].replace('END:VEVENT', 'LOCATION:User location\r\nEND:VEVENT')
        with self.assertRaises(RuntimeError): self.run_sync()
        self.assertIn(self.href, self.r.items)

    def test_lost_delete_ack_recovers(self):
        self.prepare()
        delete = self.r.delete
        def lost_ack(href, before):
            delete(href, before)
            raise RuntimeError('lost delete reply')
        self.r.delete = lost_ack
        with self.assertRaises(RuntimeError): self.run_sync()
        self.r.delete = delete
        self.run_sync()
        self.assertEqual(set(self.r.items), {'series'})
        self.assertFalse((self.root / 'pending.dpapi').exists())

    def test_single_original_different_alarm_is_bound_after_cleanup(self):
        self.prepare()
        self.r.items.pop('series')
        original = copy.deepcopy(self.r.items[self.href])
        original['uid'] = 'original'
        original['content'] = original['content'].replace('ic35-events-1@local', 'original')
        self.r.items['original'] = original
        first = self.run_sync()
        self.assertEqual(set(self.r.items), {'original'})
        self.assertEqual(first['stats']['write_remote'], 0)
        for _ in range(3):
            result = self.run_sync()
            self.assertEqual(result['stats']['write_remote'], 0)
            self.assertEqual(result['stats']['delete_remote'], 0)
            self.assertEqual(result['stats']['write_device'], 0)
            self.assertEqual(set(self.r.items), {'original'})

    def test_successful_create_is_not_deleted_without_original(self):
        self.prepare(); self.r.items.pop('series')
        self.r.items[self.href] = base.remote('events', uid='ic35-events-1@local')
        self.run_sync()
        self.assertIn(self.href, self.r.items)
        self.assertFalse((self.root / 'pending.dpapi').exists())

    def test_provider_added_alarm_after_lost_create_ack_is_bound(self):
        self.prepare(); self.r.items.pop('series')
        self.run_sync()
        before = copy.deepcopy((self.d.items, self.r.items))
        self.run_sync()
        self.assertEqual((self.d.items, self.r.items), before)
        self.assertFalse((self.root / 'pending.dpapi').exists())

    def test_provider_alarm_does_not_override_explicit_update(self):
        self.prepare()
        d = self.d.items['events:1']; r = self.r.items[self.href]
        self.assertTrue(s.confirmed_write(d, r, r['uid'], True))
        self.assertFalse(s.confirmed_write(d, r, r['uid'], False))
        self.assertFalse(s.confirmed_write(d, r, 'different-uid', True))

    def test_initial_matching_preserves_different_reminders(self):
        self.d.items['events:1'] = base.device('events')
        f = base.fields('events'); f['AlrmBef'] = 4
        raw = m.render('events', f, 'original')
        self.r.items['original'] = dict(kind='events', content=raw, etag='1', **m.parse('events', raw, self.r.zone))
        before = copy.deepcopy((self.d.items, self.r.items))
        self.run_sync(); self.run_sync()
        self.assertEqual((self.d.items, self.r.items), before)

    def test_ambiguous_originals_block_initial_matching(self):
        self.d.items['events:1'] = base.device('events')
        self.r.items = {'a': base.remote('events', uid='a'), 'b': base.remote('events', uid='b')}
        with self.assertRaises(RuntimeError): self.run_sync()


if __name__ == '__main__': unittest.main()
