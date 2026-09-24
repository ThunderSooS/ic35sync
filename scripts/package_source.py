"""Explicit source allowlist; validates ZIP contents and records SHA-256."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '3.4.0a11'
FILES = ['app.py', 'desktop_entry.py', 'dav_model.py', 'dav_sync.py', 'bridge.py', 'ic35_protocol.py',
         'todo_protocol.py', 'manager_protocol.py', 'private_storage.py', 'sync_sounds.py',
         'radicale_windows_launcher.py', 'requirements.txt', 'build-requirements.txt', 'LICENSE',
         'THIRD_PARTY_NOTICES.md', 'README.md', 'README.en.md', 'PRIVACY.md', 'CHANGELOG.md',
         'VALIDATION.md', '.gitignore', 'installer.iss', 'thunderbird_rpc.py', 'thunderbird_calendar.py', 'TWITCH_EINRICHTEN.md']
selected = [ROOT / name for name in FILES]
for folder in ('scripts', 'tests', 'sounds', 'build-licenses', 'addon'):
    selected += [p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
out = ROOT / 'release'
out.mkdir(exist_ok=True)
target = out / f'IC35-Sync-Beta-{VERSION}-Source.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in selected:
        archive.write(path, f'IC35-Thunderbird-{VERSION}/' + path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(selected)
for path in sorted(out.iterdir()):
    if VERSION in path.name and path.suffix in ('.zip', '.exe', '.xpi'):
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f'{checksum}  {path.name}  ({path.stat().st_size:,} bytes)')
