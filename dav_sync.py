"""Local three-way reconciliation with ETags, readback and durable recovery journal."""
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET
import bridge
import dav_model as model
import ic35_protocol as p
import todo_protocol as todo
import private_storage as storage


def device_snapshot(export):
    result = {}
    for kind, dbname in model.DB.items():
        db = export.get('databases', {}).get(dbname)
        if not db or db.get('error') or db.get('count') != len(db.get('records', [])):
            raise ValueError(f'{dbname}: unvollständig; kein Abgleich')
        for rec in db['records']:
            if rec.get('deleted'):
                continue
            fields = model.values(kind, rec)
            rid = int(rec['record_id'])
            key = f'{kind}:{rid}'
            if rid <= 0 or key in result:
                raise ValueError('Ungültige/doppelte Geräte-ID')
            item = {'kind': kind, 'rid': rid, 'fields': fields}
            try:
                model.validate(kind, fields)
                item['semantic'] = model.semantic(kind, fields)
            except (ValueError, UnicodeError) as exc:
                item['error'] = str(exc)
            result[key] = item
    return result


class DAV:
    def __init__(self, base, zone):
        if urlparse(base).hostname != '127.0.0.1':
            raise ValueError('Diese Ausgabe unterstützt nur den lokalen Thunderbird-Dienst')
        self.base, self.zone = base.rstrip('/'), zone

    def request(self, href, method, body=None, headers=None):
        if not href.startswith('/ic35/') or '..' in unquote(href).split('/') or urlparse(href).netloc:
            raise ValueError('Unzulässiger DAV-Pfad')
        return bridge._dav_request(self.base + href, method, body,
            content_type=('application/xml; charset=utf-8' if method == 'PROPFIND' else
                          'text/vcard; charset=utf-8' if href.endswith('.vcf') else 'text/calendar; charset=utf-8'), headers=headers)

    def snapshot(self):
        result = {}
        for collection in ('addressbook', 'calendar'):
            parent = f'/ic35/{collection}/'
            status, _, payload = self.request(parent, 'PROPFIND',
                '<D:propfind xmlns:D="DAV:"><D:prop><D:getetag/><D:resourcetype/></D:prop></D:propfind>', {'Depth': '1'})
            if status != 207:
                raise RuntimeError(f'DAV-Sammlung nicht vollständig lesbar: HTTP {status}')
            root = ET.fromstring(payload)
            for response in root.findall('{DAV:}response'):
                href = urlparse(response.findtext('{DAV:}href', '')).path
                if href.rstrip('/') == parent.rstrip('/'):
                    continue
                if not href.startswith(parent) or '/' in href[len(parent):]:
                    raise ValueError('Unerwartete DAV-Unterressource')
                if href in result:
                    raise ValueError('Doppelte DAV-Ressource')
                code, headers, raw = self.request(href, 'GET')
                etag = next((v for k, v in headers.items() if k.lower() == 'etag'), None)
                if code != 200 or not etag:
                    raise RuntimeError('DAV-Ressource beim Lesen verändert oder ETag fehlt')
                content = raw.decode('utf-8-sig')
                if collection == 'addressbook':
                    kind = 'contacts'
                else:
                    kinds = [k for k, tag in [('events', 'BEGIN:VEVENT'), ('tasks', 'BEGIN:VTODO')] if tag in content.upper()]
                    if len(kinds) != 1:
                        raise ValueError('Nicht eindeutig zuordenbare Kalenderressource')
                    kind = kinds[0]
                item = {'kind': kind, 'content': content, 'etag': etag}
                try:
                    item.update(model.parse(kind, content, self.zone))
                except Exception as exc:
                    item['error'] = str(exc)
                result[href] = item
        return result

    def check(self, href, expected):
        code, headers, _ = self.request(href, 'GET')
        if expected is None:
            if code != 404:
                raise RuntimeError('Neues DAV-Ziel existiert inzwischen; Abbruch')
        elif code != 200 or next((v for k, v in headers.items() if k.lower() == 'etag'), None) != expected['etag']:
            raise RuntimeError('Thunderbird hat den Eintrag während des Abgleichs verändert; erneut synchronisieren')

    def write(self, href, content, before):
        headers = {'If-Match': before['etag']} if before else {'If-None-Match': '*'}
        code, _, _ = self.request(href, 'PUT', content, headers)
        if code not in (200, 201, 204):
            raise RuntimeError(f'DAV-Schreiben abgebrochen: HTTP {code}')

    def delete(self, href, before):
        code, _, _ = self.request(href, 'DELETE', headers={'If-Match': before['etag']})
        if code not in (200, 204):
            raise RuntimeError(f'DAV-Löschen abgebrochen: HTTP {code}')


