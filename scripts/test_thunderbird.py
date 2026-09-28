"""Run actual extension APIs in a disposable Thunderbird profile with synthetic calendars only."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from thunderbird_rpc import Broker
import dav_model as model
import bridge
from dav_sync import DAV

out = ROOT / '.integration' / uuid.uuid4().hex[:8]
profile = out / 'profile'
(profile / 'extensions').mkdir(parents=True)
token = secrets.token_urlsafe(32)
pairing = {'token': token, 'profile': None}
broker = Broker(out, port=0, pairing=pairing)
bridge.ensure_radicale_storage(out / 'dav')
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0)); dav_port = sock.getsockname()[1]
dav_log = (out / 'radicale.log').open('w')
dav_proc = subprocess.Popen([sys.executable, str(ROOT / 'radicale_windows_launcher.py'), '--config', '',
    '--storage-filesystem-folder', str(out / 'dav'), '--storage-type', 'multifilesystem', '--auth-type', 'none',
    '--server-hosts', f'127.0.0.1:{dav_port}'], stdout=dav_log, stderr=dav_log, creationflags=subprocess.CREATE_NO_WINDOW)
direct = DAV(f'http://127.0.0.1:{dav_port}', 'Europe/Berlin')
for _ in range(100):
    try: direct.snapshot(); break
    except OSError: time.sleep(.1)
prefs = {'extensions.autoDisableScopes': 0, 'extensions.enabledScopes': 15, 'extensions.startupScanScopes': 15,
         'extensions.experiments.enabled': True, 'xpinstall.signatures.required': False,
         'mail.shell.checkDefaultClient': False, 'mail.provider.enabled': False,
         'mailnews.start_page.enabled': False, 'app.update.enabled': False,
         'datareporting.policy.dataSubmissionEnabled': False, 'toolkit.telemetry.enabled': False,
         'calendar.alarms.show': False, 'calendar.alarms.playsound': False}
(profile / 'user.js').write_text('\n'.join('user_pref(' + json.dumps(k) + ', ' + json.dumps(v) + ');' for k, v in prefs.items()))

# Fixtures exist only in this disposable test XPI. They are never included in the release.
fixture = """
  if (job.method === 'list' && job.params?.taskLinksTest) {
    const c = globalThis.testGoogle;
    const links = taskLinks(c);
    if (job.params?.native) {
      const { CalTodo } = ChromeUtils.importESModule('resource:///modules/CalTodo.sys.mjs');
      const item = new CalTodo(); item.id = 'server-native'; item.title = 'Created on Google';
      if (job.params.subtask) item.setProperty('RELATED-TO', 'parent-id');
      await c.addItem(item);
    }
    if (job.params?.pending !== undefined) { links.pending = job.params.pending; taskLinks(c, links); }
    return taskLinks(c);
  }
  if (job.method === 'list' && job.params?.selfTest) {
    const make = cached => ({id: 'test-' + Math.random(), type: 'caldav', wrappedJSObject: {isCached: cached},
      observers: new Set(), addObserver(o) { this.observers.add(o); }, removeObserver(o) { this.observers.delete(o); }});
    const never = () => new Promise(() => {});
    const c = make(false);
    let calls = 0;
    await mutate(c, 'one', 'add', () => {
      calls++;
      setTimeout(() => { for (const o of c.observers) o.onAddItem({id: 'one', calendar: c}); }, 10);
      return never();
    }, 1000);
    if (calls !== 1 || c.observers.size || pendingMutations.has(c.id)) throw new Error('lost acknowledgement failed');
    const wrong = make(false);
    try {
      await mutate(wrong, 'one', 'modify', () => {
        for (const o of wrong.observers) o.onModifyItem({id: 'different', calendar: wrong});
        return never();
      }, 40);
      throw new Error('wrong UID accepted');
    } catch(e) { if (!String(e.message).includes('Schreibbestätigung fehlt')) throw e; }
    let retried = false;
    try { await mutate(wrong, 'one', 'modify', () => { retried = true; }, 40); }
    catch(e) { if (!String(e.message).includes('Keine Wiederholung')) throw e; }
    if (retried || wrong.observers.size) throw new Error('write was repeated or observer leaked');
    const cached = make(true);
    try { await mutate(cached, 'one', 'add', never, 40); throw new Error('unconfirmed cached write accepted'); }
    catch(e) { if (!String(e.message).includes('Schreibbestätigung fehlt')) throw e; }
    const rejected = make(false);
    try { await mutate(rejected, 'one', 'add', () => Promise.reject(new Error('test rejected')), 40); }
    catch(e) { if (e.message !== 'test rejected') throw e; }
    if (pendingMutations.has(rejected.id) || rejected.observers.size) throw new Error('rejection leaked');
    pendingMutations.delete(wrong.id); pendingMutations.delete(cached.id);
    return {lostAck: true, wrongUidRejected: true, noRetry: true, cachedNotConfirmed: true};
  }
  if (job.method === '_fixture') {
    const tasks = cal.manager.createCalendar('storage', Services.io.newURI('moz-storage-calendar://'));
    tasks.id = Services.uuid.generateUUID().toString(); tasks.name = 'Synthetic Google Tasks';
    const wrapper = {
      id: tasks.id, name: 'ThunderClub fixture', type: 'ext-{a62ef8ec-5fdc-40c2-873c-223b8a6925cc}',
      readOnly: false, canRefresh: false,
      getProperty(k) { return k === 'capabilities.events.supported' ? false : tasks.getProperty(k); },
      getItem(id) { return tasks.getItem(id); },
      getItems(...args) { return tasks.getItems(...args); },
      async addItem(item) {
        const copy = item.clone(); copy.id = 'google-' + Services.uuid.generateUUID().toString();
        copy.entryDate = null; copy.priority = 0;
        if (copy.dueDate?.isDate) copy.dueDate = cal.createDateTime(copy.dueDate.icalString + 'T000000Z');
        return tasks.addItem(copy);
      },
      modifyItem(item, old) { return tasks.modifyItem(item, old); },
      deleteItem(item) { return tasks.deleteItem(item); },
    };
    globalThis.testGoogle = wrapper;
    const c = cal.manager.createCalendar('storage', Services.io.newURI('moz-storage-calendar://'));
    c.id = Services.uuid.generateUUID().toString().replace(/[{}]/g, '');
    c.name = 'IC35 isolated test'; cal.manager.registerCalendar(c);
    const { CalEvent } = ChromeUtils.importESModule('resource:///modules/CalEvent.sys.mjs');
    const event = new CalEvent(); event.id = 'fixture-one'; event.title = 'Fixture';
    event.startDate = cal.createDateTime('20261001T120000');
    event.endDate = cal.createDateTime('20261001T130000'); event.calendar = c;
    await c.addItem(event);
    const login = Cc['@mozilla.org/login-manager/loginInfo;1'].createInstance(Ci.nsILoginInfo);
    login.init('FIXTURE_ORIGIN', null, 'Radicale - Password Required', 'ic35', 'ic35', '', '');
    await Services.logins.addLoginAsync(login);
    const network = cal.manager.createCalendar('caldav', Services.io.newURI('FIXTURE_URL'));
    network.id = Services.uuid.generateUUID().toString().replace(/[{}]/g, '');
    network.name = 'IC35 isolated CalDAV'; network.setProperty('cache.enabled', true);
    network.setProperty('username', 'ic35');
    network.setProperty('refreshInterval', 0); cal.manager.registerCalendar(network);
    const uncached = cal.manager.createCalendar('caldav', Services.io.newURI('FIXTURE_URL'));
    uncached.id = Services.uuid.generateUUID().toString().replace(/[{}]/g, '');
    uncached.name = 'IC35 uncached CalDAV'; uncached.setProperty('cache.enabled', false);
    uncached.setProperty('username', 'ic35'); uncached.setProperty('refreshInterval', 0);
    cal.manager.registerCalendar(uncached);
    return c.id;
  }
