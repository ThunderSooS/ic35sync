/* GPL-2.0. Uses Thunderbird calendar APIs; never reads account credentials. */
var { cal } = ChromeUtils.importESModule('resource:///modules/calendar/calUtils.sys.mjs');
var { CalIcsParser } = ChromeUtils.importESModule('resource:///modules/CalIcsParser.sys.mjs');
var { CalIcsSerializer } = ChromeUtils.importESModule('resource:///modules/CalIcsSerializer.sys.mjs');
var { setTimeout, clearTimeout } = ChromeUtils.importESModule('resource://gre/modules/Timer.sys.mjs');

function bounded(promise, milliseconds, message) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(message)), milliseconds);
  })]).finally(() => clearTimeout(timer));
}

// A timeout is not cancellation. Keep uncertain writes locked until their
// original promise or a confirmed uncached-provider notification completes.
const pendingMutations = new Map();
async function mutate(calendar, uid, operation, invoke, timeoutMs = 60000) {
  if (pendingMutations.has(calendar.id)) {
    throw new Error('Ein früherer Kalender-Schreibvorgang ist noch unbestätigt. Keine Wiederholung. Thunderbird neu starten und den gespeicherten Stand prüfen lassen.');
  }
  const marker = {};
  pendingMutations.set(calendar.id, marker);
  const unlock = () => { if (pendingMutations.get(calendar.id) === marker) pendingMutations.delete(calendar.id); };
  let observer;
  let finished = false;
  let timer;
  const remove = () => { if (observer) { calendar.removeObserver(observer); observer = null; } };
  const confirmation = new Promise((resolve, reject) => {
    const finish = (error, value) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer); remove();
      error ? reject(error) : resolve(value);
    };
    // Cached providers can notify before uploading. Only use provider events
    // as an acknowledgement for CalDAV with its offline cache disabled.
    if (calendar.type === 'caldav' && calendar.wrappedJSObject?.isCached === false) {
      const received = item => {
        if (item?.id === uid && item.calendar?.id === calendar.id) {
          unlock(); finish(null, item);
        }
      };
      observer = {
        QueryInterface: ChromeUtils.generateQI(['calIObserver']),
        onAddItem(item) { if (operation !== 'delete') received(item); },
        onModifyItem(item) { if (operation !== 'delete') received(item); },
        onDeleteItem(item) { if (operation === 'delete') received(item); },
        onLoad() {}, onError() {}, onStartBatch() {}, onEndBatch() {},
        onPropertyChanged() {}, onPropertyDeleting() {},
      };
      calendar.addObserver(observer);
    }
    timer = setTimeout(() => finish(new Error('Kalender-Schreibbestätigung fehlt. Der Termin kann bereits angekommen sein. Kein weiterer Schreibversuch; der gespeicherte Vorgang bleibt zur Prüfung erhalten.')), timeoutMs);
    try {
      Promise.resolve(invoke()).then(value => { unlock(); finish(null, value); },
                                    error => { unlock(); finish(error); });
    } catch (error) { unlock(); finish(error); }
  });
  try { return await confirmation; }
  finally { remove(); }
}

function googleTasks(calendar) {
  return ['gdata', 'ext-{a62ef8ec-5fdc-40c2-873c-223b8a6925cc}'].includes(calendar.type);
}

// Persist server-assigned task IDs before acknowledging a create to Python.
// An interrupted create without a confirmed ID must never be retried blindly.
function taskLinks(calendar, value) {
  const key = 'extensions.ic35.taskLinks.' + encodeURIComponent(calendar.id);
  if (value !== undefined) {
    Services.prefs.setStringPref(key, JSON.stringify(value));
    Services.prefs.savePrefFile(null);
  }
  return JSON.parse(Services.prefs.getStringPref(key, '{"ids":{},"pending":null}'));
}

function taskPacked(calendar, item) {
  if (!googleTasks(calendar)) return packed(item);
  const links = taskLinks(calendar);
  const copy = item.clone();
  const alias = Object.keys(links.ids).find(id => links.ids[id] === item.id);
  if (alias) copy.id = alias;
  // Google Tasks stores a date in a UTC timestamp; do not shift it to local time.
  if (copy.dueDate) {
    const date = copy.dueDate.clone();
    date.isDate = true;
    copy.dueDate = date;
  }
  // Normalizing a clone marks it dirty in Thunderbird and can update timestamps.
  // Compare the untouched provider item, never the generated transport clone.
  return {...packed(copy), etag: packed(item).etag};
}

function describe(calendar) {
  return {id: calendar.id, name: calendar.name, type: calendar.type,
    readOnly: calendar.readOnly, disabled: !!calendar.getProperty('disabled'),
    events: calendar.getProperty('capabilities.events.supported') !== false,
    tasks: calendar.getProperty('capabilities.tasks.supported') !== false};
}

