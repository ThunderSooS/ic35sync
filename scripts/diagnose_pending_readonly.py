"""Read-only targeted diagnosis. Close the sync app, leave Thunderbird running."""
import os
from pathlib import Path
import sys
import time
from urllib.parse import unquote
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import private_storage as storage
from thunderbird_rpc import Broker
from thunderbird_calendar import Calendars
import dav_model as model

root = Path(os.environ['APPDATA']) / 'IC35ThunderbirdAlpha'
journals = list(root.glob('sync_states/*/pending.dpapi'))
if len(journals) != 1:
    raise RuntimeError('Exactly one pending calendar operation required')
op = storage.read_json(journals[0])
parts = op['href'].split('/')
assert len(parts) == 5 and parts[1:3] == ['thunderbird', 'events']
calendar_id = unquote(parts[3])
pairing = storage.read_json(root / 'addon_pairing.dpapi')
assert pairing.get('profile')
broker = Broker(root, pairing=pairing)
try:
    deadline = time.monotonic() + 45
    while not broker.last_seen and time.monotonic() < deadline:
        time.sleep(.25)
    response = broker.call('snapshot', {'calendarId': calendar_id, 'kind': 'events'})
    assert response.get('complete') is True
    class Local:
        zone = 'Europe/Berlin'
    adapter = Calendars(Local(), broker, {'events': calendar_id})
    remote = {adapter.href('events', d['uid']): adapter.item('events', d) for d in response['items']}
    r = remote.get(op['href'])
    print('Snapshot count:', len(remote), 'Target present:', r is not None)
    print('Series match:', model.series_protects(op['device']['fields'], remote, Local.zone, exact=True))
    if r:
        print('Target parse error:', r.get('error'))
        print('UID matches:', r.get('uid') == op['uid'])
        print('Duplicate matches:', model.duplicate_matches_journal(r, op['device']['semantic']))
        print('Semantic differences:', {k: [op['device']['semantic'].get(k), v] for k, v in r.get('semantic', {}).items()
                                        if op['device']['semantic'].get(k) != v})
    output = Path(__file__).resolve().parents[1] / '.integration/pending-diagnostic.dpapi'
    storage.write_json(output, {'journal': op, 'remote': remote})
    print('Protected diagnostic saved; no calendar writes requested.')
finally:
    broker.close()
