"""Read-only IC35 memo export into a user-selected folder.

Each IC35 memo becomes one plain-text file named after its subject plus the
IC35 record id, e.g. ``Einkauf [IC35-000012].txt``.  The record id keeps the
mapping stable when the subject changes on the device.  Files for memos that
no longer exist on the IC35 are left untouched (nothing is ever deleted).
"""
from pathlib import Path
import os
import re
import tempfile

import ic35_protocol as proto

MEMO_DB = 'Memo'
_TAG = re.compile(r' \[IC35-(\d{6})\]\.txt$', re.IGNORECASE)
_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
             *(f'LPT{i}' for i in range(1, 10))}
MAX_SUBJECT = 80


def safe_subject(subject) -> str:
    text = _INVALID.sub('_', str(subject or '')).strip().rstrip('. ')
    text = re.sub(r'\s+', ' ', text)[:MAX_SUBJECT].rstrip('. ')
    if not text or text.upper() in _RESERVED:
        text = f'Notiz {text}'.strip() if text else 'Notiz'
    return text


def file_name(record: dict) -> str:
    subject = record.get('fields', {}).get('Betreff', {}).get('value', '')
    return f'{safe_subject(subject)} [IC35-{int(record["record_id"]):06d}].txt'


def memo_text(record: dict) -> str:
    body = str(record.get('fields', {}).get('Notizen', {}).get('value', '') or '')
    body = body.replace('\r\n', '\n').replace('\r', '\n')
    return body.replace('\n', '\r\n')


def read_memos(ser, log=print) -> list[dict]:
    """Read all memo records without modifying the device."""
    fd = proto.open_database(ser, MEMO_DB)
    if fd is None:
        raise RuntimeError('Notizen-Datenbank des IC35 konnte nicht geöffnet werden.')
    records = []
    try:
        count = proto.read_database_count(ser, MEMO_DB, fd)
        if count is None:
            raise RuntimeError('Anzahl der IC35-Notizen konnte nicht gelesen werden.')
        log(f'IC35-Notizen: {count} Datensatz/Datensätze gefunden.')
        for index in range(count):
            raw = proto.read_record_raw_by_index(ser, MEMO_DB, fd, index)
            if raw is None:
                raise RuntimeError(f'Notiz {index + 1} konnte nicht gelesen werden.')
            record = proto.decode_record(MEMO_DB, raw, index)
            if record is None or record.get('file_id') != proto.FILE_IDS[MEMO_DB]:
                raise RuntimeError(f'Notiz {index + 1} konnte nicht dekodiert werden.')
            if not record.get('deleted'):
                records.append(record)
    finally:
        proto.close_database(ser, MEMO_DB, fd)
    return records


def _existing_by_id(folder: Path) -> dict[int, list[Path]]:
    found: dict[int, list[Path]] = {}
    for path in folder.glob('*.txt'):
        match = _TAG.search(path.name)
        if match:
            found.setdefault(int(match.group(1)), []).append(path)
    return found


def _atomic_write(path: Path, text: str):
    fd, tmp = tempfile.mkstemp(prefix='.ic35-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as stream:
            stream.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_memos(records: list[dict], folder, log=print) -> dict:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    existing = _existing_by_id(folder)
    stats = {'created': 0, 'updated': 0, 'unchanged': 0, 'renamed': 0}
    for record in records:
        rid = int(record['record_id'])
        target = folder / file_name(record)
        text = memo_text(record)
        old_paths = [p for p in existing.get(rid, []) if p.name.lower() != target.name.lower()]
        if target.exists():
            current = target.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
            if current == text.replace('\r\n', '\n'):
                stats['unchanged'] += 1
            else:
                _atomic_write(target, text)
                stats['updated'] += 1
                log(f'Notiz aktualisiert: {target.name}')
        else:
            _atomic_write(target, text)
            if old_paths:
                stats['renamed'] += 1
                log(f'Notiz umbenannt: {old_paths[0].name} → {target.name}')
            else:
                stats['created'] += 1
                log(f'Notiz angelegt: {target.name}')
        for old in old_paths:
            old.unlink(missing_ok=True)
    return stats