function selected(args) {
  const calendar = cal.manager.getCalendars().find(c => c.id === args.calendarId);
  if (!calendar) throw new Error('Ausgewählter Kalender fehlt. Keine Daten geändert.');
  if (!['events', 'tasks'].includes(args.kind)) throw new Error('Unbekannter Datentyp');
  const info = describe(calendar);
  if (info.disabled || info.readOnly || !info[args.kind]) throw new Error('Kalender ist deaktiviert, schreibgeschützt oder unterstützt diesen Datentyp nicht.');
  if (!['storage', 'caldav'].includes(calendar.type) && !(googleTasks(calendar) && args.kind === 'tasks')) throw new Error('Dieser Kalenderanbieter wird für den gewählten Datentyp nicht unterstützt.');
  if (googleTasks(calendar) && taskLinks(calendar).pending) throw new Error('Google-Aufgabe wurde möglicherweise angelegt, aber ihre ID nicht bestätigt. Abgleich gesperrt, um doppelte Aufgaben zu verhindern. Bitte den letzten Vorgang prüfen lassen.');
  if (Services.io.offline && calendar.type !== 'storage') throw new Error('Thunderbird ist offline. Bitte zuerst den Kalender synchronisieren.');
  const status = calendar.getProperty('currentStatus');
  if (status && !Components.isSuccessCode(status)) throw new Error('Thunderbird meldet einen Kalenderfehler. Bitte zuerst dort synchronisieren.');
  return calendar;
}

async function noPending(calendar) {
  const cached = calendar.wrappedJSObject?.mCachedCalendar;
  if (!cached) return;
  for (const flag of ['ITEM_FILTER_OFFLINE_CREATED', 'ITEM_FILTER_OFFLINE_MODIFIED', 'ITEM_FILTER_OFFLINE_DELETED']) {
    for await (const batch of cal.iterate.streamValues(cached.getItems(Ci.calICalendar.ITEM_FILTER_ALL_ITEMS | Ci.calICalendar[flag], 0, null, null))) {
      if (batch.length) throw new Error('Thunderbird hat noch nicht übertragene Kalenderänderungen. Zuerst online synchronisieren, dann IC35 erneut abgleichen.');
    }
  }
}

async function refresh(calendar) {
  if (calendar.type === 'storage' || !calendar.canRefresh) return;
  await new Promise((resolve, reject) => {
    let timer;
    const finish = error => {
      clearTimeout(timer);
      calendar.removeObserver(observer);
      error ? reject(error) : resolve();
    };
    const observer = {
      QueryInterface: ChromeUtils.generateQI(['calIObserver']),
      onLoad() { finish(); },
      onError() { finish(new Error('Thunderbird konnte den Kalender nicht aktualisieren.')); },
      onStartBatch() {}, onEndBatch() {}, onAddItem() {}, onModifyItem() {}, onDeleteItem() {},
      onPropertyChanged() {}, onPropertyDeleting() {},
    };
    calendar.addObserver(observer);
    timer = setTimeout(() => finish(new Error('Kalender-Aktualisierung dauert zu lange. Abgleich gestoppt.')), 75000);
    try { Promise.resolve(calendar.refresh()).catch(finish); } catch (e) { finish(e); }
  });
  await noPending(calendar);
  const status = calendar.getProperty('currentStatus');
  if (status && !Components.isSuccessCode(status)) throw new Error('Kalender-Aktualisierung fehlgeschlagen.');
}

function packed(item) {
  const serializer = new CalIcsSerializer();
  serializer.addItems([item]);
  const content = serializer.serializeToString();
  const stream = Cc['@mozilla.org/io/string-input-stream;1'].createInstance(Ci.nsIStringInputStream);
  stream.setUTF8Data(content);
  const hash = Cc['@mozilla.org/security/hash;1'].createInstance(Ci.nsICryptoHash);
  hash.init(hash.SHA256);
  hash.updateFromStream(stream, -1);
  return {uid: item.id, content, etag: hash.finish(true)};
}

function assertKind(item, kind) {
  if (item && ((kind === 'events') !== item.isEvent())) throw new Error('UID gehört zu anderem Datentyp.');
}

function ordinary(item) {
  if (item.recurrenceInfo || item.recurrenceId || item.organizer || item.getAttendees().length) {
    throw new Error('Serien und Besprechungseinladungen werden nicht verändert.');
  }
}

