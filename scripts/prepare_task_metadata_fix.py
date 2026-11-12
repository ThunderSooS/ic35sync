"""Integrate the helper after verifying Git revision and newline-only checkout changes."""
import hashlib
import os
from pathlib import Path
import json
import subprocess

EXPECTED_BLOB = '937523d4e931cd92cf14352f1afd2d806909e45f'


def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def validated_source(tracked, working):
    if git_blob(tracked) != EXPECTED_BLOB:
        raise RuntimeError('Unexpected committed dav_sync.py revision; refusing integration')
    normalize = lambda raw: raw.replace(b'\r\n', b'\n')
    if normalize(tracked) != normalize(working):
        raise RuntimeError('Working dav_sync.py differs beyond line endings; refusing integration')
    source = normalize(tracked).decode('utf-8-sig')
    old = "r['semantic'] == binding['remote'] and r.get('content') == binding.get('remote_content', r.get('content'))"
    anchor = 'import private_storage as storage\n'
    if source.count(old) != 1 or source.count(anchor) != 1:
        raise RuntimeError('Unexpected deletion guard or import structure')
    source = source.replace(anchor, anchor + 'from task_delete_metadata import remote_unchanged_for_delete as _remote_unchanged_for_delete\n')
    source = source.replace(old, '_remote_unchanged_for_delete(r, binding)')
    compile(source, 'dav_sync.py', 'exec')
    return source


def main():
    root = Path(__file__).resolve().parents[1]
    path = root / 'dav_sync.py'
    tracked = subprocess.run(['git', 'show', 'HEAD:dav_sync.py'], cwd=root,
                             check=True, capture_output=True).stdout
    working = path.read_bytes()
    source = validated_source(tracked, working)
    path.write_bytes(source.encode('utf-8'))
    out = root / 'build-evidence'
    out.mkdir(exist_ok=True)
    (out / 'dav_sync.py').write_bytes(path.read_bytes())
    (out / 'task_delete_metadata.py').write_bytes((root / 'task_delete_metadata.py').read_bytes())
    (out / 'provenance.json').write_text(json.dumps({
        'commit': os.environ.get('GITHUB_SHA', 'local'),
        'original_dav_sync_git_blob': git_blob(tracked),
        'checkout_had_line_ending_changes': tracked != working,
        'built_dav_sync_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'integration': 'build checkout only',
        'scope': 'task deletion from device to Thunderbird; valid root DTSTAMP and LAST-MODIFIED values only',
        'real_device_validation': 'pending'
    }, indent=2), encoding='utf-8')
    (out / 'READ-ME-FIRST.txt').write_text(
        'EXPERIMENTAL TASK METADATA FIX - NOT A STABLE RELEASE\n'
        'This IC35Thunderbird.exe includes the DTSTAMP and LAST-MODIFIED deletion comparison fix.\n'
        'This is not the diagnostic EXE and not an installer. Internal version labels are unchanged.\n'
        'Back up IC35 and Thunderbird data before testing.\n'
        'Existing deletions may now propagate when every other compared property is unchanged.\n'
        'Do not reset or delete sync state. No real-device validation has been performed by this build.\n'
        'The original DTSTAMP-only patch is obsolete for this workflow and is not applied.\n', encoding='utf-8')
    print('Verified committed revision and checkout contents; task metadata fix integrated.')


if __name__ == '__main__':
    main()