def confirmed_write(device, remote, uid, creating):
    if not remote or remote.get('error') or remote.get('uid') != uid:
        return False
    if remote.get('semantic') == device['semantic']:
        return True
    # Some providers apply their default reminder to a newly created event.
    # Only accept this on CREATE; an explicit later reminder edit stays strict.
    return bool(creating and device['kind'] == 'events' and
                model.duplicate_matches_journal(remote, device['semantic']))


def build_plan(bindings, device, remote, href_factory=None, zone='Europe/Berlin'):
    operations, conflicts, skipped = [], [], []
    used_d, used_r = set(), set()
    protected = {key for key, d in device.items() if d['kind'] == 'events' and not d.get('error')
                 and model.series_protects(d['fields'], remote, zone)}
    for key in protected:
        used_d.add(key)
        if key in bindings:
            used_r.add(bindings[key]['href'])
        skipped.append(key + ': vorhandener Serientermin; keine Einzelkopie und keine Änderung')
    def add(action, key, href):
        operations.append({'action': action, 'key': key, 'href': href,
                           'device': device.get(key), 'remote': remote.get(href)})
    for key, binding in bindings.items():
        if key in protected:
            continue
        href = binding['href']
        if href in used_r:
            raise ValueError('Doppelte Zuordnung im State')
        used_d.add(key); used_r.add(href)
        d, r = device.get(key), remote.get(href)
        if (d and d.get('error')) or (r and r.get('error')):
            skipped.append(key + ': ' + str((d or {}).get('error') or (r or {}).get('error')))
            continue
        if r and (r['uid'] != binding['uid'] or (d and d['kind'] != r['kind'])):
            conflicts.append(key + ': Ressource/UID wurde ersetzt')
        elif not d and not r:
            add('forget', key, href)
        elif not d:
            if r['semantic'] == binding['remote'] and r.get('content') == binding.get('remote_content', r.get('content')):
                add('delete_remote', key, href)
            else:
                conflicts.append(key + ': Gerät gelöscht, Thunderbird geändert')
        elif not r:
            if d['semantic'] == binding['device'] and d['fields'] == binding.get('device_fields', d['fields']):
                add('delete_device', key, href)
            else:
                conflicts.append(key + ': Thunderbird gelöscht, Gerät geändert')
        elif d['semantic'] == r['semantic']:
            add('bind', key, href)
        else:
            dc, rc = d['semantic'] != binding['device'], r['semantic'] != binding['remote']
            if dc and rc:
                conflicts.append(key + ': auf beiden Seiten geändert')
            elif dc:
                add('write_remote', key, href)
            elif rc:
                add('write_device', key, href)
            # Unchanged but different representations retain their baseline.
    for key, d in device.items():
        if key in used_d:
            continue
        if d.get('error'):
            skipped.append(key + ': ' + d['error']); continue
        candidates = [h for h, r in remote.items() if h not in used_r and not r.get('error')
                      and model.same_entry(r, d)]
        same_devices = [k for k, other in device.items() if k not in used_d and not other.get('error')
                        and model.same_entry(other, d)]
        if candidates and (len(candidates) != 1 or len(same_devices) != 1):
            conflicts.append(key + ': mehrdeutige Dublette'); continue
        if candidates:
            href = candidates[0]
            used_r.add(href)
            add('bind', key, href)
        else:
            collection = 'addressbook' if d['kind'] == 'contacts' else 'calendar'
            suffix = 'vcf' if d['kind'] == 'contacts' else 'ics'
            href = f'/ic35/{collection}/ic35-{d["kind"]}-{d["rid"]}.{suffix}'
            if href_factory:
                href = href_factory(d['kind'], d['rid'])
            if href in remote:
                conflicts.append(key + ': Zielname bereits belegt')
            else:
                add('write_remote', key, href)
        used_d.add(key)
    for href, r in remote.items():
        if href in used_r:
            continue
        if r.get('error'):
            skipped.append(href + ': ' + r['error']); continue
        if r['kind'] == 'events' and model.series_protects(r['fields'], remote, zone):
            skipped.append(href + ': Einzeltermin überschneidet sich mit Serie; manuell prüfen'); continue
        add('write_device', None, href)
    return operations, conflicts, skipped