""".replace('FIXTURE_URL', f'http://127.0.0.1:{dav_port}/ic35/calendar/').replace('FIXTURE_ORIGIN', f'http://127.0.0.1:{dav_port}')
with zipfile.ZipFile(profile / 'extensions/ic35-bridge@thundersoos.cc.xpi', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in (ROOT / 'addon').iterdir():
        content = path.read_text(encoding='utf-8')
        if path.name == 'api.js':
            content = content.replace('cal.manager.getCalendars()', '[...cal.manager.getCalendars(), ...(globalThis.testGoogle ? [globalThis.testGoogle] : [])]')
            content = content.replace('async function execute(job, context = {}) {', 'async function execute(job, context = {}) {' + fixture)
            content = content.replace('() => old ? calendar.modifyItem(item, old) : calendar.addItem(item)',
                "() => { const result = old ? calendar.modifyItem(item, old) : calendar.addItem(item); if (args._dropAck) { result.catch(() => {}); return new Promise(() => {}); } return result; }")
        if path.name == 'background.js':
            content = content.replace('http://127.0.0.1:5234', f'http://127.0.0.1:{broker.port}')
            content = content.replace('(async function loop() {', '(async function loop() {\n' +
                'await browser.storage.local.set(' + json.dumps({'token': token, 'profile': 'isolated-test-profile'}) + ');\n' +
                'await browser.ic35Calendar.execute(JSON.stringify({method: "_fixture"}));\n')
        archive.writestr(path.name, content)
env = dict(os.environ, MOZ_HEADLESS='1', MOZ_CRASHREPORTER_DISABLE='1')
log = (out / 'thunderbird.log').open('w', encoding='utf-8')
startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
proc = subprocess.Popen(['C:/Program Files/Mozilla Thunderbird/thunderbird.exe', '-no-remote', '-headless', '-profile', str(profile)],
                        env=env, stdout=log, stderr=log, startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(120):
        if broker.last_seen: break
        if proc.poll() is not None: raise RuntimeError('Thunderbird exited: ' + str(proc.returncode))
        time.sleep(.5)
    else: raise RuntimeError('Add-on did not connect; diagnostic directory: ' + str(out))
    calendars = broker.call('list')
    assert broker.call('list', {'selfTest': True})['noRetry']
    assert broker.call('list')['calendars'], 'list must still work after mutation timeout'
    calendar = next(c for c in calendars['calendars'] if c['name'] == 'IC35 isolated test')
    args = {'calendarId': calendar['id'], 'kind': 'events', 'zone': 'Europe/Berlin'}
    snapshot = broker.call('snapshot', args)
    assert snapshot['complete'] and len(snapshot['items']) == 1, snapshot
    entry = snapshot['items'][0]
    assert entry['uid'] == 'fixture-one'
    f = model.parse('events', entry['content'], 'Europe/Berlin')['fields']
    f['Betreff'] = 'Changed through real Thunderbird API'
    modified = broker.call('write', dict(args, uid=entry['uid'], content=model.render('events', f, entry['uid'], entry['content']), expected=entry['etag']))
    assert model.parse('events', modified['content'], 'Europe/Berlin')['fields']['Betreff'] == f['Betreff']
    try: broker.call('delete', dict(args, uid=entry['uid'], expected=entry['etag']))
    except RuntimeError: pass
    else: raise AssertionError('Stale version was accepted')
    broker.call('delete', dict(args, uid=entry['uid'], expected=modified['etag']))
    assert broker.call('get', dict(args, uid=entry['uid'])) is None
    for kind in ('events', 'tasks'):
        if kind == 'events': fields = f
        else: fields = {'Betreff': 'Task', 'Notizen': '', 'Start': '', 'Ende': '', 'Erledigt': 1, 'Prioritaet': 0, 'category-id': 18, 'category': 'Unfiled'}
        uid = 'new-' + kind
        target = dict(args, kind=kind, uid=uid)
        created = broker.call('write', dict(target, expected=None, content=model.render(kind, fields, uid)))
        assert model.parse(kind, created['content'], 'Europe/Berlin')['semantic'] == model.semantic(kind, fields)
        broker.call('delete', dict(target, expected=created['etag']))
    assert broker.call('snapshot', args)['items'] == []
    network = next(c for c in broker.call('list')['calendars'] if c['name'] == 'IC35 isolated CalDAV')
    target = dict(args, calendarId=network['id'], kind='events', uid='network-test')
    assert broker.call('snapshot', target)['items'] == []
    created = broker.call('write', dict(target, expected=None, content=model.render('events', f, target['uid'])))
    upstream = direct.snapshot()
    assert len(upstream) == 1 and next(iter(upstream.values()))['uid'] == target['uid']
    href = next(iter(upstream))
    changed_fields = dict(f, Betreff='Changed on CalDAV server')
    direct.write(href, model.render('events', changed_fields, target['uid']), upstream[href])
    actual = broker.call('snapshot', target)['items'][0]
    assert model.parse('events', actual['content'], 'Europe/Berlin')['fields']['Betreff'] == changed_fields['Betreff']
    broker.call('delete', dict(target, expected=actual['etag']))
    assert direct.snapshot() == {}
    uncached = next(c for c in broker.call('list')['calendars'] if c['name'] == 'IC35 uncached CalDAV')
    lost = dict(args, calendarId=uncached['id'], kind='events', uid='lost-ack-test', _dropAck=True)
    broker.call('snapshot', lost)
    created_lost = broker.call('write', dict(lost, expected=None, content=model.render('events', f, lost['uid'])))
    assert created_lost['uid'] == lost['uid']
    assert len(direct.snapshot()) == 1
    f_lost = dict(f, Betreff='Lost modify acknowledgement')
    modified_lost = broker.call('write', dict(lost, expected=created_lost['etag'], content=model.render('events', f_lost, lost['uid'])))
    assert model.parse('events', modified_lost['content'], 'Europe/Berlin')['fields']['Betreff'] == f_lost['Betreff']
    broker.call('delete', dict(lost, expected=modified_lost['etag']))
    assert direct.snapshot() == {}
    # End-to-end reconciliation through the production adapter; only the physical IC35 is simulated.
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_sync import FakeDevice, device, export
    from thunderbird_calendar import Calendars
    from dav_sync import Sync
    # Real Thunderbird item/ICS APIs with a simulated Google provider assigning IDs.
    # This does not authenticate to or write to a personal Google account.
    google = next(c for c in broker.call('list')['calendars'] if c['name'] == 'ThunderClub fixture')
    task_device = FakeDevice(); task_device.items['tasks:1'] = device('tasks', 'Stream anniversary')
    task_device.items['tasks:1']['fields']['Ende'] = '20261025'
    task_device.items['tasks:1']['semantic'] = model.semantic('tasks', task_device.items['tasks:1']['fields'])
    task_adapter = Calendars(direct, broker, {'tasks': google['id']})
    task_state = out / 'google-task-state'
    def task_sync():
        return Sync(task_state, 'synthetic-device', task_adapter, task_device, lambda _: None).run(export(task_device.items))
    task_sync()
    task_snapshot = task_adapter.snapshot()
    task_href = next(iter(task_snapshot)); task_remote = task_snapshot[task_href]
    assert task_remote['fields']['Betreff'] == 'Stream anniversary'
    assert task_remote['fields']['Ende'] == '20261025'
    assert task_remote['uid'] == 'ic35-tasks-1@local'
    assert broker.call('list', {'taskLinksTest': True})['ids'][task_remote['uid']].startswith('google-')
    task_sync(); assert len(task_adapter.snapshot()) == 1
    changed = dict(task_remote['fields'], Betreff='Edited in Thunderbird', Erledigt=1)
    task_adapter.write(task_href, model.render('tasks', changed, task_remote['uid']), task_remote)
    task_sync()
    assert task_device.items['tasks:1']['fields']['Erledigt'] == 1
    assert task_device.items['tasks:1']['fields']['Betreff'] == 'Edited in Thunderbird'
    d = task_device.items['tasks:1']; d['fields']['Erledigt'] = 0
    d['semantic'] = model.semantic('tasks', d['fields'])
    task_sync(); assert task_adapter.snapshot()[task_href]['fields']['Erledigt'] == 0
    task_device.items.clear(); task_sync(); assert task_adapter.snapshot() == {}
    task_device.items['tasks:2'] = device('tasks', 'Delete from Thunderbird', rid=2)
    task_sync(); snap = task_adapter.snapshot(); h = next(iter(snap))
    task_adapter.delete(h, snap[h]); task_sync(); assert task_device.items == {}
    broker.call('list', {'taskLinksTest': True, 'pending': {'uid': 'uncertain-create'}})
    try: task_adapter.snapshot()
    except RuntimeError as exc: assert 'ID nicht bestätigt' in str(exc)
    else: raise AssertionError('Uncertain create must block synchronization')
    broker.call('list', {'taskLinksTest': True, 'pending': None})
    broker.call('list', {'taskLinksTest': True, 'native': True})
    task_sync(); assert next(iter(task_device.items.values()))['fields']['Betreff'] == 'Created on Google'
    broker.call('list', {'taskLinksTest': True, 'native': True, 'subtask': True})
    try: task_adapter.snapshot()
    except RuntimeError as exc: assert 'Unteraufgaben' in str(exc)
    else: raise AssertionError('Task hierarchy must be blocked')
    simulated = FakeDevice(); simulated.items['events:1'] = device('events', 'From simulated IC35')
    adapter = Calendars(direct, broker, {'events': network['id']})
    state_dir = out / 'sync-state'
    Sync(state_dir, 'synthetic-device', adapter, simulated, lambda _: None).run(export(simulated.items))
    upstream = direct.snapshot(); href = next(iter(upstream))
    assert upstream[href]['fields']['Betreff'] == 'From simulated IC35'
    new_fields = dict(upstream[href]['fields'], Betreff='Back from server')
    direct.write(href, model.render('events', new_fields, upstream[href]['uid']), upstream[href])
    Sync(state_dir, 'synthetic-device', adapter, simulated, lambda _: None).run(export(simulated.items))
    assert simulated.items['events:1']['fields']['Betreff'] == 'Back from server'
    simulated.items.clear()
    Sync(state_dir, 'synthetic-device', adapter, simulated, lambda _: None).run(export(simulated.items))
    assert direct.snapshot() == {}
    dav_proc.terminate(); dav_proc.wait(timeout=10)
    try: broker.call('snapshot', target)
    except RuntimeError: pass
    else: raise AssertionError('Unavailable CalDAV must not be accepted as an empty calendar')
    result = {'Google_Tasks_simulated_provider_real_Thunderbird_bidirectional_completion_deletion': 'ok', 'Thunderbird': calendars['version'], 'real_addon_RPC': 'ok', 'read_create_update_delete': 'ok',
              'uncached_CalDAV_lost_create_modify_ack': 'ok', 'timeout_still_allows_list_and_blocks_retry': 'ok',
              'real_cached_CalDAV_upstream_and_downstream': 'ok', 'unavailable_CalDAV_stops': True,
              'stale_version_rejected': True, 'test_profile_only': True, 'full_sync_simulated_IC35_real_Thunderbird_CalDAV': 'ok'}
    (ROOT / 'thunderbird-test-results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
finally:
    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    proc.wait(timeout=15)
    dav_proc.terminate(); dav_proc.wait(timeout=10); dav_log.close()
    broker.close(); log.close()
    print('Diagnostic directory:', out)
