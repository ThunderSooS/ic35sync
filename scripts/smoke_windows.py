"""Isolated frozen-app checks, without IC35 or personal Thunderbird data."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bridge
from dav_sync import DAV
from dav_model import render

exe = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'dist/IC35Thunderbird.exe'
with tempfile.TemporaryDirectory(prefix='ic35-package-') as tmp:
    tmp = Path(tmp)
    result = tmp / 'check.json'
    proc = subprocess.run([str(exe), '--package-check', str(result)], timeout=60)
    if proc.returncode or not result.exists():
        error = Path(str(result) + '.error')
        raise RuntimeError(error.read_text() if error.exists() else 'Package check did not complete')
    checks = json.loads(result.read_text())
    bridge.ensure_radicale_storage(tmp / 'dav')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    with (tmp / 'server.log').open('w') as log:
        server = subprocess.Popen([str(exe), '--radicale', '--config', '', '--storage-filesystem-folder',
            str(tmp / 'dav'), '--storage-type', 'multifilesystem', '--auth-type', 'none',
            '--server-hosts', f'127.0.0.1:{port}'], stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            dav = DAV(f'http://127.0.0.1:{port}', 'Europe/Berlin')
            for _ in range(100):
                try:
                    assert dav.snapshot() == {}
                    break
                except OSError:
                    if server.poll() is not None:
                        raise RuntimeError((tmp / 'server.log').read_text())
                    time.sleep(.1)
            else:
                raise RuntimeError((tmp / 'server.log').read_text())
            fields = {'Betreff': 'Synthetic test', 'Notizen': '', 'Start': '', 'Ende': '',
                      'Erledigt': 0, 'Prioritaet': 1, 'category-id': 18, 'category': 'Unfiled'}
            href = '/ic35/calendar/test.ics'
            dav.write(href, render('tasks', fields, 'synthetic-only'), None)
            actual = dav.snapshot()[href]
            assert actual['fields']['Betreff'] == 'Synthetic test'
            dav.delete(href, actual)
            assert dav.snapshot() == {}
            checks['frozen_DAV_read_write_delete'] = 'ok'
        finally:
            subprocess.run(['taskkill', '/PID', str(server.pid), '/T', '/F'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            server.wait(timeout=10)
    (ROOT / 'smoke-results.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    print(json.dumps(checks))