class Device:
    def __init__(self, ser):
        self.ser = ser

    def read(self, kind, rid, fd):
        raw = p.read_record_raw_by_id(self.ser, model.DB[kind], fd, rid)
        if raw is None:
            raise RuntimeError('Geräteressource nicht lesbar')
        return p.decode_record(model.DB[kind], raw, -1)

    def confirm(self, op):
        """Recheck the source before changing the remote side, including absence."""
        kind = (op['device'] or op['remote'])['kind']
        fd = p.open_database(self.ser, model.DB[kind])
        if fd is None:
            raise RuntimeError('Gerätedatenbank nicht geöffnet')
        try:
            before = op['device']
            if before:
                if model.values(kind, self.read(kind, before['rid'], fd)) != before['fields']:
                    raise RuntimeError('Gerätedatensatz seit der Planung verändert')
            else:
                rid = int(op['key'].split(':')[1])
                count = p.read_database_count(self.ser, model.DB[kind], fd)
                if count is None:
                    raise RuntimeError('Geräteanzahl nicht lesbar')
                for index in range(count):
                    raw = p.read_record_raw_by_index(self.ser, model.DB[kind], fd, index)
                    if raw is None:
                        raise RuntimeError('Geräte-Löschung nicht vollständig prüfbar')
                    rec = p.decode_record(model.DB[kind], raw, index)
                    model.values(kind, rec)
                    if rec['record_id'] == rid:
                        raise RuntimeError('Gelöschter Geräteeintrag ist wieder vorhanden')
        finally:
            p.close_database(self.ser, model.DB[kind], fd)

    def execute(self, op):
        kind = (op['device'] or op['remote'])['kind']
        before = op['device']
        fd = p.open_database(self.ser, model.DB[kind])
        if fd is None:
            raise RuntimeError('Gerätedatenbank nicht geöffnet')
        try:
            if before:
                live = model.values(kind, self.read(kind, before['rid'], fd))
                if live != before['fields']:
                    raise RuntimeError('Gerätedatensatz wurde seit der Planung verändert')
            if op['action'] == 'delete_device':
                rid = before['rid']
                if kind == 'tasks':
                    todo.delete(self.ser, fd, rid)
                else:
                    count = p.read_database_count(self.ser, model.DB[kind], fd)
                    if count is None:
                        raise RuntimeError('Geräteanzahl nicht lesbar')
                    delete = p.delete_address_record if kind == 'contacts' else p.delete_schedule_record
                    verify = p.verify_address_record_absent if kind == 'contacts' else p.verify_schedule_record_absent
                    delete(self.ser, fd, rid)
                    verify(self.ser, fd, rid, expected_count=count - 1)
                return None
            fields = dict(op['remote']['fields'])
            if before:
                for key in ('category-id', 'category', '(def.)1', '(def.)2'):
                    if key in before['fields']:
                        fields[key] = before['fields'][key]
            model.validate(kind, fields)
            if kind == 'tasks':
                rec = todo.write(self.ser, fd, fields, before['rid'] if before else None)
            else:
                create = p.write_new_address_record if kind == 'contacts' else p.write_new_schedule_record
                update = p.update_address_record if kind == 'contacts' else p.update_schedule_record
                rid, _ = update(self.ser, fd, before['rid'], fields) if before else create(self.ser, fd, fields)
                if before and rid != before['rid']:
                    raise RuntimeError('Geräte-ID nach Update verändert')
                rec = self.read(kind, rid, fd)
                readback = model.values(kind, rec)
                matches = model.matches_event_written(readback, fields) if kind == 'events' else readback == fields
                if not matches:
                    raise RuntimeError('Geräte-Kontrolllesen stimmt nicht überein')
            actual = model.values(kind, rec)
            return {'kind': kind, 'rid': int(rec['record_id']), 'fields': actual,
                    'semantic': model.semantic(kind, actual)}
        finally:
            p.close_database(self.ser, model.DB[kind], fd)


