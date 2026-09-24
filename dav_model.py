"""Loss-checked IC35 mappings for local CardDAV and CalDAV resources."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import copy
import vobject
import bridge
import ic35_protocol as p
import todo_protocol as todo

DB = {'contacts': 'Addresses', 'events': 'Schedule', 'tasks': 'To Do List'}
FILE_ID = {'contacts': 5, 'events': 8, 'tasks': 7}
# IC35 alarm codes, as used by the existing transport/exporter.
MIN_TO_CODE = {0: 1, 1: 2, 5: 3, 10: 4, 30: 5, 60: 6, 120: 7, 600: 8, 1440: 9, 2880: 10}


def values(kind, record):
    if record.get('error') or record.get('file_id') != FILE_ID[kind]:
        raise ValueError('Ungültiger Gerätedatensatz')
    fields = record.get('fields', {})
    if set(fields) != {name for name, _ in p.FIELD_SPECS[DB[kind]]}:
        raise ValueError('Unvollständiger Gerätedatensatz')
    return {k: v['value'] for k, v in fields.items()}


def record(kind, fields, rid=1):
    return {'record_id': rid, 'file_id': FILE_ID[kind], 'change_flag': 0,
            'fields': {k: {'value': v} for k, v in fields.items()}}


def validate(kind, fields):
    if set(fields) != {name for name, _ in p.FIELD_SPECS[DB[kind]]}:
        raise ValueError('Unvollständige Felder')
    limits = p.ADDRESS_MAX_BYTES if kind == 'contacts' else p.SCHEDULE_MAX_BYTES
    if kind == 'tasks':
        todo.encode(fields)
        return
    for key, value in fields.items():
        if isinstance(value, str):
            if '\x00' in value:
                raise ValueError(f'{key}: Nullzeichen nicht unterstützt')
            raw = value.encode('cp1252', errors='strict')
            if len(raw) > limits.get(key, 255):
                raise ValueError(f'{key}: zu lang für den IC35; keine Kürzung')


def semantic(kind, fields):
    result = {k: (v.replace('\r\n', '\n').replace('\r', '\n') if isinstance(v, str) else v)
              for k, v in fields.items() if k not in ('category', 'category-id', '(def.)1', '(def.)2')}
    if kind == 'events':
        if int(fields.get('AlrmRep') or 0) & 0x0F:
            raise ValueError('Terminserie: in dieser Thunderbird-Alpha noch nicht unterstützt')
        # DCS15 fills this unused date even for non-recurring events.
        if fields.get('EndRepeat'):
            datetime.strptime(fields['EndRepeat'], '%Y%m%d')
        result.pop('AlrmRep', None)
        result.pop('EndRepeat', None)
        result.pop('RepAlln', None)
    if kind == 'tasks':
        if result.get('Start') == '20000101' and result.get('Ende') == '20001231':
            result['Start'] = result['Ende'] = ''
        if result.get('Start') == result.get('Ende'):
            result['Start'] = ''
    return result


def matches_event_written(actual, expected):
    """Accept observed DCS15 defaults only; retain exact checks on meaningful fields."""
    normalized = dict(actual)
    if expected.get('AlrmRep') == 0 and normalized.get('AlrmRep') is None:
        normalized['AlrmRep'] = 0
    if not (int(expected.get('AlrmRep') or 0) & 0x0F) and not expected.get('EndRepeat'):
        value = normalized.get('EndRepeat')
        if value:
            try:
                if len(value) != 8 or datetime.strptime(value, '%Y%m%d').strftime('%Y%m%d') != value:
                    return False
            except (ValueError, TypeError):
                return False
            normalized['EndRepeat'] = ''
    return normalized == expected


def component(doc, kind):
    if kind == 'contacts':
        if doc.name != 'VCARD':
            raise ValueError('Keine vCard')
        return doc
    name = 'vevent' if kind == 'events' else 'vtodo'
    items = doc.contents.get(name, [])
    other = 'vtodo' if kind == 'events' else 'vevent'
    if len(items) != 1 or doc.contents.get(other):
        raise ValueError('Mehrere Kalenderkomponenten/Serienausnahmen werden nicht verändert')
    return items[0]


def text(comp, name, default=''):
    value = comp.contents.get(name, [])
    return value[0].value if value else default


def series_protects(fields, remote, zone, exact=False):
    """Recognize occurrences for exclusion only; never turn a series into a writable item."""
    start = datetime.strptime(fields['Start(Datum)'] + fields['Start(Zeit)'], '%Y%m%d%H%M%S')
    end = datetime.strptime(fields['Ende(Datum)'] + fields['Ende(Zeit)'], '%Y%m%d%H%M%S')
    for resource in remote.values():
        if resource['kind'] != 'events':
            continue
        doc = vobject.readOne(resource['content'])
        events = doc.contents.get('vevent', [])
        for event in events:
            if str(text(event, 'summary')) != fields['Betreff']:
                continue
            recurring = any(event.contents.get(k) for k in ('rrule', 'rdate', 'recurrence-id'))
            if not recurring or str(text(event, 'status')).upper() == 'CANCELLED':
                continue
            first = text(event, 'dtstart', None)
            last = text(event, 'dtend', None)
            if not isinstance(first, datetime):
                continue
            duration = (_wall(last, zone) - _wall(first, zone)) if last else text(event, 'duration', timedelta(0))
            if end - start != duration:
                continue
            if event.contents.get('recurrence-id'):
                if _wall(first, zone) == start:
                    return True
                continue
            # Only expand ordinary day-or-longer rules, bounded to the candidate instant.
            # Unhandled high-frequency rules conservatively protect same-title records.
            if any(not any('FREQ=' + f in str(rule.value).upper() for f in ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'))
                   for rule in event.contents.get('rrule', [])):
                if not exact:
                    return True
                continue
            target = start.replace(tzinfo=ZoneInfo(zone)).astimezone(first.tzinfo) if first.tzinfo else start
            overrides = [x for x in events if text(x, 'uid') == text(event, 'uid') and x.contents.get('recurrence-id')]
            if any(_wall(text(x, 'recurrence-id'), zone) == start for x in overrides):
                continue
            if any(_wall(value, zone) == start for prop in event.contents.get('exdate', [])
                   for value in (prop.value if isinstance(prop.value, list) else [prop.value])):
                continue
            rules = event.getrruleset(addRDate=True)
            if rules and rules.between(target, target, inc=True):
                return True
    return False


def same_entry(left, right):
    """Initial matching only: preserve separate reminder baselines after binding."""
    if left.get('error') or right.get('error') or left['kind'] != right['kind']:
        return False
    a, b = dict(left['semantic']), dict(right['semantic'])
    if left['kind'] == 'events':
        a.pop('AlrmBef', None)
        b.pop('AlrmBef', None)
    return a == b


def duplicate_matches_journal(item, expected):
    """Allow only a provider-added reminder when undoing our own interrupted create."""
    if item.get('error') or not item.get('semantic'):
        return False
    actual = dict(item['semantic'])
    if expected.get('AlrmBef') == 0:
        actual['AlrmBef'] = 0
    if actual != expected:
        return False
    comp = component(vobject.readOne(item['content']), 'events')
    allowed = {'uid', 'summary', 'description', 'dtstart', 'dtend', 'dtstamp', 'created',
               'last-modified', 'status', 'sequence', 'transp', 'valarm'}
    return all(k in allowed or k.startswith(('x-ic35-', 'x-moz-')) for k in comp.contents)


def _wall(value, zone):
    if not isinstance(value, datetime):
        raise ValueError('Ganztägiger Termin: in dieser Alpha noch nicht unterstützt')
    if value.tzinfo:
        value = value.astimezone(ZoneInfo(zone)).replace(tzinfo=None)
    return value


def parse(kind, raw, zone):
    docs = list(vobject.readComponents(raw))
    if len(docs) != 1:
        raise ValueError('Genau eine vCard/ein Kalenderobjekt pro Ressource erforderlich')
    doc = docs[0]
    comp = component(doc, kind)
    if not text(comp, 'uid'):
        raise ValueError('UID fehlt')
    if kind == 'contacts':
        # Reject unrepresentable multiplicity instead of losing data on the device.
        if len(comp.contents.get('email', [])) > 2 or len(comp.contents.get('adr', [])) > 1:
            raise ValueError('Kontakt mit mehr als zwei E-Mails oder mehreren Anschriften')
        for name in ('n', 'fn', 'org', 'url', 'bday', 'note'):
            if len(comp.contents.get(name, [])) > 1:
                raise ValueError('Kontakt: mehrfaches Feld ' + name)
        fields = bridge.contact_semantic_to_ic35_fields({})
        n = text(comp, 'n', None)
        if n is not None:
            if n.additional or n.prefix or n.suffix:
                raise ValueError('Kontakt: Namenszusätze sind auf dem IC35 nicht darstellbar')
            fields['Vorname'], fields['Nachname'] = str(n.given), str(n.family)
        elif text(comp, 'fn'):
            fields['Nachname'] = str(text(comp, 'fn'))
        org = text(comp, 'org', [])
        if len(org) > 1:
            raise ValueError('Kontakt: mehrteilige Organisation nicht unterstützt')
        fields['Firma'] = str(org[0]) if org else ''
        address = text(comp, 'adr', None)
        if address:
            if address.box or address.extended:
                raise ValueError('Kontakt: Postfach/Zusatzanschrift nicht unterstützt')
            for key, attr in [('Strasse', 'street'), ('Ort', 'city'), ('Bundesland', 'region'), ('PLZ', 'code'), ('Land', 'country')]:
                fields[key] = str(getattr(address, attr))
        seen = set()
        for tel in comp.contents.get('tel', []):
            types = {s.upper() for part in tel.params.get('TYPE', []) for s in part.split(',')}
            if types - {'HOME', 'WORK', 'CELL', 'FAX', 'VOICE', 'PREF'}:
                raise ValueError('Kontakt: nicht unterstützter Telefontyp')
            slot = 'Handy' if 'CELL' in types else 'Fax' if 'FAX' in types else 'Tel.Buero' if 'WORK' in types else 'Tel.Privat'
            if slot in seen:
                raise ValueError('Kontakt: mehrere Nummern für ' + slot)
            seen.add(slot)
            value = str(tel.value)
            fields[slot] = value[4:] if value.lower().startswith('tel:') else value
        for index, email in enumerate(comp.contents.get('email', []), 1):
            fields[f'E-Mail{index}'] = str(email.value)
        fields['URL'] = str(text(comp, 'url'))
        birthday = str(text(comp, 'bday'))
        if birthday:
            fields['Geburtstag'] = datetime.strptime(birthday.replace('-', ''), '%Y%m%d').strftime('%Y%m%d')
        fields['Notizen'] = str(text(comp, 'note'))
    else:
        if any(comp.contents.get(k) for k in ('rrule', 'rdate', 'exdate', 'recurrence-id', 'attendee', 'organizer')):
            raise ValueError('Serien, Serienausnahmen und Besprechungseinladungen werden nicht verändert')
        fields = {'Betreff': str(text(comp, 'summary')), 'Notizen': str(text(comp, 'description'))}
        if not fields['Betreff'].strip():
            raise ValueError('Betreff fehlt')
        if kind == 'events':
            start = _wall(text(comp, 'dtstart', None), zone)
            end = text(comp, 'dtend', None)
            if end is None and comp.contents.get('duration'):
                end = start + text(comp, 'duration')
            end = _wall(end, zone)
            if start.second or end.second or start.microsecond or end.microsecond:
                raise ValueError('Termine mit Sekunden werden nicht auf Minuten gekürzt')
            if end < start:
                raise ValueError('Terminende liegt vor Beginn')
            alarms = comp.contents.get('valarm', [])
            code = 0
            if alarms:
                if len(alarms) != 1 or str(text(alarms[0], 'action')).upper() != 'DISPLAY':
                    raise ValueError('Nur eine einfache Anzeige-Erinnerung wird unterstützt')
                trigger = text(alarms[0], 'trigger', None)
                if not isinstance(trigger, timedelta) or trigger.total_seconds() % 60:
                    raise ValueError('Nicht unterstützte Erinnerung')
                if alarms[0].trigger.params.get('RELATED', ['START']) != ['START']:
                    raise ValueError('Erinnerung relativ zum Ende nicht unterstützt')
                minutes = int(-trigger.total_seconds() / 60)
                if minutes not in MIN_TO_CODE:
                    raise ValueError('Erinnerungsabstand auf IC35 nicht darstellbar')
                code = MIN_TO_CODE[minutes]
            fields.update({'Start(Datum)': start.strftime('%Y%m%d'), 'Start(Zeit)': start.strftime('%H%M%S'),
                'Ende(Datum)': end.strftime('%Y%m%d'), 'Ende(Zeit)': end.strftime('%H%M%S'),
                'AlrmBef': code, 'AlrmRep': 0xC0 if not code else 0, 'RepAlln': 0, 'EndRepeat': ''})
        else:
            def day(name):
                value = text(comp, name, None)
                if value is None:
                    return ''
                if isinstance(value, datetime):
                    raise ValueError('Aufgaben mit Uhrzeit werden nicht auf ein Datum gekürzt')
                if not isinstance(value, date):
                    raise ValueError('Ungültiges Aufgabendatum')
                return value.strftime('%Y%m%d')
            status = str(text(comp, 'status', 'NEEDS-ACTION')).upper()
            percent = int(text(comp, 'percent-complete', 0))
            if status not in ('NEEDS-ACTION', 'COMPLETED') or percent not in (0, 100):
                raise ValueError('Aufgabe mit Zwischenstatus nicht unterstützt')
            priority = int(text(comp, 'priority', 0))
            if priority not in (0, 1, 5, 9):
                raise ValueError('Aufgabenpriorität muss normal, hoch oder niedrig sein')
            if comp.contents.get('valarm'):
                raise ValueError('Aufgabenerinnerungen werden nicht verändert')
            fields.update(Start=day('dtstart'), Ende=day('due'), Erledigt=int(status == 'COMPLETED'),
                Prioritaet={0: 1, 1: 2, 5: 1, 9: 0}[priority], **{'category-id': 18, 'category': 'Unfiled'})
    validate(kind, fields)
    return {'fields': fields, 'semantic': semantic(kind, fields), 'uid': str(text(comp, 'uid'))}


def render(kind, fields, uid, original=None):
    rec = record(kind, fields)
    serializer = {'contacts': bridge.contact_to_vcard, 'events': bridge.event_to_ics, 'tasks': bridge.todo_to_ics}[kind]
    fresh = vobject.readOne(serializer(rec, uid))
    new = component(fresh, kind)
    if kind == 'tasks' and fields.get('Start') == '20000101' and fields.get('Ende') == '20001231':
        new.contents.pop('dtstart', None)
        new.contents.pop('due', None)
    if not original:
        return fresh.serialize()
    doc = vobject.readOne(original)
    old = component(doc, kind)
    keys = ('n', 'fn', 'org', 'tel', 'adr', 'email', 'url', 'bday', 'note') if kind == 'contacts' else (
        ('summary', 'description', 'dtstart', 'dtend', 'duration', 'valarm') if kind == 'events' else
        ('summary', 'description', 'dtstart', 'due', 'status', 'completed', 'percent-complete', 'priority'))
    # Preserve UID and properties which have no device equivalent (e.g. LOCATION).
    for key in keys:
        existing = old.contents.get(key, [])
        replacement = new.contents.get(key, [])
        if [str(x.value) for x in existing if hasattr(x, 'value')] == [str(x.value) for x in replacement if hasattr(x, 'value')] and key != 'valarm':
            continue
        old.contents.pop(key, None)
        if key in new.contents:
            old.contents[key] = copy.deepcopy(new.contents[key])
    for key in (('rev',) if kind == 'contacts' else ('dtstamp', 'last-modified')):
        old.contents.pop(key, None)
        now = datetime.now(vobject.icalendar.utc)
        old.add(key).value = now.strftime('%Y%m%dT%H%M%SZ') if kind == 'contacts' else now
    return doc.serialize()