async function execute(job, context = {}) {
  if (job.method === 'list') return {version: Services.appinfo.version, calendars: cal.manager.getCalendars().map(describe)};
  if (!['snapshot', 'get', 'write', 'delete'].includes(job.method)) throw new Error('Unbekannter Befehl');
  const args = job.params;
  const calendar = selected(args);
  if (job.method === 'snapshot') {
    await refresh(calendar);
    await noPending(calendar);
    const filter = args.kind === 'events' ? Ci.calICalendar.ITEM_FILTER_TYPE_EVENT :
      Ci.calICalendar.ITEM_FILTER_TYPE_TODO | Ci.calICalendar.ITEM_FILTER_COMPLETED_ALL;
    const items = [];
    for await (const batch of cal.iterate.streamValues(calendar.getItems(filter, 0, null, null))) {
      for (const item of batch) {
        assertKind(item, args.kind);
        if (googleTasks(calendar) && item.getProperty('RELATED-TO')) throw new Error('Google-Aufgabenliste enthält Unteraufgaben. Hierarchien werden zum Schutz vor kaskadierenden Löschungen noch nicht synchronisiert.');
        items.push(taskPacked(calendar, item));
      }
    }
    return {complete: true, items};
  }
  if (typeof args.uid !== 'string' || !args.uid) throw new Error('UID fehlt');
  await noPending(calendar);
  const links = googleTasks(calendar) ? taskLinks(calendar) : null;
  const serverUid = links?.ids[args.uid] || args.uid;
  const old = await calendar.getItem(serverUid);
  assertKind(old, args.kind);
  if (job.method === 'get') return old ? taskPacked(calendar, old) : null;
  if ((old ? taskPacked(calendar, old).etag : null) !== args.expected) throw new Error('Eintrag wurde seit der Planung verändert. Bitte erneut synchronisieren.');
  if (old) ordinary(old);
  if (job.method === 'delete') {
    if (!old) throw new Error('Zu löschender Eintrag fehlt');
    if (context.expired) throw new Error('Auftrag bereits abgelaufen; keine neue Änderung gestartet.');
    await mutate(calendar, args.uid, 'delete', () => calendar.deleteItem(old));
    await noPending(calendar);
    if (await calendar.getItem(serverUid)) throw new Error('Löschung wurde nicht bestätigt');
    return null;
  }
  const parser = new CalIcsParser();
  parser.parseString(args.content);
  const items = parser.getItems();
  if (items.length !== 1 || parser.getParentlessItems().length) throw new Error('Genau ein Einzeltermin/eine Aufgabe erforderlich');
  const item = items[0];
  assertKind(item, args.kind); ordinary(item);
  if (item.id !== args.uid) throw new Error('UID darf nicht geändert werden');
  if (links) {
    if (item.priority && ![0, 5].includes(item.priority)) throw new Error('Google Tasks unterstützt keine hohe/niedrige Priorität. Aufgabe auf dem IC35 zuerst auf normale Priorität setzen.');
    if (item.entryDate && (!item.dueDate || item.entryDate.icalString !== item.dueDate.icalString)) throw new Error('Google Tasks unterstützt kein separates Startdatum. Startdatum dieser IC35-Aufgabe entfernen oder dem Fälligkeitsdatum angleichen.');
    item.entryDate = null;
    item.id = serverUid;
  }
  item.calendar = calendar;
  if (old) item.generation = old.generation;
  // IC35 stores local wall time. Make the intended zone explicit for CalDAV.
  const zone = cal.timezoneService.getTimezone(args.zone);
  if (!zone) throw new Error('Unbekannte IC35-Zeitzone');
  if (item.isEvent()) {
    for (const key of ['startDate', 'endDate']) {
      if (item[key] && !item[key].isDate && item[key].timezone.isFloating) {
        const value = item[key].clone(); value.timezone = zone; item[key] = value;
      }
    }
  }
  if (context.expired) throw new Error('Auftrag bereits abgelaufen; keine neue Änderung gestartet.');
  if (links && !old) { links.pending = {uid: args.uid, title: item.title}; taskLinks(calendar, links); }
  const written = await mutate(calendar, serverUid, old ? 'modify' : 'add', () => old ? calendar.modifyItem(item, old) : calendar.addItem(item));
  if (links && !old) {
    if (!written?.id) throw new Error('Google hat keine Aufgaben-ID bestätigt. Kein automatischer Wiederholungsversuch.');
    links.ids[args.uid] = written.id;
    links.pending = null;
    taskLinks(calendar, links);
  }
  await noPending(calendar);
  const actual = await calendar.getItem(links?.ids[args.uid] || args.uid);
  if (!actual) throw new Error('Schreiben wurde nicht bestätigt');
  return taskPacked(calendar, actual);
}

var ic35Calendar = class extends ExtensionCommon.ExtensionAPI {
  getAPI() {
    return {ic35Calendar: {async execute(command) {
      const context = {expired: false};
      try { return JSON.stringify({ok: true, data: await bounded(execute(JSON.parse(command), context), 85000,
        'Thunderbird-Auftrag dauert zu lange. Verbindung bleibt verfügbar; vor weiteren Änderungen wird der gespeicherte Stand geprüft.')}); }
      catch (e) { return JSON.stringify({ok: false, error: String(e.message || e)}); }
      finally { context.expired = true; }
    }}};
  }
};