class Sync:
    def __init__(self, root, identity, dav, device, logger=print):
        self.root, self.dav, self.device, self.log = Path(root), dav, device, logger
        self.state_path = self.root / 'thunderbird_state.dpapi'
        self.pending_path = self.root / 'pending.dpapi'
        self.state = storage.read_json(self.state_path) if self.state_path.exists() else {
            'version': 1, 'identity': identity, 'zone': dav.zone, 'bindings': {}}
        if self.state.get('version') != 1 or self.state.get('identity') != identity or self.state.get('zone') != dav.zone:
            raise ValueError('State gehört zu anderem Gerät oder anderer Zeitzone')

    def save_binding(self, key, d, r, href, opid):
        if d is None or r is None:
            self.state['bindings'].pop(key, None)
        else:
            self.state['bindings'][key] = {'href': href, 'device': d['semantic'],
                'remote': r['semantic'], 'uid': r['uid'], 'remote_content': r['content'], 'device_fields': d['fields']}
        self.state['last_operation'] = opid
        storage.write_json(self.state_path, self.state)

    def recover(self, device, remote):
        if not self.pending_path.exists():
            return
        op = storage.read_json(self.pending_path)
        if self.state.get('last_operation') == op['id']:
            self.pending_path.unlink(); return
        key, href, action = op['key'], op['href'], op['action']
        d, r = device.get(key), remote.get(href)
        originals = [h for h, other in remote.items() if h != href and d
                     and not other.get('error') and model.same_entry(other, d)]
        has_original = bool(d and d['kind'] == 'events' and
                            (len(originals) == 1 or model.series_protects(d['fields'], remote, self.dav.zone, exact=True)))
        if action == 'rollback_duplicate' or (action == 'write_remote' and op['remote'] is None
                and d and d['kind'] == 'events' and d == op['device'] and r
                and op.get('uid') == f'ic35-events-{d["rid"]}@local'
                and r.get('uid') == op['uid']
                and has_original and model.duplicate_matches_journal(r, d['semantic'])):
            if d != op['device'] or not has_original or (r and not model.duplicate_matches_journal(r, d['semantic'])):
                raise RuntimeError('Dublettenprüfung: Original fehlt oder Inhalt verändert; keine Löschung')
            if action != 'rollback_duplicate':
                storage.write_json(self.root / 'backups' / (op['id'] + '-duplicate.dpapi'),
                                   {'journal': op, 'duplicate': r, 'remote': remote})
                op = dict(op, action='rollback_duplicate', duplicate=r)
                storage.write_json(self.pending_path, op)
            if r is not None:
                if r != op['duplicate']:
                    raise RuntimeError('Einzelkopie inzwischen geändert; keine automatische Löschung')
                self.device.confirm(op)
                self.dav.check(href, r)
                self.log('Entferne bestätigte Einzelkopie aus unterbrochenem Vorgang; vorhandenes Original bleibt erhalten …')
                self.dav.delete(href, r)
                self.dav.check(href, None)
                remote.pop(href, None)
            self.pending_path.unlink()
            self.log('Einzelkopie bereinigt; IC35-Termin wird dem vorhandenen Original zugeordnet oder als Serienvorkommen geschützt.')
            return
        if action == 'write_device':
            target = op['remote']['semantic']
            if key is None:
                matches = [(k, x) for k, x in device.items() if k not in op['before_ids']
                           and x['kind'] == op['remote']['kind'] and x.get('semantic') == target]
                if len(matches) == 1:
                    key, d = matches[0]
            if d and d.get('semantic') == target and r and r.get('semantic') == target:
                self.save_binding(key, d, r, href, op['id'])
            elif (d == op['device'] and r == op['remote'] and
                  (op['key'] is not None or set(device) == set(op['before_ids']))):
                pass
            else:
                raise RuntimeError('Unterbrochener Geräteschreibvorgang nicht eindeutig; pending.dpapi erhalten')
        elif action == 'write_remote':
            if d and d == op['device'] and confirmed_write(d, r, op['uid'], op['remote'] is None):
                self.save_binding(key, d, r, href, op['id'])
            elif d == op['device'] and r == op['remote']:
                pass
            else:
                raise RuntimeError('Unterbrochener Thunderbird-Schreibvorgang nicht eindeutig')
        elif action in ('delete_device', 'delete_remote'):
            if d is None and r is None:
                self.save_binding(key, None, None, href, op['id'])
            elif d == op['device'] and r == op['remote']:
                pass
            else:
                raise RuntimeError('Unterbrochene Löschung nicht eindeutig')
        else:
            raise RuntimeError('Unbekanntes Operationsjournal')
        self.pending_path.unlink()
        self.log('Unterbrochener Vorgang anhand der aktuellen Daten sicher geprüft.')

    def run(self, export):
        device, remote = device_snapshot(export), self.dav.snapshot()
        self.recover(device, remote)
        operations, conflicts, skipped = build_plan(self.state['bindings'], device, remote, getattr(self.dav, 'new_href', None), self.dav.zone)
        if conflicts:
            raise RuntimeError('Konflikt – keine Daten geändert: ' + '; '.join(conflicts))
        # Validate every conversion before making the first change.
        for op in operations:
            if op['action'] == 'write_remote':
                d, r = op['device'], op['remote']
                op['uid'] = r['uid'] if r else f'ic35-{d["kind"]}-{d["rid"]}@local'
                op['content'] = model.render(d['kind'], d['fields'], op['uid'], r['content'] if r else None)
                if model.parse(d['kind'], op['content'], self.dav.zone)['semantic'] != d['semantic']:
                    raise ValueError('Darstellung in Thunderbird wäre verlustbehaftet; keine Daten geändert')
        for message in skipped:
            self.log('Übersprungen: ' + message)
        # Before every batch, persist the complete inputs for diagnosis/recovery.
        storage.write_json(self.root / 'backups' / (uuid.uuid4().hex + '.dpapi'),
                           {'export': export, 'remote': remote, 'state': self.state, 'operations': operations})
        stats = {'write_device': 0, 'write_remote': 0, 'delete_device': 0, 'delete_remote': 0, 'bind': 0}
        for op in operations:
            action, key, href = op['action'], op['key'], op['href']
            d, r = op['device'], op['remote']
            if action in ('bind', 'forget'):
                self.save_binding(key, d, r, href, str(uuid.uuid4()))
                stats['bind'] += 1
                continue
            self.dav.check(href, r)
            op.update(id=str(uuid.uuid4()), before_ids=list(device))
            if action in ('write_remote', 'delete_remote'):
                self.device.confirm(op)
            storage.write_json(self.pending_path, op)
            self.log(f'Übertrage {action}: {key or href} – warte auf Bestätigung …')
            if action == 'write_device':
                d = self.device.execute(op)
                key = f'{d["kind"]}:{d["rid"]}'
                device[key] = d
                # Refuse to commit the baseline if Thunderbird changed during device I/O.
                self.dav.check(href, r)
            elif action == 'delete_device':
                self.device.execute(op)
                self.dav.check(href, None)
                device.pop(key, None)
                d = None
            elif action == 'write_remote':
                self.dav.write(href, op['content'], r)
                r = self.dav.read(href) if hasattr(self.dav, 'read') else self.dav.snapshot().get(href)
                if not confirmed_write(d, r, op['uid'], op['remote'] is None):
                    raise RuntimeError('Thunderbird-Kontrolllesen fehlgeschlagen')
                if r['semantic'] != d['semantic']:
                    self.log('Kalender hat eine Standard-Erinnerung ergänzt; beide Ausgangswerte werden getrennt gespeichert.')
            elif action == 'delete_remote':
                self.dav.delete(href, r)
                self.dav.check(href, None)
                r = None
            self.save_binding(key, d, r, href, op['id'])
            self.pending_path.unlink()
            stats[action] += 1
            self.log(f'{action}: {key}')
        return {'stats': stats, 'skipped': skipped}
