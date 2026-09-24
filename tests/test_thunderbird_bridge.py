import copy
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
import unittest
from urllib import request, error
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from thunderbird_rpc import Broker
from thunderbird_calendar import Calendars
from dav_sync import build_plan
from test_sync import device, remote


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token = secrets.token_urlsafe(32)
        self.broker = Broker(self.tmp.name, port=0, pairing={'token': self.token, 'profile': 'test-profile'})
    def tearDown(self): self.broker.close(); self.tmp.cleanup()
    def post(self, path='/result', body=None, headers=None):
        data = dict(protocol=1, profile='test-profile', session='test-session', id='unused', ok=True, data=None)
        data.update(body or {})
        hdr = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}
        hdr.update(headers or {})
        req = request.Request(f'http://127.0.0.1:{self.broker.port}' + path, json.dumps(data).encode(), hdr, method='POST')
        with request.urlopen(req, timeout=15) as res: return json.load(res)
    def rejected(self, **kwargs):
        with self.assertRaises(error.HTTPError) as caught: self.post(**kwargs)
        self.assertIn(caught.exception.code, (400, 403, 409))
    def test_wrong_secret_denied(self): self.rejected(headers={'Authorization': 'Bearer wrong'})
    def test_website_origin_denied(self): self.rejected(headers={'Origin': 'https://example.invalid'})
    def test_wrong_host_denied(self): self.rejected(headers={'Host': 'example.invalid'})
    def test_other_profile_denied(self):
        self.post()
        self.rejected(body={'profile': 'other-profile', 'session': 'other-session'})

    def test_repair_pairing_after_stale_profile(self):
        self.post(body={'profile': 'old-profile'})
        self.broker.last_seen = 0
        self.post(body={'profile': 'new-profile'})
        self.assertEqual(self.broker.pairing['profile'], 'new-profile')
    def test_protocol_mismatch_denied(self): self.rejected(body={'protocol': 99})
    def test_other_live_instance_denied(self):
        self.post(); self.rejected(body={'session': 'other-session'})
    def test_roundtrip_no_reexecution(self):
        self.post()
        outcome = []
        def call(): outcome.append(self.broker.call('list', timeout=3))
        worker = threading.Thread(target=call); worker.start()
        job = self.post('/poll')
        self.assertEqual(job['method'], 'list')
        self.post(body={'id': job['id'], 'data': {'calendars': []}})
        worker.join(3)
        self.assertEqual(outcome, [{'calendars': []}])
        self.post(body={'id': job['id'], 'data': 'duplicate reply'})
        self.assertEqual(outcome, [{'calendars': []}])
        self.assertFalse(self.broker.pending)
    def test_timeout_does_not_leave_runnable_job(self):
        self.post()
        with self.assertRaises(RuntimeError): self.broker.call('write', timeout=.01)
        self.assertFalse(self.broker.pending)
    def test_no_connection_never_queues_write(self):
        with self.assertRaises(RuntimeError): self.broker.call('write')
        self.assertTrue(self.broker.jobs.empty())


class CalendarAdapterTests(unittest.TestCase):
    def setUp(self):
        self.local = Mock(zone='Europe/Berlin')
        self.local.snapshot.return_value = {'/ic35/addressbook/a.vcf': remote('contacts'), '/ic35/calendar/local.ics': remote('events', 'Local'), '/ic35/calendar/task.ics': remote('tasks')}
        self.broker = Mock(pairing={'profile': 'test-profile'})
        self.remote = remote('events', 'Twitch')
        self.broker.call.return_value = {'complete': True, 'items': [{'uid': self.remote['uid'], 'content': self.remote['content'], 'etag': self.remote['etag']}]}
        self.adapter = Calendars(self.local, self.broker, {'events': 'selected-calendar', 'tasks': ''})
    def test_only_selected_calendar_replaces_local_events(self):
        snapshot = self.adapter.snapshot()
        self.assertEqual(len(snapshot), 3)
        self.assertNotIn('/ic35/calendar/local.ics', snapshot)
        self.assertIn('/ic35/calendar/task.ics', snapshot)
        self.assertEqual(snapshot[self.adapter.href('events', self.remote['uid'])]['fields']['Betreff'], 'Twitch')
    def test_incomplete_snapshot_stops(self):
        self.broker.call.return_value = {'complete': False, 'items': []}
        with self.assertRaises(RuntimeError): self.adapter.snapshot()
    def test_other_calendar_href_cannot_be_written(self):
        with self.assertRaises(ValueError): self.adapter.write('/thunderbird/events/another/id', '', None)
        self.broker.call.assert_not_called()
    def test_state_separates_calendar_and_profile(self):
        first = self.adapter.state_key()
        self.adapter.selections['events'] = 'other'; second = self.adapter.state_key()
        self.broker.pairing['profile'] = 'other-profile'; third = self.adapter.state_key()
        self.assertEqual(len({first, second, third}), 3)
    def test_new_device_event_targets_existing_thunderbird_calendar(self):
        operations, conflicts, _ = build_plan({}, {'events:1': device('events')}, {}, self.adapter.new_href)
        self.assertFalse(conflicts)
        href = operations[0]['href']
        self.assertEqual(self.adapter.params(href)['calendarId'], 'selected-calendar')
        self.assertEqual(self.adapter.params(href)['uid'], 'ic35-events-1@local')
    def test_missing_get_cannot_masquerade_as_existing(self):
        self.broker.call.return_value = None
        with self.assertRaises(RuntimeError): self.adapter.check(self.adapter.href('events', 'one'), self.remote)


if __name__ == '__main__': unittest.main()
