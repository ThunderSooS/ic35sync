"""Use existing Thunderbird calendars through the paired add-on, not their account credentials."""
import hashlib
import json
from urllib.parse import quote, unquote
import dav_model as model


class Calendars:
    def __init__(self, local_dav, broker, selections):
        self.local = local_dav
        self.zone = local_dav.zone
        self.broker = broker
        self.selections = {kind: ident for kind, ident in selections.items() if ident and kind in ('events', 'tasks')}

    def state_key(self):
        payload = {'profile': self.broker.pairing['profile'], 'calendars': self.selections}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]

    def new_href(self, kind, rid):
        if kind in self.selections:
            return self.href(kind, f'ic35-{kind}-{rid}@local')
        collection, suffix = ('addressbook', 'vcf') if kind == 'contacts' else ('calendar', 'ics')
        return f'/ic35/{collection}/ic35-{kind}-{rid}.{suffix}'

    def href(self, kind, uid):
        return '/thunderbird/' + kind + '/' + quote(self.selections[kind], safe='') + '/' + quote(uid, safe='')

    def params(self, href):
        parts = href.split('/')
        if len(parts) != 5 or parts[1] != 'thunderbird' or self.selections.get(parts[2]) != unquote(parts[3]):
            raise ValueError('Kalenderzuordnung passt nicht zum gewählten Ziel')
        return {'calendarId': unquote(parts[3]), 'kind': parts[2], 'uid': unquote(parts[4]), 'zone': self.zone}

    def item(self, kind, data):
        result = {'kind': kind, 'content': data['content'], 'etag': data['etag']}
        if not data['uid'] or not data['etag']:
            raise ValueError('Unvollständiger Thunderbird-Datensatz')
        try:
            result.update(model.parse(kind, data['content'], self.zone))
            if result['uid'] != data['uid']:
                raise ValueError('Thunderbird-UID stimmt nicht überein')
        except Exception as exc:
            result['error'] = str(exc)
        return result

    def snapshot(self):
        result = {href: r for href, r in self.local.snapshot().items() if r['kind'] not in self.selections}
        for kind, calendar_id in self.selections.items():
            response = self.broker.call('snapshot', {'calendarId': calendar_id, 'kind': kind})
            if response.get('complete') is not True:
                raise RuntimeError('Thunderbird-Kalender wurde nicht vollständig gelesen; kein Abgleich')
            for data in response['items']:
                href = self.href(kind, data['uid'])
                if href in result:
                    raise ValueError('Doppelte Thunderbird-UID')
                result[href] = self.item(kind, data)
        return result

    def check(self, href, expected):
        if href.startswith('/ic35/'):
            return self.local.check(href, expected)
        data = self.broker.call('get', self.params(href))
        if (expected is None and data is not None) or (expected is not None and (data is None or data['etag'] != expected['etag'])):
            raise RuntimeError('Kalendereintrag in Thunderbird wurde zwischenzeitlich verändert; Abgleich angehalten')

    def read(self, href):
        if href.startswith('/ic35/'):
            return self.local.snapshot().get(href)
        args = self.params(href)
        data = self.broker.call('get', args)
        return self.item(args['kind'], data) if data else None

    def write(self, href, content, before):
        if href.startswith('/ic35/'):
            return self.local.write(href, content, before)
        args = self.params(href)
        args.update(content=content, expected=before['etag'] if before else None)
        self.broker.call('write', args)

    def delete(self, href, before):
        if href.startswith('/ic35/'):
            return self.local.delete(href, before)
        self.broker.call('delete', dict(self.params(href), expected=before['etag']))
