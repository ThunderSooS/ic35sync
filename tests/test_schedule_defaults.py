import copy
import unittest
import dav_model as m
import test_sync as base
from test_sync import fields


class ScheduleDefaults(unittest.TestCase):
    def setUp(self):
        self.expected = fields('events')
        self.expected.update(AlrmRep=0, AlrmBef=4)
        self.actual = dict(self.expected, AlrmRep=None, EndRepeat='20260923')

    def test_observed_defaults_match(self):
        self.assertTrue(m.matches_event_written(self.actual, self.expected))
        self.assertEqual(m.semantic('events', self.actual), m.semantic('events', self.expected))

    def test_changed_content_still_rejected(self):
        for key, value in [('Betreff', 'Other'), ('Start(Zeit)', '140000'), ('AlrmBef', 5), ('AlrmRep', 64), ('RepAlln', 2), ('EndRepeat', 'invalid')]:
            with self.subTest(key=key):
                self.assertFalse(m.matches_event_written(dict(self.actual, **{key: value}), self.expected))

    def test_repeat_flag_still_rejected(self):
        for flag in (1, 2, 5, 8):
            with self.assertRaises(ValueError): m.semantic('events', dict(self.actual, AlrmRep=flag))


class ScheduleRecovery(unittest.TestCase):
    setUp = base.Engine.setUp
    tearDown = base.Engine.tearDown
    run_sync = base.Engine.run_sync
    def test_resume_existing_pending_without_duplicate(self):
        f = fields('events'); f.update(AlrmRep=0, AlrmBef=4)
        content = m.render('events', f, 'recovery-test')
        href = '/ic35/calendar/test.ics'
        self.r.items[href] = dict(kind='events', content=content, etag='"1"', **m.parse('events', content, self.r.zone))
        execute = self.d.execute
        def firmware_write(op):
            result = execute(op)
            result['fields'].update(AlrmRep=None, EndRepeat='20260923')
            result['semantic'] = m.semantic('events', result['fields'])
            raise RuntimeError('Previous version rejected firmware defaults after successful write')
        self.d.execute = firmware_write
        with self.assertRaises(RuntimeError): self.run_sync()
        self.assertTrue((self.root / 'pending.dpapi').exists())
        self.d.execute = execute
        result = self.run_sync()
        self.assertEqual(len(self.d.items), 1)
        self.assertEqual(result['stats']['write_device'], 0)
        self.assertFalse((self.root / 'pending.dpapi').exists())
        self.assertEqual(self.run_sync()['stats']['write_device'], 0)


if __name__ == '__main__': unittest.main()
