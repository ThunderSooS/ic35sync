"""Two-way synchronisation of IC35 memos with plain text files in a folder.

Each IC35 memo corresponds to one ``.txt`` file named after its subject plus
the IC35 record id, e.g. ``Einkauf [IC35-000012].txt``.  A ``.txt`` file
without such a tag is a new note and is created on the IC35.

The last synchronised state of every memo is stored (DPAPI-protected by the
app), which allows a real three-way comparison:

* changed only on one side      -> change is copied to the other side,
* deleted on one side, unchanged on the other -> deleted on the other side,
* changed differently on both sides, or deleted on one and changed on the
  other -> conflict: nothing is written for this memo, a hint is logged.

Safety rules: nothing is truncated (too long texts or characters outside
Windows-1252 are skipped with a reason), every device write is read back, a
missing folder or a folder in which *all* known notes vanished stops the memo
sync, and an interrupted creation is recognised on the next run instead of
creating a duplicate.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import re
import tempfile

import ic35_protocol as proto

MEMO_DB = 'Memo'
FILE_ID = proto.FILE_IDS[MEMO_DB]
MAGIC = b'\x60\x16\x99'           # ic35link 1.18 syntrans.c, FILEMEMO
MAX_SUBJECT_BYTES = 60            # ic35link doc/ic35sync.txt, Memo field 0
MAX_BODY_BYTES = 255              # Memo field 1 (IC35 line breaks are CRLF)
DEFAULT_CATEGORY = (0x0F, 'Unfiled')
STATE_VERSION = 1

_TAG = re.compile(r'^(.*) \[IC35-(\d{6})\]$', re.IGNORECASE)
_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
             *(f'LPT{i}' for i in range(1, 10))}
MAX_NAME_CHARS = 80


# ---------------------------------------------------------------------------
# Names and texts
# ---------------------------------------------------------------------------

def safe_subject(subject) -> str:
    text = _INVALID.sub('_', str(subject or '')).strip().rstrip('. ')
    text = re.sub(r'\s+', ' ', text)[:MAX_NAME_CHARS].rstrip('. ')
    if not text or text.upper() in _RESERVED:
        text = f'Notiz {text}'.strip() if text else 'Notiz'
    return text


def tagged_name(subject, rid) -> str:
    return f'{safe_subject(subject)} [IC35-{int(rid):06d}].txt'


def norm(text) -> str:
    return str(text or '').replace('\r\n', '\n').replace('\r', '\n')


def to_crlf(text) -> str:
    return norm(text).replace('\n', '\r\n')


def check_device_text(subject, body):
    """Raise ValueError if the memo cannot be stored on the IC35 unchanged."""
    for label, value, limit in (('Betreff', subject, MAX_SUBJECT_BYTES),
                                ('Text', to_crlf(body), MAX_BODY_BYTES)):
        if '\x00' in value:
            raise ValueError(f'{label}: Nullzeichen sind nicht erlaubt')
        try:
            raw = value.encode('cp1252', errors='strict')
        except UnicodeEncodeError as exc:
            raise ValueError(f'{label}: Zeichen „{value[exc.start]}“ ist auf dem IC35 nicht darstellbar') from exc
        if len(raw) > limit:
            raise ValueError(f'{label}: {len(raw)} Byte, der IC35 erlaubt maximal {limit}. Keine Kürzung')


def encode_memo(subject, body, category_id, category) -> bytes:
    check_device_text(subject, body)
    parts = [subject.encode('cp1252'), to_crlf(body).encode('cp1252'),
             b'' if category_id is None else bytes([int(category_id) & 0xFF]),
             str(category or '').encode('cp1252', errors='strict')[:8]]
    return bytes(map(len, parts)) + b''.join(parts)


def _digest(subject, body) -> str:
    return hashlib.sha256((norm(subject) + '\x00' + norm(body)).encode('utf-8')).hexdigest()


# ---------------------------------------------------------------------------
# Device access (real IC35)
# ---------------------------------------------------------------------------

@dataclass
class Memo:
    rid: int
    subject: str
    body: str
    category_id: int | None = None
    category: str = ''


def memo_from_record(record) -> Memo:
    if not record or record.get('error') or record.get('file_id') != FILE_ID:
        raise ValueError('Ungültiger Notiz-Datensatz')
    fields = record.get('fields', {})
    if set(fields) != {name for name, _ in proto.FIELD_SPECS[MEMO_DB]}:
        raise ValueError('Unvollständiger Notiz-Datensatz')
    value = lambda name: fields[name]['value']
    return Memo(int(record['record_id']), str(value('Betreff') or ''), norm(value('Notizen')),
                value('category-id'), str(value('category') or ''))


class Device:
    """Memo operations on a connected, authenticated IC35."""

    def __init__(self, ser, log=print):
        self.ser, self.log = ser, log

    def _with_fd(self, action):
        fd = proto.open_database(self.ser, MEMO_DB)
        if fd is None:
            raise RuntimeError('Notizen-Datenbank des IC35 konnte nicht geöffnet werden.')
        try:
            return action(fd)
        finally:
            proto.close_database(self.ser, MEMO_DB, fd)

    def _read_all(self, fd):
        count = proto.read_database_count(self.ser, MEMO_DB, fd)
        if count is None:
            raise RuntimeError('Anzahl der IC35-Notizen konnte nicht gelesen werden.')
        memos = []
        for index in range(count):
            raw = proto.read_record_raw_by_index(self.ser, MEMO_DB, fd, index)
            record = proto.decode_record(MEMO_DB, raw, index) if raw else None
            if record is None:
                raise RuntimeError(f'Notiz {index + 1} konnte nicht gelesen werden.')
            if not record.get('deleted'):
                memos.append(memo_from_record(record))
        return memos

    def read_all(self):
        return self._with_fd(self._read_all)

    def write(self, subject, body, category_id, category, rid=None) -> Memo:
        data = encode_memo(subject, body, category_id, category)
        if rid is not None and not 0 < int(rid) <= 0xFFFFFF:
            raise ValueError('Ungültige Notiz-ID')

        def action(fd):
            uid = int(rid).to_bytes(3, 'little') + bytes([FILE_ID]) if rid else bytes(4)
            result = None
            for offset in range(0, len(data), 80):
                chunk = data[offset:offset + 80]
                last = offset + len(chunk) >= len(data)
                if offset == 0:
                    chunk = (b'\x01' + (b'\x09' if rid else b'\x08') + fd + uid + MAGIC
                             + b'\x00\x00' + len(data).to_bytes(4, 'little') + chunk)
                label = f"Notiz {'UPDATE' if rid else 'CREATE'} Block {offset // 80 + 1}"
                request = proto.make_fragment_command(0x82 if last else 0x02, 0x49 if last else 0x48, chunk)
                response = proto.l1_transaction(self.ser, request, label)
                if response is None:
                    raise RuntimeError(f'{label}: keine Antwort vom IC35.')
                result = proto._decode_write_response(response, last, label)
                if result is None:
                    raise RuntimeError(f'{label}: vom IC35 nicht bestätigt.')
            new_id, file_id = result
            if file_id != FILE_ID or not new_id or (rid and new_id != int(rid)):
                raise RuntimeError('Unerwartete Schreibantwort des IC35 für eine Notiz.')
            raw = proto.read_record_raw_by_id(self.ser, MEMO_DB, fd, new_id)
            memo = memo_from_record(proto.decode_record(MEMO_DB, raw, -1) if raw else None)
            if memo.subject != subject or memo.body != norm(body):
                raise RuntimeError('Rücklesen der Notiz stimmt nicht mit den geschriebenen Daten überein.')
            return memo
        return self._with_fd(action)

    def delete(self, rid):
        if not 0 < int(rid) <= 0xFFFFFF:
            raise ValueError('Ungültige Notiz-ID')

        def action(fd):
            l4 = b'\x01\x02' + fd + int(rid).to_bytes(3, 'little') + bytes([FILE_ID])
            if proto.command_transaction(self.ser, 0x83, l4, f'Delete Notiz {rid}') is None:
                raise RuntimeError('Löschen der Notiz wurde vom IC35 nicht bestätigt.')
            if any(m.rid == int(rid) for m in self._read_all(fd)):
                raise RuntimeError('Notiz ist nach dem Löschen noch auf dem IC35 vorhanden.')
        self._with_fd(action)


# ---------------------------------------------------------------------------
# Folder access
# ---------------------------------------------------------------------------

@dataclass
class NoteFile:
    path: Path
    stem: str          # subject part of the file name (without tag/extension)
    body: str
    rid: int | None


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252', errors='replace')
    return norm(text)


def scan_folder(folder: Path) -> list[NoteFile]:
    notes = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() != '.txt' or path.name.startswith(('.', '~')):
            continue
        match = _TAG.match(path.stem)
        stem, rid = (match.group(1), int(match.group(2))) if match else (path.stem, None)
        notes.append(NoteFile(path, stem.strip(), read_text(path), rid))
    return notes


def atomic_write(path: Path, text: str):
    fd, tmp = tempfile.mkstemp(prefix='.ic35-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as stream:
            stream.write(to_crlf(text))
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

class Stop(Exception):
    """Memo sync must not continue (folder/device state looks unsafe)."""


class MemoSync:
    def __init__(self, folder, device, load_state, save_state, log=print, backup=None):
        self.folder = Path(folder)
        self.device, self.log = device, log
        self.load_state, self.save_state, self.backup = load_state, save_state, backup
        self.stats = dict(to_device=0, to_folder=0, deleted_device=0, deleted_folder=0,
                          conflicts=0, skipped=0)

    # -- state ------------------------------------------------------------
    def _state(self):
        state = self.load_state() or {}
        if state.get('version') != STATE_VERSION or state.get('folder') != str(self.folder):
            if state.get('bindings'):
                self.log('Notizen: anderer Ordner als beim letzten Abgleich – Zuordnung wird neu aufgebaut.')
            state = {'version': STATE_VERSION, 'folder': str(self.folder), 'bindings': {}, 'pending': []}
        state.setdefault('bindings', {}); state.setdefault('pending', [])
        return state

    def _commit(self):
        self.save_state(self.state)

    def _bind(self, memo: Memo, path: Path):
        self.state['bindings'][str(memo.rid)] = {
            'subject': memo.subject, 'body': memo.body, 'file': path.name,
            'stem': _TAG.match(path.stem).group(1) if _TAG.match(path.stem) else path.stem,
            'category_id': memo.category_id, 'category': memo.category}

    # -- helpers ----------------------------------------------------------
    def _write_file(self, memo: Memo, old: NoteFile | None = None) -> Path:
        target = self.folder / tagged_name(memo.subject, memo.rid)
        same = old is not None and old.path.name.lower() == target.name.lower()
        if same:
            atomic_write(old.path, memo.body)
            if old.path.name != target.name:      # only letter case differs
                os.rename(old.path, target)
            return target
        if target.exists():
            other = _TAG.match(target.stem)
            if not other or int(other.group(2)) != memo.rid:
                raise RuntimeError(f'Zieldatei {target.name} existiert bereits')
        atomic_write(target, memo.body)
        if old is not None and old.path.exists():
            old.path.unlink()
        return target

    def _conflict(self, rid, text):
        self.stats['conflicts'] += 1
        self.log(f'KONFLIKT Notiz {rid:06d}: {text}')

    def _skip(self, what, exc):
        self.stats['skipped'] += 1
        self.log(f'Notiz übersprungen ({what}): {exc}')

    def _category(self, memos):
        for memo in memos:
            if memo.category.lower() == 'unfiled' and memo.category_id is not None:
                return memo.category_id, memo.category
        return DEFAULT_CATEGORY

    # -- main -------------------------------------------------------------
    def run(self):
        self.state = self._state()
        bindings = self.state['bindings']
        if not self.folder.exists():
            if bindings:
                raise Stop(f'Notizordner {self.folder} fehlt – Notizen werden nicht abgeglichen.')
            self.folder.mkdir(parents=True)
        device = {m.rid: m for m in self.device.read_all()}
        if self.backup:
            self.backup([m.__dict__ for m in device.values()])
        tagged, untagged = self._scan()
        if self.state['pending']:
            self._resume_pending(device, untagged)
            self._commit()
            tagged, untagged = self._scan()

        known = [int(rid) for rid in bindings]
        if len(known) >= 3 and not any(rid in tagged for rid in known) and not untagged:
            raise Stop('Keine der bekannten Notizdateien ist im Ordner vorhanden. '
                       'Ordner prüfen – aus Sicherheitsgründen wird auf dem IC35 nichts gelöscht.')
        if len(known) >= 3 and not device:
            raise Stop('Der IC35 meldet keine Notizen mehr, obwohl bereits Notizen abgeglichen wurden. '
                       'Aus Sicherheitsgründen werden keine Dateien gelöscht.')

        category = self._category(device.values())

        for rid in sorted(set(known) | set(device) | set(tagged)):
            try:
                self._reconcile(rid, bindings.get(str(rid)), device.get(rid), tagged.get(rid, False))
            except Stop:
                raise
            except Exception as exc:
                self._skip(f'IC35-ID {rid:06d}', exc)
            self._commit()

        for note in untagged:
            try:
                self._create_on_device(note, category)
            except Exception as exc:
                self._skip(note.path.name, exc)
            self._commit()
        self._commit()
        return self.stats

    def _scan(self):
        tagged, untagged = {}, []
        for note in scan_folder(self.folder):
            if note.rid is None:
                untagged.append(note)
            elif note.rid in tagged:
                tagged[note.rid] = None  # duplicate tag -> conflict below
            else:
                tagged[note.rid] = note
        return tagged, untagged

    def _resume_pending(self, device, untagged):
        """Bind memos created in an interrupted previous run instead of duplicating them."""
        bound = {int(rid) for rid in self.state['bindings']}
        for pending in list(self.state['pending']):
            note = next((n for n in untagged if n.path.name == pending['file']), None)
            match = [m for m in device.values() if m.rid not in bound
                     and _digest(m.subject, m.body) == pending['digest']]
            if note and len(match) == 1 and _digest(note.stem, note.body) == pending['digest']:
                memo = match[0]
                path = self._write_file(memo, note)
                self._bind(memo, path)
                bound.add(memo.rid)
                untagged.remove(note)
                self.log(f'Notiz aus unterbrochenem Abgleich zugeordnet: {path.name}')
            elif note and match:
                untagged.remove(note)
                self._conflict(match[0].rid, f'unterbrochene Neuanlage von „{note.path.name}“ nicht eindeutig; '
                               'Datei und IC35-Notiz bitte prüfen, dann die doppelte löschen.')
                continue
            self.state['pending'].remove(pending)

    def _reconcile(self, rid, base, memo, note):
        if note is None:
            return self._conflict(rid, 'mehrere Dateien tragen dieselbe IC35-ID; bitte eine davon entfernen.')
        note = note or None
        if base is None:
            if memo and note:
                if note.body == memo.body and note.stem in (safe_subject(memo.subject), memo.subject):
                    self._bind(memo, note.path)
                    return
                return self._conflict(rid, f'„{note.path.name}“ und IC35-Notiz unterscheiden sich beim ersten '
                                      'Abgleich; bitte beide auf denselben Stand bringen.')
            if memo:
                path = self._write_file(memo)
                self._bind(memo, path)
                self.stats['to_folder'] += 1
                self.log(f'Notiz vom IC35 übernommen: {path.name}')
                return
            if note:
                return self._conflict(rid, f'„{note.path.name}“ gehört zu keiner IC35-Notiz. Für eine neue Notiz '
                                      'den Zusatz „[IC35-…]“ aus dem Dateinamen entfernen.')
            return

        dev_changed = memo is not None and (memo.subject, memo.body) != (base['subject'], base['body'])
        file_changed = note is not None and (note.stem, note.body) != (base['stem'], base['body'])

        if memo is None and note is None:
            self.state['bindings'].pop(str(rid))
            return
        if memo is None:
            if file_changed:
                return self._conflict(rid, f'auf dem IC35 gelöscht, aber „{note.path.name}“ wurde geändert. '
                                      'Datei behalten = Zusatz „[IC35-…]“ entfernen; sonst Datei löschen.')
            note.path.unlink()
            self.state['bindings'].pop(str(rid))
            self.stats['deleted_folder'] += 1
            self.log(f'Notiz auf dem IC35 gelöscht, Datei entfernt: {note.path.name}')
            return
        if note is None:
            if dev_changed:
                return self._conflict(rid, f'Datei „{base["file"]}“ gelöscht, aber die Notiz wurde auf dem IC35 '
                                      'geändert. Auf dem IC35 löschen oder die Datei wiederherstellen.')
            self.device.delete(rid)
            self.state['bindings'].pop(str(rid))
            self.stats['deleted_device'] += 1
            self.log(f'Datei gelöscht, Notiz auf dem IC35 entfernt: „{memo.subject}“')
            return
        if not dev_changed and not file_changed:
            if note.path.name != tagged_name(memo.subject, rid):
                path = self._write_file(memo, note)
                self._bind(memo, path)
            return
        if dev_changed and not file_changed:
            path = self._write_file(memo, note)
            self._bind(memo, path)
            self.stats['to_folder'] += 1
            self.log(f'Änderung vom IC35 übernommen: {path.name}')
            return
        subject = note.stem if note.stem != base['stem'] else base['subject']
        if dev_changed and (memo.subject, memo.body) != (subject, note.body):
            return self._conflict(rid, f'auf dem IC35 und in „{note.path.name}“ unterschiedlich geändert; '
                                  'bitte beide auf denselben Stand bringen.')
        if (memo.subject, memo.body) != (subject, note.body):
            memo = self.device.write(subject, note.body, memo.category_id, memo.category, rid=rid)
            self.stats['to_device'] += 1
            self.log(f'Änderung auf den IC35 übertragen: „{memo.subject}“')
        path = self._write_file(memo, note) if note.path.name != tagged_name(memo.subject, rid) else note.path
        self._bind(memo, path)

    def _create_on_device(self, note: NoteFile, category):
        subject = note.stem
        check_device_text(subject, note.body)
        self.state['pending'].append({'file': note.path.name, 'digest': _digest(subject, note.body)})
        self._commit()
        memo = self.device.write(subject, note.body, *category)
        path = self._write_file(memo, note)
        self._bind(memo, path)
        self.state['pending'] = [p for p in self.state['pending'] if p['file'] != note.path.name]
        self.stats['to_device'] += 1
        self.log(f'Neue Notiz auf den IC35 übertragen: {path.name}')


def summary(stats) -> str:
    return (f'Notizen → IC35: {stats["to_device"]} · → Ordner: {stats["to_folder"]} · '
            f'gelöscht IC35/Ordner: {stats["deleted_device"]}/{stats["deleted_folder"]} · '
            f'Konflikte: {stats["conflicts"]} · übersprungen: {stats["skipped"]}')
