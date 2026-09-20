"""Exercise the packaged app with isolated test storage and loopback only."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
exe = ROOT / 'dist/IC35Sync.exe'
with tempfile.TemporaryDirectory(prefix='ic35-package-') as td:
    root = Path(td)
    result = root / 'check.json'
    env = dict(os.environ, IC35_SYNC_DATA_DIR=str(root / 'appdata'))
    proc = subprocess.Popen([str(exe), '--package-check', str(result)], env=env)
    try:
        code = proc.wait(timeout=45)
        if code:
            error = Path(str(result) + '.error')
            raise RuntimeError(error.read_text() if error.exists() else f'Package exit: {code}')
        assert '"ok"' in result.read_text()
    finally:
        if proc.poll() is None:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    print('Packaged Tk, Google API definitions, audio resources and OAuth client: OK')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with (root / 'radicale.log').open('w') as log:
        proc = subprocess.Popen([str(exe), '--radicale', '--config', '',
            '--storage-filesystem-folder', str(root / 'storage'),
            '--storage-type', 'multifilesystem_nolock', '--auth-type', 'none',
            '--server-hosts', f'127.0.0.1:{port}'], env=env,
            stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        try:
            for _ in range(60):
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1) as response:
                        assert response.status == 200
                        break
                except OSError:
                    if proc.poll() is not None:
                        raise RuntimeError((root / 'radicale.log').read_text())
                    time.sleep(.5)
            else:
                raise RuntimeError('Packaged CardDAV server did not respond')
            print('Packaged CardDAV subprocess with isolated storage: HTTP 200')
        finally:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
            proc.wait(timeout=10)
