"""Read-only task conflict inspector; never starts the sync engine or opens IC35."""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
from urllib.parse import unquote

TARGETS = ('tasks:15', 'tasks:20')


def properties(raw):
    if not isinstance(raw, str):
        raise ValueError('Missing calendar content')
    logical = []
    for line in raw.splitlines():
        if line.startswith((' ', '\t')) and logical:
            logical[-1] += line[1:]
        else:
            logical.append(line)
    result = defaultdict(Counter)
    stack = []
    for line in logical:
        if line.startswith('BEGIN:'):
            stack.append(line[6:])
        label = line.split(':', 1)[0].split(';', 1)[0].upper()
        if not label or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' for c in label):
            label = 'UNRECOGNIZED-LINE'
        result['/'.join(stack) + '/' + label][line] += 1
        if line.startswith('END:') and stack:
            stack.pop()
    return result


def compare(binding, remote):
    if remote is None:
        return {'target_present': False}
    if remote.get('error'):
        return {'target_present': True, 'parse_error': True}
    old, new = binding.get('remote_content'), remote['content']
    baseline, current = binding.get('remote', {}), remote['semantic']
    result = {
        'target_present': True,
        'uid_matches': remote['uid'] == binding.get('uid'),
        'semantic_equal': baseline == current,
        'semantic_different_fields': sorted(k for k in set(baseline) | set(current)
                                             if (k in baseline) != (k in current)
                                             or baseline.get(k) != current.get(k)),
        'baseline_content_available': isinstance(old, str),
        'raw_content_equal': old == new,
    }
    if isinstance(old, str):
        before, after = properties(old), properties(new)
        result['different_properties'] = sorted(k for k in set(before) | set(after)
                                                 if before.get(k) != after.get(k))
        result['same_after_line_ending_normalization'] = old.splitlines() == new.splitlines()
        result['same_unordered_unfolded_properties'] = before == after
    return result


def inspect(root):
    import private_storage as storage
    import dav_model as model
    root = Path(root)
    for port in (5233, 5234):
        with socket.socket() as probe:
            probe.settimeout(.3)
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError('Bitte alle IC35-Sync-Fenster schliessen. Thunderbird geoeffnet lassen.')
    config = json.loads((root / 'settings.json').read_text(encoding='utf-8-sig'))
    selections = {k: v for k, v in config.get('calendars', {}).items()
                  if k in ('events', 'tasks') and v}
    pairing = None
    state_root = root
    if selections:
        pairing = storage.read_json(root / 'addon_pairing.dpapi')
        if not pairing.get('profile') or not pairing.get('token'):
            raise RuntimeError('Vorhandene Add-on-Kopplung fehlt; Diagnose aendert die Kopplung nicht.')
        payload = {'profile': pairing['profile'], 'calendars': selections}
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
        state_root = root / 'sync_states' / key
    state = storage.read_json(state_root / 'thunderbird_state.dpapi')
    zone = config.get('zone', 'Europe/Berlin')
    if state.get('version') != 1 or state.get('zone') != zone:
        raise RuntimeError('Vergleichsstand passt nicht zu Version oder Zeitzone; keine Diagnose.')
    bindings = state.get('bindings', {})
    if any(key not in bindings for key in TARGETS):
        raise RuntimeError('Die beiden Zielaufgaben fehlen im aktuell ausgewaehlten Vergleichsstand.')
    report = {'mode': 'read-only', 'report_contains_property_names_not_task_values': True,
              'device_access': False, 'calendar_writes_requested': False,
              'state_files_modified': False, 'tasks': {}}
    native = selections.get('tasks')
    broker = None
    try:
        if native:
            from thunderbird_rpc import Broker
            broker = Broker(root, pairing=dict(pairing))
            deadline = time.monotonic() + 45
            while not broker.last_seen and time.monotonic() < deadline:
                time.sleep(.25)
            if not broker.last_seen or broker.pairing['profile'] != pairing['profile']:
                raise RuntimeError('Gekoppeltes Thunderbird-Profil nicht verbunden; keine Aufgaben gelesen.')
        for key in TARGETS:
            binding = bindings[key]
            href = binding['href']
            remote = None
            if native:
                parts = href.split('/')
                if (len(parts) != 5 or parts[1:3] != ['thunderbird', 'tasks']
                        or unquote(parts[3]) != native or unquote(parts[4]) != binding['uid']):
                    raise RuntimeError('Zielzuordnung passt nicht zum ausgewaehlten Aufgabenkalender.')
                if broker.pairing['profile'] != pairing['profile']:
                    raise RuntimeError('Thunderbird-Profil hat gewechselt; Diagnose abgebrochen.')
                data = broker.call('get', {'calendarId': native, 'kind': 'tasks',
                                          'uid': binding['uid'], 'zone': zone}, timeout=30)
                if broker.pairing['profile'] != pairing['profile']:
                    raise RuntimeError('Thunderbird-Profil hat gewechselt; Diagnose abgebrochen.')
                if data is not None:
                    parsed = model.parse('tasks', data['content'], zone)
                    if parsed['uid'] != data['uid']:
                        raise RuntimeError('UID der Thunderbird-Antwort stimmt nicht ueberein.')
                    remote = dict(parsed, content=data['content'])
            else:
                from urllib.parse import urlparse
                parts = href.split('/')
                if (not href.startswith('/ic35/calendar/') or len(parts) != 4
                        or urlparse(href).netloc or not parts[3]
                        or unquote(parts[3]) in ('.', '..')
                        or any(c in unquote(parts[3]) for c in '/\\')):
                    raise RuntimeError('Unzulaessige lokale Aufgabenadresse; keine Datei gelesen.')
                folder = root / 'radicale' / 'collection-root' / 'ic35' / 'calendar'
                path = folder / unquote(parts[3])
                if path.exists():
                    if not path.is_file() or path.is_symlink() or path.resolve().parent != folder.resolve():
                        raise RuntimeError('Lokales Aufgabenziel ist keine regulaere Sammlungsdatei.')
                    content = path.read_text(encoding='utf-8-sig')
                    remote = dict(model.parse('tasks', content, zone), content=content)
            report['tasks'][key] = compare(binding, remote)
    finally:
        if broker:
            broker.close()
    return report


def self_test():
    old = 'BEGIN:VCALENDAR\r\nBEGIN:VTODO\r\nDTSTAMP:20261111T220000Z\r\nSUMMARY:Private title\r\nEND:VTODO\r\nEND:VCALENDAR\r\n'
    binding = {'uid': 'private-uid', 'remote': {'title': 'Private title'}, 'remote_content': old}
    remote = {'uid': 'private-uid', 'semantic': {'title': 'Private title'}, 'content': old}
    assert compare(binding, remote)['raw_content_equal']
    remote['content'] = old.replace('220000Z', '230000Z')
    result = compare(binding, remote)
    assert result['different_properties'] == ['VCALENDAR/VTODO/DTSTAMP']
    assert result['semantic_equal']
    remote['semantic'] = {'title': 'Changed private title'}
    assert compare(binding, remote)['semantic_different_fields'] == ['title']
    assert compare(binding, None) == {'target_present': False}
    assert 'private-uid' not in json.dumps(result) and 'Private title' not in json.dumps(result)
    assert properties('SUMMARY:folded\r\n text\r\n') == properties('SUMMARY:foldedtext\n')
    import ast
    tree = ast.parse(Path(__file__).read_text(encoding='utf-8'))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'call']
    assert len(calls) == 1 and calls[0].args[0].value == 'get'
    print('Synthetic comparisons, privacy checks and RPC allowlist: OK')


def main():
    import tkinter as tk
    from tkinter import filedialog, messagebox
    ui = tk.Tk()
    ui.withdraw()
    try:
        if not messagebox.askokcancel('IC35 Aufgaben-Diagnose',
                'Bitte IC35-Sync schliessen und Thunderbird geoeffnet lassen.\n'
                'Keinen Sync-Knopf druecken. Die Diagnose liest nur zwei Aufgaben\n'
                'und den gespeicherten Vergleichsstand. Keine Synchronisierung.\n\n'
                'Der Bericht enthaelt Eigenschaftsnamen, keine Aufgabentexte. Fortfahren?'):
            return
        root = Path(os.environ.get('IC35_TB_DATA_DIR') or Path(os.environ['APPDATA']) / 'IC35ThunderbirdAlpha')
        report = inspect(root)
        target = filedialog.asksaveasfilename(title='Diagnosebericht speichern',
                    initialfile='IC35-Aufgaben-Diagnose.json', defaultextension='.json',
                    filetypes=[('JSON', '*.json')])
        if target:
            with open(target, 'x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
            messagebox.showinfo('Diagnose abgeschlossen',
                'Bericht gespeichert. Bitte diesen JSON-Bericht zur Analyse teilen.\n'
                'Es wurden keine Sync-Daten geaendert.')
    except RuntimeError as exc:
        messagebox.showerror('Diagnose angehalten', str(exc))
    except Exception as exc:
        messagebox.showerror('Diagnose angehalten',
            'Diagnose fehlgeschlagen (' + type(exc).__name__ + ').\n'
            'Keine automatische Reparatur oder Synchronisierung ausgefuehrt.\n'
            'Bei FileExistsError bitte einen neuen Bericht-Dateinamen waehlen.')
    finally:
        ui.destroy()


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        main()
